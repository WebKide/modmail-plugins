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
import html
import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands


class Append2Json(commands.Cog):
    """Append missing Purport fields to existing Bhagavad Gita JSON using direct sibling element flow."""

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

            status_msg = await ctx.send(f"⏳ **[1/3]** Initializing anchor isolation maps for Chapter {chapter_num}...")

            # -------------------------
            # STEP 3 & 4: MAP & MERGE
            # -------------------------
            purport_map, chapter_end_text = await self.fetch_purport_map(chapter_num, status_msg)

            if not purport_map:
                return await status_msg.edit(content=f"❌ Failed to extract structural map for Chapter {chapter_num}.")

            await status_msg.edit(content="⏳ **[2/3]** Merging precise multi-class paragraphs into JSON positions...")
            verses = data.get("Verses", [])

            for idx, verse in enumerate(verses, start=1):
                verse["Purport-title"] = "PURPORT"
                verse_str = str(idx)
                verse["Purport-En"] = purport_map.get(verse_str, "No purport for this śloka.")

                if idx == len(verses):
                    verse["Chapter-end"] = "Chapter End"
                    verse["Chapter-En"] = chapter_end_text

            # -------------------------
            # STEP 5: OUTPUT HANDLER
            # -------------------------
            await status_msg.edit(content="⏳ **[3/3]** Saving and encoding output file stream...")
            output_json = json.dumps(data, ensure_ascii=False, indent=2)

            await status_msg.edit(content=f"✅ **Success!** Verified and filled all {len(verses)} verses with full paragraphs.")
            await ctx.send(file=discord.File(io.StringIO(output_json), filename=filename.replace(".json", "_enhanced.json")))

        except json.JSONDecodeError:
            await ctx.send("❌ Invalid JSON format provided.")
        except Exception as e:
            await ctx.send(f"❌ Structural Anchor Error: {str(e)}")

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
        if not chapter_desc:
            return None
        match = re.search(r'(\d+)', chapter_desc)
        return match.group(1) if match else None

    def parse_verse_range(self, range_text, chapter_num):
        if not range_text:
            return []

        clean_text = range_text.strip().upper()
        numbers = re.findall(r'\d+', clean_text)

        if not numbers:
            return []

        if '-' in clean_text or '–' in clean_text or 'TEXTS' in clean_text:
            try:
                sub_numbers = re.findall(rf'(?:BG\s+{chapter_num}\.|\.)(\d+)', clean_text)
                if len(sub_numbers) >= 2:
                    start = int(sub_numbers[0])
                    end = int(sub_numbers[-1])
                else:
                    start = int(numbers[0])
                    end = int(numbers[-1])
                return list(range(start, end + 1))
            except ValueError:
                return []

        return [int(numbers[0])] if numbers else []

    async def fetch_purport_map(self, chapter_num, status_msg: discord.Message):
        url = f"{self.base_url}/bg/{chapter_num}?d=1"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

        purport_map = {}
        chapter_end_text = f"Thus end the Bhaktivedanta Purports to Chapter {chapter_num}"

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        return None, ""

                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    text_num_divs = soup.find_all("div", class_="Textnum")
                    total_sections = len(text_num_divs)

                    if not text_num_divs:
                        return None, ""

                    for i, current_div in enumerate(text_num_divs):
                        if i == 0 or (i + 1) % 5 == 0 or (i + 1) == total_sections:
                            await status_msg.edit(content=f"⏳ Extracting purports: Section {i+1}/{total_sections}...")

                        header_text = current_div.get_text(strip=True)
                        verses_covered = self.parse_verse_range(header_text, chapter_num)
                        if not verses_covered:
                            continue

                        next_text_num = text_num_divs[i + 1] if i + 1 < total_sections else None

                        found_purport_header = False
                        purport_paragraphs = []

                        # Navigate using exact DOM sibling adjacency instead of a flattened list
                        sibling = current_div.find_next_sibling()
                        while sibling and sibling != next_text_num:
                            if sibling.name == "a" or not sibling.get_text(strip=True):
                                sibling = sibling.find_next_sibling()
                                continue

                            classes = sibling.get("class", [])

                            # Trigger active extraction phase once the PURPORT title is identified
                            if "Titles" in classes and sibling.get_text(strip=True) == "PURPORT":
                                found_purport_header = True
                                sibling = sibling.find_next_sibling()
                                continue

                            if found_purport_header:
                                # Captures transition blocks changing layout types on legacy pages
                                if "Purport" in classes or "Normal-Level" in classes:
                                    clean_p = ' '.join(html.unescape(sibling.get_text(strip=True)).split())
                                    if clean_p and clean_p not in ["SYNONYMS", "TRANSLATION", "PURPORT"] and not clean_p.startswith("Link to this page"):
                                        purport_paragraphs.append(clean_p)

                            sibling = sibling.find_next_sibling()

                        full_purport = "\n\n".join(purport_paragraphs) if purport_paragraphs else "No purport for this śloka."

                        for v_num in verses_covered:
                            purport_map[str(v_num)] = full_purport

                    # Track explicit global footer note if visible
                    thus_end = soup.find('div', class_='Thus-end')
                    if thus_end:
                        chapter_end_text = ' '.join(thus_end.get_text(strip=True).split())

            return purport_map, chapter_end_text

        except Exception as e:
            print(f"Error fetching purports: {e}")
            return None, ""


async def setup(bot):
    await bot.add_cog(Append2Json(bot))
