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
from typing import List, Tuple, Dict
from datetime import datetime

# v1.17
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
    17: {'total_verses': 28, 'grouped_ranges': [(5, 6), (26, 27)], 'chapter_title': '17. The Divisions of Faith'},
    18: {'total_verses': 78, 'grouped_ranges': [(13, 14), (36, 37), (51, 53)], 'chapter_title': '18. Conclusion-The Perfection of Renunciation'}
}


class AsItIs(commands.Cog):
    """ (∩｀-´)⊃━☆ﾟ.*･｡ﾟ Bhagavad Gītā As It Is (Original 1972 Macmillan edition)

    Free Plugin to print Gītā verses inside a Discord text-channel. Full embed support.

    Śrīla Prabhupāda's original 1972 Macmillan Bhagavad-gītā As It Is with elaborate commentary [not available here, yet], original Sanskrit and English word meanings. It is a first-class EXACT reproduction of the original hard cover book.

    No other philosophical or religious work reveals, in such a lucid and profound way, the nature of consciousness, the self, the universe and the Supreme.

    Bhagavad Gītā As It Is is the largest-selling, most widely used edition of the Gītā in the world.
    """
    def __init__(self, bot):
        self.bot = bot
        self.data_path = Path(__file__).parent / "gita"
        self._chapter_cache = {}  # Cache for loaded chapter data

    def _load_chapter_data(self, chapter: int) -> dict:
        """Load chapter data from JSON file with caching"""
        if chapter in self._chapter_cache:
            return self._chapter_cache[chapter]
            
        file_path = self.data_path / f"bg_ch{chapter:02d}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Chapter {chapter} data file not found")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._chapter_cache[chapter] = data
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in chapter {chapter} file: {str(e)}")

    def _validate_verse(self, chapter: int, verse: str) -> Tuple[bool, str]:
        """Validate chapter and verse input"""
        if chapter not in BG_CHAPTER_INFO:
            return False, f"Invalid chapter entry. Bhagavad Gītā has 18 chapters (requested {chapter})."
        
        chapter_info = BG_CHAPTER_INFO[chapter]
        
        # Handle multiple verses (e.g., "16-18")
        if '-' in verse:
            try:
                start, end = sorted(map(int, verse.split('-')))
                if start >= end:
                    return False, "Start verse must be less than end verse"
                
                # Check against predefined grouped ranges
                for r_start, r_end in chapter_info['grouped_ranges']:
                    if start == r_start and end == r_end:
                        return True, f"{start}-{end}"
                
                # Validate bounds
                if end > chapter_info['total_verses']:
                    return False, f"Chapter {chapter} only has {chapter_info['total_verses']} verses."
                if start < 1:
                    return False, "Verse numbers start at 1"
                
                return True, f"{start}-{end}"
            except ValueError:
                return False, "Invalid verse range format. Use like '16-18'"
        
        # Handle single verse
        try:
            verse_num = int(verse)
            if verse_num < 1 or verse_num > chapter_info['total_verses']:
                return False, f"Chapter {chapter} has verses 1-{chapter_info['total_verses']}"
            
            # Check if part of grouped range
            for r_start, r_end in chapter_info['grouped_ranges']:
                if r_start <= verse_num <= r_end:
                    return True, f"{r_start}-{r_end}"
            
            return True, verse
        except ValueError:
            return False, f"Invalid verse number: {verse}"

    def _find_verse_data(self, chapter_data: dict, verse_ref: str) -> dict:
        """Find verse data handling TEXT/TEXTS formats"""
        possible_keys = []
        base_ref = verse_ref.replace('-', '-')
        
        # Generate possible key variations
        for prefix in ['TEXT', 'TEXTS']:
            possible_keys.append(f"{prefix} {base_ref}")
            if '-' in base_ref:
                start = base_ref.split('-')[0]
                possible_keys.append(f"{prefix} {start}")
                possible_keys.append(f"{prefix} {base_ref.replace('-', '–')}")
        
        # Check each possible key
        for verse_data in chapter_data.get("Verses", []):
            if verse_data.get("Text-num", "") in possible_keys:
                return verse_data
        
        # Fallback search
        search_num = base_ref.split('-')[0] if '-' in base_ref else base_ref
        for verse_data in chapter_data.get("Verses", []):
            if search_num in verse_data.get("Text-num", ""):
                return verse_data
        
        raise ValueError(f"Verse {verse_ref} not found")

    def _format_verse_text(self, verse_data: dict) -> str:
        """Format verse text preserving line breaks and bold sections"""
        verse_text = verse_data.get('Verse-Text', '')
        
        # Replace ; with \n but preserve complete lines
        lines = []
        current_line = ""
        in_bold = False
        
        for char in verse_text:
            if char == ';' and not in_bold:
                if current_line:
                    lines.append(current_line.strip())
                    current_line = ""
                continue
                
            current_line += char
            if char == '*':
                in_bold = not in_bold
                
            if char == '\n':
                if current_line.strip():
                    lines.append(current_line.strip())
                current_line = ""
        
        if current_line.strip():
            lines.append(current_line.strip())
        
        # Handle Uvaca line
        formatted_text = '\n'.join(lines)
        if 'Uvaca-line' in verse_data:
            uvaca = verse_data['Uvaca-line'].strip()
            if not uvaca.endswith((':', '-', '—')):
                uvaca += ':'
            return f"{uvaca}\n{formatted_text}"
        
        return formatted_text

    def _format_synonyms(self, synonyms: str) -> List[str]:
        """Format synonyms and keep them in a single or two adjacent fields"""
        if not synonyms.strip():
            return ["No synonyms available"]
        
        # First clean up the synonyms string
        synonyms = synonyms.replace('\n', ' ')  # Remove any existing newlines
        synonyms = ' '.join(synonyms.split())  # Collapse multiple spaces
        
        # Format each synonym pair with italics
        formatted_items = []
        for item in synonyms.split(';'):
            item = item.strip()
            if not item:
                continue
                
            # Handle word-meaning separation
            if '—' in item:
                word, meaning = item.split('—', 1)
                formatted_items.append(f"_**{word.strip()}**_ — {meaning.strip()}")
            elif '-' in item and not any(c in item for c in ['ā', 'ī', 'ū', 'ṁ', 'ṣ', 'ṭ', 'ḥ']):
                parts = item.split('-', 1)
                formatted_items.append(f"_**{parts[0].strip()}**_ - {parts[1].strip()}")
            else:
                formatted_items.append(item)
        
        # Join all synonyms with semicolons and spaces
        formatted_text = '; '.join(formatted_items)
        
        # Only split if absolutely necessary (exceeds Discord char limit)
        if len(formatted_text) > 1000:
            # Split at natural break points (after semicolons)
            chunks = []
            current_chunk = ""
            for item in formatted_items:
                if len(current_chunk) + len(item) + 2 > 1000:  # +2 for "; "
                    chunks.append(current_chunk)
                    current_chunk = item
                else:
                    if current_chunk:
                        current_chunk += "; " + item
                    else:
                        current_chunk = item
            if current_chunk:
                chunks.append(current_chunk)
            return chunks
        
        return [formatted_text]

    def _format_translation(self, translation: str) -> List[str]:
        """Format translation with proper paragraph breaks"""
        if not translation:
            return ["No translation available"]
        
        # Clean up excessive whitespace
        translation = ' '.join(translation.split())
        return self._split_long_text(translation)

    def _split_long_text(self, text: str, max_len: int = 1000) -> List[str]:
        """Split text at natural breaks while preserving complete lines"""
        if len(text) <= max_len:
            return [text]
        
        lines = text.split('\n')
        chunks = []
        current_chunk = ""
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_len:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = line
                else:  # Single line too long
                    # Try to split at last space
                    split_pos = line.rfind(' ', 0, max_len-3)
                    if split_pos > 0:
                        chunks.append(line[:split_pos] + '...')
                        current_chunk = line[split_pos+1:]
                    else:
                        chunks.append(line[:max_len-3] + '...')
                        current_chunk = line[max_len-3:]
            else:
                if current_chunk:
                    current_chunk += '\n' + line
                else:
                    current_chunk = line
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _safe_add_field(self, embed: discord.Embed, name: str, value: str, inline: bool = False):
        """Add field with automatic splitting if needed"""
        if not value:
            return
        
        if isinstance(value, list):
            value = '\n'.join(value)
        
        chunks = self._split_long_text(str(value))
        embed.add_field(name=name, value=chunks[0], inline=inline)
        for chunk in chunks[1:]:
            embed.add_field(name="↳", value=chunk, inline=inline)

    # +------------------------------------------------------------+
    # |         Bhagavad Gītā As It Is (1972) Macmillan            |
    # +------------------------------------------------------------+
    @commands.command(name='asitis', aliases=['1972', 'bg'], no_pm=True)
    async def gita_verse(self, ctx, chapter: int, verse: str):
        """Retrieve a śloka from the Bhagavad Gītā As It Is (Original 1972 Macmillan edition):

        - Supports Chapter Title
        - Supports Sanskrit Text
        - Supports Synonyms
        - Supports English Translation
        - Supports multiple verses
        - No-support for elaborate commentaries, yet
        """
        start_time = datetime.now()
        
        # Validate input
        is_valid, verse_ref = self._validate_verse(chapter, verse)
        if not is_valid:
            return await ctx.send(f"🚫 {verse_ref}")
        
        try:
            # Load data
            chapter_data = self._load_chapter_data(chapter)
            verse_data = self._find_verse_data(chapter_data, verse_ref)
            
            # Create embed: Orange border-left
            embed = discord.Embed(
                color=discord.Color(0xF5A623),
                description=f"**Chapter {BG_CHAPTER_INFO[chapter]['chapter_title']}**"
            )
            
            # Add verse text field
            verse_text = self._format_verse_text(verse_data)
            self._safe_add_field(
                embed,
                name=f"ＴＥＸＴ {verse_ref}:",
                value=verse_text,
                inline=False
            )

            # Add Thumbnail with original artwork from BBT
            # embed.set_thumbnail(url="https://i.imgur.com/wGEGAiw.png")
            embed.set_author(
                name="Bhagavad Gītā — As It Is (Original 1972 edition)",
                icon_url="https://i.imgur.com/iZ6CHAz.png"
            )
            
            # Add synonyms (split into multiple fields if needed)
            synonyms = verse_data.get('Word-for-Word', '')
            synonyms_chunks = self._format_synonyms(synonyms)
            for i, chunk in enumerate(synonyms_chunks):
                self._safe_add_field(
                    embed,
                    name="ＳＹＮＯＮＹＭＳ:" if i == 0 else "↳",
                    value=chunk,
                    inline=False
                )
            
            # Add Translation (split into multiple fields if needed)
            translation = verse_data.get('Translation-En', '')
            translation_chunks = self._format_translation(translation)
            for i, chunk in enumerate(translation_chunks):
                self._safe_add_field(
                    embed,
                    name="ＴＲＡＮＳＬＡＴＩＯＮ:" if i == 0 else "↳",
                    value=f"> **{chunk}**",
                    inline=False
                )
            
            # Add Footer with time duration latency and IMG
            latency = (datetime.now() - start_time).total_seconds() * 1000
            v_text = "𝗌́𝗅𝗈𝗄𝖺" if verse_ref == 1 else "𝗌́𝗅𝗈𝗄𝖺𝗌"
            embed.set_footer(
                text=f"𝖠𝖽𝗁𝗒𝖺𝗒𝖺 {chapter}, {v_text} {verse_ref} 𝗈𝖿 {total_verses} ➜ retrieved in {latency:.2f} ms",
                icon_url="https://i.imgur.com/10jxmCh.png"
            )
            
            await ctx.send(embed=embed)
        
        except FileNotFoundError as e:
            await ctx.send(f"🚫 {str(e)}")
        except ValueError as e:
            await ctx.send(f"🚫 Error in verse data:\n\n{str(e)}")
        except Exception as e:
            await ctx.send(f"🚫 Unexpected error retrieving verse:\n\n{str(e)}")

async def setup(bot):
    await bot.add_cog(AsItIs(bot))
