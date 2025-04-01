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
    def _get_chapter_path(self, chapter: int) -> Path:
        """Get the full path to a chapter JSON file"""
        return self.data_path / f"bg_ch{chapter:02d}.json"
    
    def _load_chapter_data(self, chapter: int) -> dict:
        """Load chapter data from JSON file"""
        file_path = self._get_chapter_path(chapter)
        if not file_path.exists():
            raise FileNotFoundError(f"Chapter {chapter} JSON file not found at {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _find_verse_data(self, chapter_data: dict, verse: str) -> dict:
        """Find specific verse data in chapter"""
        for verse_data in chapter_data["Verses"]:
            if verse_data["Text-num"] == f"TEXT {verse}":
                return verse_data
        raise ValueError(f"Verse {verse} not found in chapter data")
    
    def _validate_verse(self, chapter: int, verse: str) -> Tuple[bool, str]:
        """Validate chapter and verse input"""
        try:
            chapter = int(chapter)
            verse = str(verse)
            
            # Check if chapter file exists
            if not self._get_chapter_path(chapter).exists():
                return False, f"Chapter {chapter} not available"
            
            return True, verse
        except ValueError:
            return False, "Invalid chapter or verse format"

    # +------------------------------------------------------------+
    # |              Bhagavad gītā — As It Is 1972                 |
    # +------------------------------------------------------------+
    @commands.command(aliases=['bg1972', '1972', 'as_it_is'], no_pm=True)
    async def asitis(self, ctx, chapter: int, verse: str):
        """Retrieve a Bhagavad Gītā As It Is (1972) śloka from local JSON files"""
        
        # Input validation
        is_valid, validated_verse = self._validate_verse(chapter, verse)
        if not is_valid:
            return await ctx.send(f"❌ {validated_verse}")
        
        try:
            # Load data
            chapter_data = self._load_chapter_data(chapter)
            verse_data = self._find_verse_data(chapter_data, validated_verse)
            
            # Create embed
            embed = discord.Embed(
                title=f"Bhagavad Gītā As It Is [ {chapter}.{validated_verse} ]",
                color=discord.Color.orange(),
                description=f"**{chapter_data['Chapter-Desc']}**"
            )
            
            embed.add_field(
                name=f"TEXT {validated_verse}",
                value=f"```{verse_data['Verse-Text']}```",
                inline=False
            )
            
            if 'Uvaca-line' in verse_data:
                embed.add_field(
                    name="Spoken by",
                    value=verse_data['Uvaca-line'],
                    inline=False
                )
            
            embed.add_field(
                name="SYNONYMS",
                value=verse_data['Word-for-Word'],
                inline=False
            )
            
            embed.add_field(
                name="TRANSLATION",
                value=f"```\n{verse_data['Translation-En']}\n```",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error retrieving verse: {str(e)}")

async def setup(bot):
    await bot.add_cog(AsItIs(bot))
    
