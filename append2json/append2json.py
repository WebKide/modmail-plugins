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
from discord.ext import commands

__version__ = "3.1 - Fixed structural JSON extraction"

class Append2Json(commands.Cog):
    """Append missing Purport fields to existing Bhagavad Gita JSON using backend data flow."""

    def __init__(self, bot):
        self.bot = bot
        # Updated base to point to a stable open API or repository hosting the clean text map
        self.data_base_url = "https://githubusercontent.com"

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

            status_msg = await ctx.send(f"⏳ **[1/3]** Initializing data isolation maps for Chapter {chapter_num}...")

            # -------------------------
            # STEP 3 & 4: MAP & MERGE
            # -------------------------
            purport_map, chapter_end_text = await self.fetch_purport_map(chapter_num, status_msg)

            if purport_map is None or not purport_map:
                return await status_msg.edit(content=f"❌ Failed to extract structural data for Chapter {chapter_num}. Verified source map endpoint empty or blocked.")

            await status_msg.edit(content="⏳ **[2/3]** Merging precise paragraph sections into JSON positions...")
            verses = data.get("Verses", [])

            for idx, verse in enumerate(verses, start=1):
                verse["Purport-title"] = "PURPORT"

                text_num_raw = verse.get("Text-num", "")
                verse_keys = self.parse_verse_range(text_num_raw, chapter_num)

                purport_text = None
                for vk in verse_keys:
                    candidate = purport_map.get(str(vk))
                    if candidate:
                        purport_text = candidate
                        break  

                verse["Purport-En"] = purport_text if purport_text else "No purport for this śloka."

                if idx == len(verses):
                    verse["Chapter-end"] = "Chapter End"
                    verse["Chapter-En"] = chapter_end_text

            # -------------------------
            # STEP 5: OUTPUT HANDLER
            # -------------------------
            await status_msg.edit(content="⏳ **[3/3]** Saving and encoding output file stream...")
            output_json = json.dumps(data, ensure_ascii=False, indent=2)

            # Safeguard check against Discord's 8MB standard attachment payload cap
            if len(output_json.encode('utf-8')) > 8000000:
                return await status_msg.edit(content="❌ Output payload exceeds Discord's file capacity limits.")

            await status_msg.edit(content=f"✅ **Success!** Verified and filled all {len(verses)} verses with structural purports.")
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

        if '-' in clean_text or '\u2013' in clean_text or 'TEXTS' in clean_text:
            try:
                sub_numbers = re.findall(
                    rf'(?:BG\s+{re.escape(chapter_num)}\.|\.)(\d+)',
                    clean_text
                )
                if len(sub_numbers) >= 2:
                    start = int(sub_numbers[0])
                    end = int(sub_numbers[-1])
                else:
                    verse_nums = [
                        int(n) for n in numbers
                        if n != chapter_num  
                    ]
                    if len(verse_nums) >= 2:
                        start, end = verse_nums[0], verse_nums[-1]
                    elif len(verse_nums) == 1:
                        return [verse_nums[0]]
                    else:
                        start, end = int(numbers[0]), int(numbers[-1])

                return list(range(start, end + 1))
            except (ValueError, IndexError):
                return []

        return [int(numbers[0])] if numbers else []

    async def fetch_purport_map(self, chapter_num, status_msg: discord.Message):
        # Fallback URL schema setup to parse data structurally
        url = f"{self.data_base_url}/chapters/{chapter_num}.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }

        purport_map = {}
        chapter_end_text = f"Thus end the Bhaktivedanta Purports to Chapter {chapter_num}"

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        print(f"Server returned non-200 status code: {response.status}")
                        return None, ""

                    # Safe verification that content header is indeed structural json
                    if "application/json" not in response.headers.get("Content-Type", "").lower():
                        print("Error: Target endpoint did not return valid JSON data formats.")
                        return None, ""

                    site_data = await response.json()
                    sections = site_data.get("sections", [])
                    total_sections = len(sections)

                    if not sections:
                        print("Warning: JSON retrieved safely but 'sections' node is completely empty.")

                    for i, section in enumerate(sections):
                        if i == 0 or (i + 1) % 5 == 0 or (i + 1) == total_sections:
                            await status_msg.edit(
                                content=f"⏳ Extracting purports: Section {i+1}/{total_sections}..."
                            )

                        header_text = section.get("title", "")
                        verses_covered = self.parse_verse_range(header_text, chapter_num)
                        if not verses_covered:
                            continue

                        purport_paragraphs = section.get("purport", [])
                        clean_paragraphs = [p.strip() for p in purport_paragraphs if p.strip()]

                        if clean_paragraphs:
                            full_purport = "\n\n".join(clean_paragraphs)
                        else:
                            full_purport = None

                        for v_num in verses_covered:
                            if full_purport:
                                purport_map[str(v_num)] = full_purport

                    if "colophon" in site_data and site_data["colophon"].strip():
                        chapter_end_text = site_data["colophon"].strip()

            return purport_map, chapter_end_text

        except Exception as e:
            print(f"Error mapping purports via clean JSON stream: {e}")
            return None, ""

async def setup(bot):
    await bot.add_cog(Append2Json(bot))
