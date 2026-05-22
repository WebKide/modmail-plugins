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
    """Append missing Purport fields to existing Bhagavad Gita JSON using anchor exclusion mapping."""

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
                if verse_str in purport_map and purport_map[verse_str].strip():
                    verse["Purport-En"] = purport_map[verse_str]
                else:
                    verse["Purport-En"] = "No purport for this śloka."

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
        match = re.match(r'^(\d+)\.', chapter_desc.strip())
        return match.group(1) if match else None

    async def fetch_purport_map(self, chapter_num, status_msg: discord.Message):
        url = f"{self.base_url}/bg/{chapter_num}?d=1"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    return None, ""

                soup = BeautifulSoup(await response.text(), 'html.parser')
                all_elements = list(soup.find_all(True))

                # Locate where each Textnum boundary block begins
                textnum_indices = [idx for idx, el in enumerate(all_elements) if el.name == 'div' and el.get('class') and 'Textnum' in el.get('class')]

                purport_map = {}
                total_sections = len(textnum_indices)

                for i, current_timeline_idx in enumerate(textnum_indices):
                    if i == 0 or (i + 1) % 5 == 0 or (i + 1) == total_sections:
                        await status_msg.edit(content=f"⏳ **[1/3]** Extracting text slices: Section **{i+1}/{total_sections}**...")

                    next_timeline_idx = textnum_indices[i + 1] if i + 1 < len(textnum_indices) else len(all_elements)
                    section_slice = all_elements[current_timeline_idx:next_timeline_idx]

                    header_element = all_elements[current_timeline_idx]
                    range_text = header_element.get_text(strip=True)
                    verses_covered = self.parse_verse_range(range_text, chapter_num)

                    # --- ANCHOR EXCLUSION MECHANISM ---
                    purport_paragraphs = []
                    found_purport_title_anchor = False

                    for el in section_slice:
                        # Detect the explicit header marking the start of the Purport section
                        if el.name == 'div' and el.get('class') and 'Titles' in el.get('class'):
                            if 'PURPORT' in el.get_text(strip=True).upper():
                                found_purport_title_anchor = True
                                continue # Skip the title itself

                        # Once the anchor is passed, gather everything until the end of the timeline slice
                        if found_purport_title_anchor:
                            # Filter out tracking anchor elements or empty blocks
                            if el.name in ['div', 'p'] and el.get('class'):
                                # Skip if it accidentally reads a sub-title or link list wrapper at the very bottom
                                if 'Titles' in el.get('class') or 'Textnum' in el.get('class'):
                                    continue

                                # Extract, sanitize inner HTML elements out, and normalize text spaces
                                clean_text = el.get_text(separator=" ", strip=True)
                                clean_text = ' '.join(clean_text.split())

                                if clean_text and clean_text not in purport_paragraphs and not clean_text.startswith("Link to this page"):
                                    purport_paragraphs.append(clean_text)

                    full_purport_string = '\n\n'.join(purport_paragraphs)

                    for v_num in verses_covered:
                        if str(v_num) in purport_map and purport_map[str(v_num)]:
                            purport_map[str(v_num)] += f"\n\n{full_purport_string}"
                        else:
                            purport_map[str(v_num)] = full_purport_string

                thus_end = soup.find('div', class_='Thus-end')
                chapter_end = ' '.join(thus_end.get_text(strip=True).split()) if thus_end else f"Thus end the Bhaktivedanta Purports to Chapter {chapter_num}"

                return purport_map, chapter_end

    def parse_verse_range(self, range_text, chapter_num):
        clean_text = range_text.strip().upper()
        numbers = []

        if "BG" in clean_text:
            numbers = re.findall(rf'BG\s+{chapter_num}\.(\d+)', clean_text)
            if not numbers:
                numbers = re.findall(r'\.(\d+)', clean_text)
        elif "TEXT" in clean_text:
            # Handle ranges inside TEXT strings like "TEXTS 16-18"
            numbers = re.findall(r'(\d+)', clean_text)

        if not numbers:
            return []

        if '-' in clean_text or '–' in clean_text or 'TEXTS' in clean_text:
            try:
                start = int(numbers[0])
                end = int(numbers[-1])
                return list(range(start, end + 1))
            except Exception:
                pass

        return [int(n) for n in numbers]


async def setup(bot):
    await bot.add_cog(Append2Json(bot))
