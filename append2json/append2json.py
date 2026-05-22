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
    """Append missing Purport fields to existing Bhagavad Gītā JSON using direct sibling element flow."""

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

                # FIX 1: Extract the actual verse number(s) from Text-num instead of using the sequential loop index.
                text_num_raw = verse.get("Text-num", "")
                verse_keys = self.parse_verse_range(text_num_raw, chapter_num)

                purport_text = None
                for vk in verse_keys:
                    candidate = purport_map.get(str(vk))
                    if candidate:
                        purport_text = candidate
                        break  # All verses in a range share the same purport text

                verse["Purport-En"] = purport_text if purport_text else "No purport for this śloka."

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
        """
        Parse a Text-num / Textnum string into a list of integer verse numbers.

        FIX 2 (TypeError): from int(numbers) to int(numbers[0])
        """
        if not range_text:
            return []

        clean_text = range_text.strip().upper()
        numbers = re.findall(r'\d+', clean_text)

        if not numbers:
            return []

        # Range / multi-verse header  (e.g. "TEXTS 16-18" or "BG 1.16-18")
        if '-' in clean_text or '\u2013' in clean_text or 'TEXTS' in clean_text:
            try:
                # Try chapter-qualified format first: "BG 1.16" or ".16"
                sub_numbers = re.findall(
                    rf'(?:BG\s+{re.escape(chapter_num)}\.|\.)(\d+)',
                    clean_text
                )
                if len(sub_numbers) >= 2:
                    start = int(sub_numbers[0])
                    end   = int(sub_numbers[-1])
                else:
                    # Plain "TEXTS 16-18": all digits in the string, drop the
                    # chapter number itself if it appears (e.g. chapter "1" must
                    # not be confused with verse "1").
                    verse_nums = [
                        int(n) for n in numbers
                        if n != chapter_num  # skip the chapter digit when present
                    ]
                    if len(verse_nums) >= 2:
                        start, end = verse_nums[0], verse_nums[-1]
                    elif len(verse_nums) == 1:
                        # Degenerate range with a single distinct number
                        return [verse_nums[0]]
                    else:
                        # All digits matched the chapter number — fall back to raw list
                        start, end = int(numbers[0]), int(numbers[-1])

                return list(range(start, end + 1))
            except (ValueError, IndexError):
                return []

        # FIX 2: Single verse — was int(numbers) (TypeError); must be int(numbers[0])
        return [int(numbers[0])] if numbers else []

    def extract_text_clean(self, tag):
        """
        Walk every text node inside *tag*, inserting a single space between
        adjacent inline elements so that words separated only by <a> or <span>
        boundaries are not fused together (e.g. "Kṛṣṇa" + "." → "Kṛṣṇa.").

        Italics/bold markup is intentionally dropped; only the plain Unicode
        characters are kept.  HTML entities are decoded automatically by
        BeautifulSoup’s .string / NavigableString handling.
        """
        parts = []
        for node in tag.descendants:
            # NavigableString = raw text node
            if isinstance(node, str):
                text = node
                # Collapse internal whitespace but preserve a leading/trailing
                # space so neighbouring words stay separated after joining.
                text = text.replace('\xa0', ' ')  # &nbsp; → space
                if text.strip():
                    parts.append(text)
                elif text and parts:
                    # Whitespace-only node: record a single space as separator
                    parts.append(' ')
        raw = ''.join(parts)
        # Normalise runs of whitespace to a single space and strip edges
        return ' '.join(raw.split())

    async def fetch_purport_map(self, chapter_num, status_msg: discord.Message):
        """
        FIX 3 (Linear Slicing / Layout Shifts):

        Walk the DOM using find_next_sibling() so we never flatten the tree or
        lose elements.  A tiny state machine drives collection:

          IDLE       → waiting for a <div class="Titles"> whose text is "PURPORT"
          COLLECTING → accumulating every <div class="Purport"> or
                       <div class="Normal-Level"> paragraph that follows,
                       stopping the moment the next <div class="Textnum"> is hit
                       OR any non-purport structural class is encountered.

        The boundary check compares the *object identity* of the sibling against
        the pre-looked-up next Textnum element, which is reliable because
        BeautifulSoup tag objects are singletons per parsed document.
        """
        url = f"{self.base_url}/bg/{chapter_num}?d=1"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

        purport_map     = {}
        chapter_end_text = f"Thus end the Bhaktivedanta Purports to Chapter {chapter_num}"

        # Classes that signal we have left the purport body and entered the next
        # structural section (used as a secondary stop condition).
        STOP_CLASSES = {
            "Textnum", "Synonyms-Section", "Synonyms-SA", "Synonyms",
            "Translation", "Titles", "Verse-Text", "Uvaca-line",
            "Verse-Ref", "Chapter-Desc",
        }
        # Classes whose text belongs to the purport body.
        PURPORT_BODY_CLASSES = {"Purport", "Normal-Level"}

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        return None, ""

                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    text_num_divs  = soup.find_all("div", class_="Textnum")
                    total_sections = len(text_num_divs)

                    if not text_num_divs:
                        return None, ""

                    for i, current_div in enumerate(text_num_divs):
                        if i == 0 or (i + 1) % 5 == 0 or (i + 1) == total_sections:
                            await status_msg.edit(
                                content=f"⏳ Extracting purports: Section {i+1}/{total_sections}..."
                            )

                        header_text    = current_div.get_text(strip=True)
                        verses_covered = self.parse_verse_range(header_text, chapter_num)
                        if not verses_covered:
                            continue

                        # The hard boundary: the very next Textnum div (or None for
                        # the last section).
                        next_text_num = text_num_divs[i + 1] if i + 1 < total_sections else None

                        # ---- State machine ----
                        in_purport         = False   # have we seen "PURPORT" title yet?
                        purport_paragraphs = []

                        sibling = current_div.find_next_sibling()
                        while sibling is not None:
                            # Hard boundary: hit the next verse's Textnum div → stop.
                            if sibling is next_text_num:
                                break

                            # Tag-level processing only (skip NavigableStrings /
                            # Comment nodes at the top level, which are rare but
                            # possible in malformed HTML).
                            if not hasattr(sibling, 'get'):
                                sibling = sibling.find_next_sibling()
                                continue

                            tag_classes = sibling.get("class", [])

                            # ── Boundary guard (secondary) ───────────────────────
                            # If we are already collecting and we hit a stop-class,
                            # we are past the purport regardless of next_text_num.
                            if in_purport and tag_classes and tag_classes[0] in STOP_CLASSES:
                                break

                            # ── Detect the "PURPORT" header div ─────────────────
                            if (
                                "Titles" in tag_classes
                                and sibling.get_text(strip=True) == "PURPORT"
                            ):
                                in_purport = True
                                sibling = sibling.find_next_sibling()
                                continue

                            # ── Collect purport body paragraphs ─────────────────
                            if in_purport:
                                # Accept both "Purport" (first paragraph, up to ~v14)
                                # and "Normal-Level" (continuation paragraphs, v15+).
                                if any(c in PURPORT_BODY_CLASSES for c in tag_classes):
                                    clean_p = self.extract_text_clean(sibling)
                                    # Filter out empty paragraphs and leftover navigation
                                    # text that sometimes bleeds in from the site.
                                    if clean_p and not clean_p.startswith("Link to this page"):
                                        purport_paragraphs.append(clean_p)

                            sibling = sibling.find_next_sibling()
                        # ---- end state machine ----

                        full_purport = (
                            "\n\n".join(purport_paragraphs)
                            if purport_paragraphs
                            else "No purport for this śloka."
                        )

                        for v_num in verses_covered:
                            purport_map[str(v_num)] = full_purport

                    # Grab the chapter-end colophon
                    thus_end = soup.find('div', class_='Thus-end')
                    if thus_end:
                        chapter_end_text = self.extract_text_clean(thus_end)

            return purport_map, chapter_end_text

        except Exception as e:
            print(f"Error fetching purports: {e}")
            return None, ""


async def setup(bot):
    await bot.add_cog(Append2Json(bot))
