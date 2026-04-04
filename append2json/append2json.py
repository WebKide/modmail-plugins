# append2json.py

"""
MIT License
Copyright (c) 2020-2025 WebKide [d.id @323578534763298816]
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import discord
import json
import re
import io
import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands


class Append2Json(commands.Cog):
    """Append missing Purport fields to existing Bhagavad Gita JSON by fetching from prabhupadabooks.com"""

    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://prabhupadabooks.com"

    @commands.command(name='append2json')
    async def append_json(self, ctx):
        """Upload a JSON file (from html2json) to add missing Purport fields and Chapter End footer"""
        if not ctx.message.attachments:
            return await ctx.send("Please attach a JSON file")

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith('.json'):
            return await ctx.send("Please attach a JSON file")

        try:
            # Read JSON file
            json_content = (await attachment.read()).decode('utf-8')
            data = json.loads(json_content)

            # Extract chapter number from Chapter-Desc
            chapter_num = self.extract_chapter_number(data.get("Chapter-Desc", ""))
            if not chapter_num:
                return await ctx.send("Could not extract chapter number from Chapter-Desc field")

            # Show status
            status_msg = await ctx.send(f"Fetching Purport data for Chapter {chapter_num}...")

            # Fetch and parse webpage
            purport_data = await self.fetch_purport_data(chapter_num)
            if not purport_data:
                await status_msg.edit(content=f"Failed to fetch data for Chapter {chapter_num}. Website may be unreachable.")
                return

            # Enhance verses with Purport
            verses = data.get("Verses", [])
            if len(verses) != len(purport_data["purports"]):
                await status_msg.edit(content=f"Warning: Verse count mismatch (JSON: {len(verses)}, HTML: {len(purport_data['purports'])}). Attempting to match by order anyway.")

            # Add Purport to each verse
            for idx, verse in enumerate(verses):
                # Add Purport fields
                verse["Purport-title"] = "PURPORT"

                if idx < len(purport_data["purports"]):
                    purport_text = purport_data["purports"][idx]
                    verse["Purport-En"] = purport_text if purport_text.strip() else "No purport for this śloka."
                else:
                    verse["Purport-En"] = "No purport for this śloka."

                # Add Chapter End fields to the LAST verse only
                if idx == len(verses) - 1:
                    verse["Chapter-end"] = "Chapter End"
                    verse["Chapter-En"] = purport_data.get("chapter_end", "")

            # Prepare output
            output_json = json.dumps(data, ensure_ascii=False, indent=2)
            output_filename = attachment.filename.replace('.json', '_enhanced.json')

            await status_msg.edit(content="✅ Purport data added successfully!")
            await ctx.send(file=discord.File(
                io.StringIO(output_json),
                filename=output_filename
            ))

        except json.JSONDecodeError:
            await ctx.send("Invalid JSON file. Please upload a valid JSON file from html2json.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    def extract_chapter_number(self, chapter_desc):
        """Extract chapter number from Chapter-Desc like '1. Observing the Armies...'"""
        match = re.match(r'^(\d+)\.', chapter_desc.strip())
        return match.group(1) if match else None

    async def fetch_purport_data(self, chapter_num):
        """Fetch and parse HTML to extract purports and chapter end footer"""
        url = f"{self.base_url}/bg/{chapter_num}?d=1"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Find all verse blocks
                    textnum_elements = soup.find_all('div', class_='Textnum')
                    if not textnum_elements:
                        return None

                    purports = []

                    for i, textnum in enumerate(textnum_elements):
                        purport_text = []
                        current = textnum.find_next_sibling()

                        # Flag to track if we've started collecting Purport for this verse
                        found_purport_title = False
                        found_purport_content = False

                        while current and current.name != 'div':
                            current = current.find_next_sibling()

                        while current:
                            # Stop if we hit the next Textnum (next verse)
                            if current.get('class') and 'Textnum' in current.get('class'):
                                break

                            # Check for Purport title
                            if current.get('class') and 'Titles' in current.get('class'):
                                if current.get_text(strip=True) == 'PURPORT':
                                    found_purport_title = True
                                    current = current.find_next_sibling()
                                    continue

                            # If we've found Purport title, collect Purport and Normal-Level divs
                            if found_purport_title:
                                if current.get('class'):
                                    classes = current.get('class')
                                    if 'Purport' in classes or 'Normal-Level' in classes:
                                        # Extract text, preserving line breaks from block elements
                                        text = self.extract_clean_text(current)
                                        if text:
                                            purport_text.append(text)
                                        found_purport_content = True

                            current = current.find_next_sibling()

                        # Join all purport paragraphs with double newline
                        final_purport = '\n\n'.join(purport_text) if purport_text else ""
                        purports.append(final_purport)

                    # Extract Chapter End footer
                    chapter_end = self.extract_chapter_end(soup, chapter_num)

                    return {
                        "purports": purports,
                        "chapter_end": chapter_end
                    }

            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return None

    def extract_clean_text(self, element):
        """Extract text from element, preserving link text but stripping HTML tags"""
        # Get text while keeping link content
        return ' '.join(element.get_text(strip=True).split())

    def extract_chapter_end(self, soup, chapter_num):
        """Extract the 'Thus end the Bhaktivedanta Purports...' footer"""
        # Look for div with class 'Thus-end'
        thus_end = soup.find('div', class_='Thus-end')
        if thus_end:
            text = self.extract_clean_text(thus_end)
        else:
            text = f"Thus end the Bhaktivedanta Purports to the {self.get_chapter_name(chapter_num)}"

        # Also get the link paragraph
        link_para = soup.find('p', align='center')
        link_text = ""
        if link_para and link_para.find('a'):
            link_text = link_para.find('a').get_text(strip=True)

        return f"{text}\n\nLink: {link_text}" if link_text else text

    def get_chapter_name(self, chapter_num):
        """Return chapter name based on chapter number"""
        # This can be expanded, but for now return generic
        chapter_names = {
            "1": "First Chapter of the Śrīmad-Bhagavad-gītā in the matter of Observing the Armies on the Battlefield of Kurukṣetra",
            # Add more as needed, or just use generic
        }
        return chapter_names.get(chapter_num, f"Chapter {chapter_num} of the Śrīmad-Bhagavad-gītā")


async def setup(bot):
    await bot.add_cog(Append2Json(bot))
