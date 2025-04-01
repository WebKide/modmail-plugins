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

from pathlib import Path
from discord.ext import commands
from typing import Tuple
from datetime import datetime

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
        self.data_path = Path(__file__).parent / "gita"  # Path to JSON files

    # +------------------------------------------------------------+
    # |               JSON chapters with verses                    |
    # +------------------------------------------------------------+
    def _validate_verse(self, chapter: int, verse: str) -> tuple:
        """Validate chapter and verse using BG_CHAPTER_INFO"""
        if chapter not in BG_CHAPTER_INFO:
            return False, f"Invalid chapter. Bhagavad Gītā has 18 chapters (requested {chapter})."
        
        chapter_info = BG_CHAPTER_INFO[chapter]
        
        # Handle verse ranges (e.g., "16-18")
        if '-' in verse:
            try:
                start, end = map(int, verse.split('-'))
                if start > end:
                    start, end = end, start
                
                # Check against grouped ranges
                for r_start, r_end in chapter_info['grouped_ranges']:
                    if start == r_start and end == r_end:
                        return True, f"{start}-{end}"
                
                # Validate range bounds
                if end > chapter_info['total_verses']:
                    return False, f"Chapter {chapter} only has {chapter_info['total_verses']} verses."
                
                return True, f"{start}-{end}"
            except ValueError:
                return False, "Invalid verse range format. Use like '16-18' or single verse '1'"
        
        # Handle single verse
        try:
            verse_num = int(verse)
            if verse_num < 1 or verse_num > chapter_info['total_verses']:
                return False, f"Chapter {chapter} has only {chapter_info['total_verses']} verses."
            
            # Check if verse is part of a grouped range
            for r_start, r_end in chapter_info['grouped_ranges']:
                if r_start <= verse_num <= r_end:
                    return True, f"{r_start}-{r_end}"
            
            return True, str(verse_num)
        except ValueError:
            return False, f"Invalid verse number: {verse}"

    def _load_chapter_data(self, chapter: int) -> dict:
        """Load chapter data from JSON file"""
        file_path = self.data_path / f"bg_ch{chapter:02d}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Chapter {chapter} data file not found")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _find_verse_data(self, chapter_data: dict, verse_ref: str) -> dict:
        """Find verse data using TEXT X or TEXT X-Y format"""
        search_key = f"TEXT {verse_ref}"
        for verse_data in chapter_data["Verses"]:
            if verse_data["Text-num"] == search_key:
                return verse_data
        raise ValueError(f"Verse {verse_ref} not found in chapter data")

    def _format_synonyms(self, synonyms: str) -> str:
        """Format synonyms with italics for Sanskrit terms"""
        parts = []
        for item in synonyms.split(';'):
            item = item.strip()
            if '—' in item:
                word, meaning = item.split('—', 1)
                parts.append(f"_{word.strip()}_ — {meaning.strip()}")
            else:
                parts.append(item)
        return '; '.join(parts)

    @commands.command(name='asitis', aliases=['bg1972', '1972'])
    async def gita_verse(self, ctx, chapter: int, verse: str):
        """Retrieve a Bhagavad Gita verse with full validation and formatting"""
        start_time = datetime.now()
        
        # Validate input using BG_CHAPTER_INFO
        is_valid, verse_ref = self._validate_verse(chapter, verse)
        if not is_valid:
            return await ctx.send(f"🚫 {verse_ref}")
        
        try:
            # Load data
            chapter_data = self._load_chapter_data(chapter)
            verse_data = self._find_verse_data(chapter_data, verse_ref)
            
            # Create embed
            embed = discord.Embed(
                title=f"Bhagavad Gītā — As It Is (₁₉₇₂) [ {chapter}.{verse_ref} ]",
                color=discord.Color(0x50e3c2),
                description=f"**{BG_CHAPTER_INFO[chapter]['chapter_title']}**"
            )
            
            #  Thumbnail with ORIGINAL artwork by BBT artists
            embed.set_thumbnail(url="https://imgur.com/wGEGAiw.png")

            # Build verse text with uvaca line if present
            verse_text = verse_data['Verse-Text']
            if 'Uvaca-line' in verse_data:
                verse_text = f"{verse_data['Uvaca-line']}\n{verse_text}"
            
            embed.add_field(
                name=f"TEXT {verse_ref}:",
                value=verse_text,
                inline=False
            )
            
            # Add formatted synonyms
            embed.add_field(
                name="SYNONYMS:",
                value=self._format_synonyms(verse_data['Word-for-Word']),
                inline=False
            )
            
            # Add translation
            embed.add_field(
                name="TRANSLATION:",
                value=f"**```\n{verse_data['Translation-En']}\n```**",
                inline=False
            )
            
            # Calculate latency
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            # Set footer with latency
            embed.set_footer(text=f"Śloka retrieved in {latency:.2f} ms", icon_url="https://imgur.com/wGEGAiw.png")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"🚫 Error retrieving verse:\n {str(e)}")

async def setup(bot):
    await bot.add_cog(AsItIs(bot))
