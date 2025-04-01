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
import os

from typing import Tuple
from discord.ext import commands

# Chapter info dict
BG_CHAPTER_INFO = {
    1: {'total_verses': 46, 'grouped_ranges': [(16, 18), (21, 22), (32, 35), (37, 38)], 'chapter_title': '1. Observing the Armies on the Battlefield of Kurukṣetra'},
    2: {'total_verses': 72, 'grouped_ranges': [(42, 43)], 'chapter_title': '2. Contents of the Gītā Summarized'},
    3: {'total_verses': 43, 'grouped_ranges': [], 'chapter_title': '3. Karma-yoga'},
    4: {'total_verses': 42, 'grouped_ranges': [], 'chapter_title': '4. Transcendental Knowledge'},
    5: {'total_verses': 29, 'grouped_ranges': [(8, 9), (27, 28)], 'chapter_title': '5. Karma-yoga — Action in Kṛṣṇa Consciousness'},
    6: {'total_verses': 47, 'grouped_ranges': [(11, 12), (13, 14), (20, 23)], 'chapter_title': '6. Sāṅkhya-yoga'},
    7: {'total_verses': 30, 'grouped_ranges': [], 'chapter_title': '7. Knowledge of the Absolute'},
    8: {'total_verses': 28, 'grouped_ranges': [], 'chapter_title': '8. Attaining the Supreme'},
    9: {'total_verses': 34, 'grouped_ranges': [], 'chapter_title': '9. The Most Confidential Knowledge'},
    10: {'total_verses': 42, 'grouped_ranges': [(4, 5), (12, 13)], 'chapter_title': '10. The Opulence of the Absolute'},
    11: {'total_verses': 55, 'grouped_ranges': [(10, 11), (26, 27), (41, 42)], 'chapter_title': '11. The Universal Form'},
    12: {'total_verses': 20, 'grouped_ranges': [(3, 4), (6, 7), (13, 14), (18, 19)], 'chapter_title': '12. Devotional Service'},
    13: {'total_verses': 35, 'grouped_ranges': [(1, 2), (6, 7), (8, 12)], 'chapter_title': '13. Nature, the Enjoyer, and Consciousness'},
    14: {'total_verses': 27, 'grouped_ranges': [(22, 25)], 'chapter_title': '14. The Three Modes of Material Nature'},
    15: {'total_verses': 20, 'grouped_ranges': [(3, 4)], 'chapter_title': '15. The Yoga of the Supreme Person'},
    16: {'total_verses': 24, 'grouped_ranges': [(1, 3), (11, 12), (13, 15)], 'chapter_title': '16. The Divine and Demoniac Natures'},
    17: {'total_verses': 28, 'grouped_ranges': [(7, 9), (14, 16), (23, 24)], 'chapter_title': '17. The Divisions of Faith'},
    18: {'total_verses': 78, 'grouped_ranges': [(5, 6), (26, 27)], 'chapter_title': '18. Conclusion-The Perfection of Renunciation'}
}

class AsItIs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = "modmail-plugins/asitis/gita"  # Path to JSON files

    # +------------------------------------------------------------+
    # |               JSON chapters with verses                    |
    # +------------------------------------------------------------+
    async def load_chapter_data(self, chapter: int):
        """Load JSON data for a specific chapter"""
        file_path = os.path.join(self.data_path, f"bg_ch{chapter:02d}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Chapter {chapter} data not found")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid data format for chapter {chapter}")

    def find_verse_data(self, chapter_data, verse_num: str):
        """Find verse data in chapter JSON"""
        for verse_data in chapter_data["Verses"]:
            if verse_data["Text-num"] == f"TEXT {verse_num}":
                return verse_data
        return None

    # +------------------------------------------------------------+
    # |               Bhagavad gītā As It Is 1972                  |
    # +------------------------------------------------------------+
    @commands.command(name=['asitis'], aliases=['1972'], no_pm=True)
    async def as_it_is(self, ctx, chapter: int, verse: str):
        """Retrieve a Bhagavad Gita śloka from local JSON files"""
        
        # Input Validation
        is_valid, validated_verse_or_error = self.validate_input(chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        verse = validated_verse_or_error
        
        try:
            # Load chapter data
            chapter_data = await self.load_chapter_data(chapter)
            
            # Get verse data
            verse_data = self.find_verse_data(chapter_data, verse)
            if not verse_data:
                return await ctx.send(f"Verse {chapter}.{verse} not found in data files")
            
            # Get chapter title from our dictionary
            chapter_title = self.get_chapter_title(chapter)
            
            # Create and send embed
            embed = discord.Embed(
                title=f"Bhagavad Gītā — As It Is (₁₉₇₂) [ {chapter}.{verse} ]",
                colour=discord.Colour(0xed791d),  # orange colour border-left
                description=f"**Chapter {chapter_title}**"
            )
            
            # Add fields with smart splitting
            await self._add_field_safe(embed, f"TEXT {verse}:", f"**{verse_data['Verse-Text']}**")
            
            if 'Uvaca-line' in verse_data:
                await self._add_field_safe(embed, "Spoken by:", verse_data['Uvaca-line'])
            
            synonyms = verse_data.get('Word-for-Word', 'Not available')
            await self._add_field_safe(embed, "SYNONYMS:", synonyms)
            
            translation = verse_data.get('Translation-En', 'Not available')
            await self._add_field_safe(embed, "TRANSLATION:", f"**```\n{translation}\n```**")
            
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"🚫 Error retrieving verse: \n{str(e)}")
            if hasattr(self.bot, 'logger'):
                self.bot.logger.error(f"BG command failed: \n\n{e}", exc_info=True)

    # +------------------------------------------------------------+
    # |                 FUNCTION TO VALIDATE                       |
    # +------------------------------------------------------------+
    def validate_input(self, chapter: int, verse_input: str):
        """
        Validate chapter and verse input against BG_CHAPTER_INFO.
        Returns a tuple (is_valid, result) where result is either an error message
        or the validated/modified verse string.
        """
        if chapter not in BG_CHAPTER_INFO:
            return (False, f"Invalid chapter. Bhagavad Gītā has 18 chapters (requested {chapter}).")
        
        chapter_data = BG_CHAPTER_INFO[chapter]
        total_verses = chapter_data['total_verses']

        # Handle a verse range (e.g., "20-23")
        if '-' in verse_input:
            try:
                start, end = sorted(map(int, verse_input.split('-')))
                if end > total_verses:
                    return (False, f"Chapter {chapter} only has {total_verses} verses.")
                
                for r_start, r_end in chapter_data['grouped_ranges']:
                    if start >= r_start and end <= r_end:
                        return (True, f"{r_start}-{r_end}")
                    if (start <= r_end and end >= r_start):
                        return (False, f"Requested verses {start}-{end} overlap with predefined grouped range {r_start}-{r_end}.")
                
                return (True, f"{start}-{end}")
            except ValueError:
                return (False, "Invalid verse range format. Use for example '20-23' or a single verse like '21'.")
        
        # Handle a single verse
        try:
            verse_num = int(verse_input)
            if verse_num < 1 or verse_num > total_verses:
                return (False, f"Chapter {chapter} has only {total_verses} verses.")
            
            for r_start, r_end in chapter_data['grouped_ranges']:
                if r_start <= verse_num <= r_end:
                    return (True, f"{r_start}-{r_end}")
            
            return (True, str(verse_num))
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")

    def _get_verse_section(self, soup, class_name):
        """Helper method to extract verse sections"""
        section = soup.find('div', class_=class_name)
        if not section:
            return "Not available"
        
        if class_name == 'av-devanagari':
            text_div = section.find('div', class_='text-center')
            if text_div:
                for br in text_div.find_all('br'):
                    br.replace_with('\n')
                return text_div.get_text(strip=False)
        
        elif class_name == 'av-verse_text':  # new method to get all the verses from the <div>
            verse_parts = []
            for italic_div in section.find_all('div', class_='italic'):
                for br in italic_div.find_all('br'):
                    br.replace_with('\n')
                verse_parts.append(italic_div.get_text(strip=False))
            return '\n'.join(verse_parts)

        elif class_name == 'av-synonyms':
            text_div = section.find('div', class_='text-justify')
            if text_div:
                # Process the content as before
                for a in text_div.find_all('a'):
                    if '-' in a.text:
                        parent_span = a.find_parent('span', class_='inline')
                        if parent_span:
                            hyphenated_term = '_' + a.text + '_'
                            parent_span.replace_with(hyphenated_term)
                
                for em in text_div.find_all('em'):
                    em.replace_with(f"_{em.get_text(strip=True)}_")
                
                text = text_div.get_text(' ', strip=True)
                text = text.replace(' - ', '-')
                text = text.replace(' ;', ';')
                text = text.replace(' .', '.')
                return text  # Return as clean string, not list

        elif class_name == 'av-translation':
            text_div = section.find('div', class_='s-justify')
            if text_div:
                return text_div.get_text(strip=True)
        
        return "Not found: 404"

    def _split_content(self, text: str, max_len: int = 1020) -> list:
        """Smart content splitting at natural breaks"""
        if len(text) <= max_len:
            return [text]
        
        # For synonyms, try to split at semicolons first
        if ';' in text:
            parts = []
            current_chunk = ""
            
            for segment in text.split(';'):
                segment = segment.strip()
                if not segment:
                    continue
                    
                temp_chunk = f"{current_chunk}; {segment}" if current_chunk else segment
                if len(temp_chunk) <= max_len:
                    current_chunk = temp_chunk
                else:
                    if current_chunk:
                        parts.append(current_chunk)
                    current_chunk = segment
            
            if current_chunk:
                parts.append(current_chunk)
                
            if len(parts) > 1:
                # Add semicolons back (except last item)
                parts = [f"{p};" for p in parts[:-1]] + [parts[-1]]
                return parts
        
        # Fallback for non-synonyms or if semicolon split isn't enough
        chunks = []
        while text:
            # Try to split at the last semicolon, comma, or space before max_len
            split_pos = max(
                text.rfind(';', 0, max_len),
                text.rfind(',', 0, max_len),
                text.rfind(' ', 0, max_len)
            )
            
            if split_pos <= 0:
                split_pos = max_len
                
            chunk = text[:split_pos].strip()
            chunks.append(chunk)
            text = text[split_pos:].strip()
        
        return chunks

    async def _add_field_safe(self, embed, name, value, inline=False):
        """Add field with automatic splitting if needed"""
        if not value:
            return
        
        # Convert to string if somehow we got a list
        if isinstance(value, list):
            value = ' '.join(value)
        
        chunks = self._split_content(str(value))
        embed.add_field(name=name, value=chunks[0], inline=inline)
        for chunk in chunks[1:]:
            embed.add_field(name="↳", value=chunk, inline=inline)

    def get_chapter_title(self, chapter: int) -> str:
        """Get chapter title from BG_CHAPTER_INFO"""
        return BG_CHAPTER_INFO.get(chapter, {}).get('chapter_title', f"Chapter {chapter}")

async def setup(bot):
    await bot.add_cog(AsItIs(bot))
    
