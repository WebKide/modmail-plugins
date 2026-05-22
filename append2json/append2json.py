# append2json.py

"""
MIT License
Copyright (c) 2020-2026 WebKide [d.id @323578534763298816]
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
    """Append missing Purport fields to existing Bhagavad Gita JSON with real-time status updates."""

    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://prabhupadabooks.com"

    @commands.command(name='append2json')
    async def append_json(self, ctx, url: str = None):
        """
        Usage:
        !append2json <raw_json_url>
        OR attach a JSON file
        """
        try:
            # -------------------------
            # STEP 1: LOAD JSON
            # -------------------------
            if url:
                data = await self.fetch_json_from_url(url)
                if not data:
                    return await ctx.send("❌ Failed to fetch or parse JSON from URL.")
                filename = "downloaded.json"
            elif ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                if not attachment.filename.endswith('.json'):
                    return await ctx.send("❌ Please attach a valid .json file.")
                
                json_content = (await attachment.read()).decode('utf-8')
                data = json.loads(json_content)
                filename = attachment.filename
            else:
                return await ctx.send("❓ Provide a JSON URL or attach a file.")

            # -------------------------
            # STEP 2: EXTRACT CHAPTER
            # -------------------------
            chapter_num = self.extract_chapter_number(data.get("Chapter-Desc", ""))
            if not chapter_num:
                return await ctx.send("❌ Could not extract chapter number from 'Chapter-Desc'.")

            # Create an initial message that we will edit in real-time
            status_msg = await ctx.send(f"⏳ **[1/3]** Initializing extraction for Chapter {chapter_num}...")

            # -------------------------
            # STEP 3: FETCH PURPORTS (WITH REAL-TIME STATUS)
            # -------------------------
            purport_data = await self.fetch_purport_data_with_status(chapter_num, status_msg)
            if not purport_data or not purport_data["purports"]:
                return await status_msg.edit(content=f"❌ Failed to extract purport data for Chapter {chapter_num}.")

            # -------------------------
            # STEP 4: MERGE DATA
            # -------------------------
            await status_msg.edit(content="⏳ **[2/3]** Merging site data into original JSON...")
            verses = data.get("Verses", [])

            for idx, verse in enumerate(verses):
                verse["Purport-title"] = "PURPORT"
                if idx < len(purport_data["purports"]):
                    text = purport_data["purports"][idx]
                    verse["Purport-En"] = text or "No purport for this śloka."
                else:
                    verse["Purport-En"] = "No purport for this śloka."

                if idx == len(verses) - 1:
                    verse["Chapter-end"] = "Chapter End"
                    verse["Chapter-En"] = purport_data.get("chapter_end", "")

            # -------------------------
            # STEP 5: OUTPUT
            # -------------------------
            await status_msg.edit(content="⏳ **[3/3]** Compiling enhanced JSON output file...")
            output_json = json.dumps(data, ensure_ascii=False, indent=2)

            await status_msg.edit(content=f"✅ **Success!** Processed Chapter {chapter_num} ({len(verses)} verses).")
            
            await ctx.send(
                file=discord.File(
                    io.StringIO(output_json),
                    filename=filename.replace(".json", "_enhanced.json")
                )
            )

        except json.JSONDecodeError:
            await ctx.send("❌ Invalid JSON format provided.")
        except Exception as e:
            await ctx.send(f"❌ Error encountered: {str(e)}")

    async def fetch_json_from_url(self, url):
        if not re.match(r'^https?://', url):
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=20) as resp:
                    if resp.status != 200:
                        return None
                    return json.loads(await resp.text())
        except Exception:
            return None

    def extract_chapter_number(self, chapter_desc):
        match = re.match(r'^(\d+)\.', chapter_desc.strip())
        return match.group(1) if match else None

    async def fetch_purport_data_with_status(self, chapter_num, status_msg: discord.Message):
        """Scrapes web data and updates the Discord user interface in real-time."""
        url = f"{self.base_url}/bg/{chapter_num}?d=1"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                textnum_elements = soup.find_all('div', class_='Textnum')
                total_verses = len(textnum_elements)
                if total_verses == 0:
                    return None

                purports = []

                for i, textnum in enumerate(textnum_elements, start=1):
                    # Periodically update Discord status to keep user informed and avoid rate limits
                    if i == 1 or i % 5 == 0 or i == total_verses:
                        await status_msg.edit(
                            content=f"⏳ **[1/3]** Scraping Chapter {chapter_num}: Processing verse **{i}/{total_verses}**..."
                        )

                    purport_text = []
                    current = textnum.find_next_sibling()
                    found_purport = False

                    while current:
                        if current.get('class') and 'Textnum' in current.get('class'):
                            break

                        if current.get('class') and 'Titles' in current.get('class'):
                            if 'PURPORT' in current.get_text(strip=True).upper():
                                found_purport = True
                                current = current.find_next_sibling()
                                continue

                        if found_purport and current.get('class'):
                            classes = current.get('class')
                            if 'Purport' in classes or 'Normal-Level' in classes:
                                text = self.extract_clean_text(current)
                                if text:
                                    purport_text.append(text)

                        current = current.find_next_sibling()

                    purports.append('\n\n'.join(purport_text))

                chapter_end = self.extract_chapter_end(soup, chapter_num)

                return {
                    "purports": purports,
                    "chapter_end": chapter_end
                }

    def extract_clean_text(self, element):
        return ' '.join(element.get_text(strip=True).split())

    def extract_chapter_end(self, soup, chapter_num):
        thus_end = soup.find('div', class_='Thus-end')
        if thus_end:
            return self.extract_clean_text(thus_end)
        return f"Thus end the Bhaktivedanta Purports to Chapter {chapter_num}"


async def setup(bot):
    await bot.add_cog(Append2Json(bot))
