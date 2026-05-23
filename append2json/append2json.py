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
from discord.ext import commands

__version__ = "4.0 - Offline HTML Parser"

class Append2Json(commands.Cog):
    """Append missing Purport fields to JSON using an attached HTML source file."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='append2json')
    async def append_json(self, ctx):
        """
        Usage:
        Attach BOTH your template .json file AND the source .html file in one message.
        """
        # Ensure there are exactly two files attached
        if len(ctx.message.attachments) != 2:
            return await ctx.send("❓ Please attach exactly **two files**: your `.json` file and the source `.html` file.")

        json_attachment = None
        html_attachment = None

        # Sort the attachments by their file type extensions
        for attachment in ctx.message.attachments:
            if attachment.filename.endswith('.json'):
                json_attachment = attachment
            elif attachment.filename.endswith('.html') or attachment.filename.endswith('.htm'):
                html_attachment = attachment

        if not json_attachment or not html_attachment:
            return await ctx.send("❌ Missing files! Make sure you upload one `.json` file and one `.html` file.")

        status_msg = await ctx.send("⏳ **[1/3]** Reading uploaded files from Discord...")

        try:
            # Load the user's template JSON file
            json_bytes = await json_attachment.read()
            user_json_data = json.loads(json_bytes.decode('utf-8'))

            # Load the source HTML file as a plain text string
            html_bytes = await html_attachment.read()
            html_content = html_bytes.decode('utf-8')

            # Extract the chapter number from the JSON file
            chapter_num = self.extract_chapter_number(user_json_data.get("Chapter-Desc", ""))
            if not chapter_num:
                return await status_msg.edit(content="❌ Could not find the chapter number in 'Chapter-Desc'.")

            await status_msg.edit(content=f"⏳ **[2/3]** Parsing HTML data for Chapter {chapter_num}...")

            # Extract the purports from the HTML string
            purport_map = self.parse_purports_from_html(html_content, chapter_num)

            if not purport_map:
                return await status_msg.edit(content=f"❌ Failed to find any purports matching `bg/{chapter_num}/` in the HTML file.")

            # Update the verses inside the JSON structure
            verses = user_json_data.get("Verses", [])
            for idx, verse in enumerate(verses, start=1):
                verse["Purport-title"] = "PURPORT"

                text_num_raw = verse.get("Text-num", "")
                verse_keys = self.parse_verse_range(text_num_raw, chapter_num)

                # Match the verse keys against our extracted map
                purport_text = None
                for vk in verse_keys:
                    candidate = purport_map.get(str(vk))
                    if candidate:
                        purport_text = candidate
                        break  

                verse["Purport-En"] = purport_text if purport_text else "No purport for this śloka."

                # If this is the last verse, attach standard closing text block markers
                if idx == len(verses):
                    verse["Chapter-end"] = "Chapter End"
                    verse["Chapter-En"] = f"Thus end the Bhaktivedanta Purports to Chapter {chapter_num}."

            # Save and export the finished JSON package
            await status_msg.edit(content="⏳ **[3/3]** Creating final JSON file package...")
            output_json = json.dumps(user_json_data, ensure_ascii=False, indent=2)

            # Safety size check before uploading to Discord
            if len(output_json.encode('utf-8')) > 8000000:
                return await status_msg.edit(content="❌ The final file is too large for Discord's upload limits.")

            await status_msg.edit(content=f"✅ **Success!** Processed {len(verses)} verses using offline HTML blocks.")

            new_filename = json_attachment.filename.replace(".json", "_enhanced.json")
            await ctx.send(file=discord.File(io.StringIO(output_json), filename=new_filename))

        except json.JSONDecodeError:
            await ctx.send("❌ The uploaded JSON file contains syntax errors.")
        except Exception as e:
            await ctx.send(f"❌ Processing Error: {str(e)}")

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
                sub_numbers = re.findall(rf'(?:BG\s+{re.escape(chapter_num)}\.|\.)(\d+)', clean_text)
                if len(sub_numbers) >= 2:
                    start, end = int(sub_numbers[0]), int(sub_numbers[-1])
                else:
                    verse_nums = [int(n) for n in numbers if n != chapter_num]
                    if len(verse_nums) >= 2:
                        start, end = verse_nums[0], verse_nums[-1]
                    elif len(verse_nums) == 1:
                        return [verse_nums[0]]
                    else:
                        start, end = int(numbers[0]), int(numbers[-1])
                return list(range(start, end + 1))
            except Exception:
                return []
        return [int(numbers[0])] if numbers else []

    def parse_purports_from_html(self, html_content, chapter_num):
        """Extracts text paragraphs from elements with data-section="purport"."""
        purport_map = {}

        # Regex pattern finds paragraphs with data-section="purport" and grabs the verse number
        # Example pattern matches: data-section="purport" data-verse-key="bg/18/1"
        pattern = r'<p[^>]*data-section="purport"[^>]*data-verse-key="bg/' + re.escape(str(chapter_num)) + r'/(\d+)"[^>]*>(.*?)</p>'
        matches = re.findall(pattern, html_content, re.DOTALL)

        # Temporary dictionary to collect multiple paragraphs for each verse
        temp_groups = {}
        for verse_num, p_content in matches:
            # Clean up residual inner HTML layout tags (like <em> or </em>)
            clean_p = re.sub(r'<[^>]+>', '', p_content).strip()
            if not clean_p:
                continue

            if verse_num not in temp_groups:
                temp_groups[verse_num] = []
            temp_groups[verse_num].append(clean_p)

        # Merge the text fragments using double line breaks
        for verse_num, paragraphs in temp_groups.items():
            purport_map[str(verse_num)] = "\n\n".join(paragraphs)

        return purport_map

async def setup(bot):
    await bot.add_cog(Append2Json(bot))
