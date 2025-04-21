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
import random
import time

from pathlib import Path
from discord.ext import commands
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta

# v2.27 - pass the context
BG_CHAPTER_INFO = {
    1: {'total_verses': 46, 'grouped_ranges': [(16, 18), (21, 22), (32, 35), (37, 38)], 'chapter_title': 'First. Observing the Armies on the Battlefield of Kurukṣetra'},
    2: {'total_verses': 72, 'grouped_ranges': [(42, 43)], 'chapter_title': 'Second. Contents of the Gītā Summarized'},
    3: {'total_verses': 43, 'grouped_ranges': [], 'chapter_title': 'Third. Karma-yoga'},
    4: {'total_verses': 42, 'grouped_ranges': [], 'chapter_title': 'Fourth. Transcendental Knowledge'},
    5: {'total_verses': 29, 'grouped_ranges': [(8, 9), (27, 28)], 'chapter_title': 'Fifth. Karma-yoga — Action in Kṛṣṇa Consciousness'},
    6: {'total_verses': 47, 'grouped_ranges': [(11, 12), (13, 14), (20, 23)], 'chapter_title': 'Sixth. Sāṅkhya-yoga'},
    7: {'total_verses': 30, 'grouped_ranges': [], 'chapter_title': 'Seventh. Knowledge of the Absolute'},
    8: {'total_verses': 28, 'grouped_ranges': [], 'chapter_title': 'Eighth. Attaining the Supreme'},
    9: {'total_verses': 34, 'grouped_ranges': [], 'chapter_title': 'Ninth. The Most Confidential Knowledge'},
    10: {'total_verses': 42, 'grouped_ranges': [(4, 5), (12, 13)], 'chapter_title': 'Tenth. The Opulence of the Absolute'},
    11: {'total_verses': 55, 'grouped_ranges': [(10, 11), (26, 27), (41, 42)], 'chapter_title': 'Eleventh. The Universal Form'},
    12: {'total_verses': 20, 'grouped_ranges': [(3, 4), (6, 7), (13, 14), (18, 19)], 'chapter_title': 'Twelfth. Devotional Service'},
    13: {'total_verses': 35, 'grouped_ranges': [(1, 2), (6, 7), (8, 12)], 'chapter_title': 'Thirteenth. Nature, the Enjoyer, and Consciousness'},
    14: {'total_verses': 27, 'grouped_ranges': [(22, 25)], 'chapter_title': 'Fourteenth. The Three Modes of Material Nature'},
    15: {'total_verses': 20, 'grouped_ranges': [(3, 4)], 'chapter_title': 'Fifteenth. The Yoga of the Supreme Person'},
    16: {'total_verses': 24, 'grouped_ranges': [(1, 3), (11, 12), (13, 15)], 'chapter_title': 'Sixteenth. The Divine and Demoniac Natures'},
    17: {'total_verses': 28, 'grouped_ranges': [(5, 6), (8, 10), (26, 27)], 'chapter_title': 'Seventeenth. The Divisions of Faith'},
    18: {'total_verses': 78, 'grouped_ranges': [(13, 14), (36, 37), (51, 53)], 'chapter_title': 'Eighteenth. Conclusion-The Perfection of Renunciation'}
}

class NavigationButtons(discord.ui.View):
    """View for handling verse navigation buttons"""
    def __init__(self, cog, chapter: int, verse_ref: str, ctx: commands.Context, timeout: float = 1800.0):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.chapter = chapter
        self.verse_ref = verse_ref
        self.ctx = ctx
        self.author = ctx.author
        self.message = None
        
        # Parse current verse reference
        self.current_start, self.current_end = self._parse_verse_ref(verse_ref)
        
        # Calculate previous and next verses
        self.prev_chapter, self.prev_verse = self._get_previous_verse()
        self.next_chapter, self.next_verse = self._get_next_verse()
        
        # Disable buttons if at boundaries
        if self.prev_chapter is None:
            self.children[0].disabled = True
        if self.next_chapter is None:
            self.children[1].disabled = True

        '''
        # Add the navigation buttons
        self.add_item(discord.ui.Button(label="◀ 𝖯𝗋𝖾𝗏𝗂𝗈𝗎𝗌 𝗌́𝗅𝗈𝗄𝖺", style=discord.ButtonStyle.grey, custom_id="prev_verse"))
        self.add_item(discord.ui.Button(label="𝖭𝖾𝗑𝗍 𝗌́𝗅𝗈𝗄𝖺 ▶", style=discord.ButtonStyle.grey, custom_id="next_verse"))

        # Add the close button
        self.add_item(discord.ui.Button(label="🗙 𝖢𝗅𝗈𝗌𝖾", style=discord.ButtonStyle.red, custom_id="close_button"))
        '''

    async def _navigate(self, interaction: discord.Interaction, chapter: int, verse_ref: str):
        """Handle navigation with latency tracking"""
        start_time = time.time()
        await interaction.response.defer()
        
        try:
            # Calculate actual navigation latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Create new embed with latency measurement
            new_embed = self.cog._create_verse_embed(chapter, verse_ref, latency_ms)
            new_view = NavigationButtons(self.cog, chapter, verse_ref, self.ctx)
            new_view.message = interaction.message
            
            # Update the message
            await interaction.message.edit(embed=new_embed, view=new_view)
            
        except Exception as e:
            await interaction.followup.send(f"Error navigating: {str(e)}", ephemeral=True)
    
    def _parse_verse_ref(self, verse_ref: str) -> Tuple[int, int]:
        """Parse verse reference into start and end numbers"""
        if isinstance(verse_ref, int):
            return verse_ref, verse_ref
        if '-' in str(verse_ref):
            parts = str(verse_ref).split('-')
            start = int(parts[0])
            end = int(parts[-1])  # Handles cases with multiple hyphens
            return start, end
        return int(verse_ref), int(verse_ref)
    
    def _get_previous_verse(self) -> Tuple[Optional[int], Optional[str]]:
        """Get the previous verse reference"""
        # Check if we're at the beginning of the Gita
        if self.chapter == 1 and self.current_start == 1:
            return None, None
        
        # Check if we need to go to previous chapter
        if self.current_start == 1:
            prev_chapter = self.chapter - 1
            if prev_chapter not in BG_CHAPTER_INFO:
                return None, None
            prev_verse = str(BG_CHAPTER_INFO[prev_chapter]['total_verses'])
            return prev_chapter, prev_verse
        
        # Get previous verse in same chapter
        prev_verse_num = self.current_start - 1
        
        # Check if previous verse is part of a grouped range
        for start, end in BG_CHAPTER_INFO[self.chapter]['grouped_ranges']:
            if start <= prev_verse_num <= end:
                return self.chapter, f"{start}-{end}"
        
        return self.chapter, str(prev_verse_num)
    
    def _get_next_verse(self) -> Tuple[Optional[int], Optional[str]]:
        """Get the next verse reference"""
        # Check if we're at the end of the Gita
        if self.chapter == 18 and self.current_end == BG_CHAPTER_INFO[18]['total_verses']:
            return None, None
        
        # Check if we need to go to next chapter
        if self.current_end == BG_CHAPTER_INFO[self.chapter]['total_verses']:
            next_chapter = self.chapter + 1
            if next_chapter not in BG_CHAPTER_INFO:
                return None, None
            return next_chapter, "1"
        
        # Get next verse in same chapter
        next_verse_num = self.current_end + 1
        
        # Check if next verse is part of a grouped range
        for start, end in BG_CHAPTER_INFO[self.chapter]['grouped_ranges']:
            if start <= next_verse_num <= end:
                return self.chapter, f"{start}-{end}"
        
        return self.chapter, str(next_verse_num)
    
    async def on_timeout(self):
        """Disable buttons when view times out"""
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass
    
    @discord.ui.button(label="◀ 𝖯𝗋𝖾𝗏𝗂𝗈𝗎𝗌 𝗌́𝗅𝗈𝗄𝖺", style=discord.ButtonStyle.grey, custom_id="prev_verse")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to navigate to previous verse"""
        if self.prev_chapter is None:
            await interaction.response.send_message("This is the first verse of the Bhagavad Gītā", ephemeral=True)
            return
        
        await self._navigate(interaction, self.prev_chapter, self.prev_verse)

    @discord.ui.button(label="𝖭𝖾𝗑𝗍 𝗌́𝗅𝗈𝗄𝖺 ▶", style=discord.ButtonStyle.grey, custom_id="next_verse")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to navigate to next verse"""
        if self.next_chapter is None:
            await interaction.response.send_message("This is the last verse of the Bhagavad Gītā", ephemeral=True)
            return
        
        await self._navigate(interaction, self.next_chapter, self.next_verse)

    @discord.ui.button(label="🗙 𝖢𝗅𝗈𝗌𝖾", style=discord.ButtonStyle.red, custom_id="close_button")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to close and delete embed"""
        # Check if the user who pressed the button is the one who invoked the command
        if interaction.user == self.author:
            # Delete the embed message
            await interaction.message.delete()
            # Try to delete the invoking command message (might fail if it's too old)
            try:
                await self.ctx.message.delete()
            except discord.NotFound:
                pass  # Message was already deleted
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I don't have permissions to delete the command message.", 
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                "Only the command author can close this.", 
                ephemeral=True
            )

class AsItIs(commands.Cog):
    """Bhagavad Gītā As It Is (Original 1972 Macmillan edition)

    Free Plugin to print Gītā verses inside a Discord's text-channel. (∩｀-´)⊃━☆ﾟ.*･｡ﾟ Full embed support and śloka Navigation.

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
            raise ValueError(f"Invalid JSON in **bg_ch{chapter}.json** file: {str(e)}")

    def _validate_verse(self, chapter: int, verse: str) -> Tuple[bool, str]:
        """Validate chapter and verse input"""
        if chapter not in BG_CHAPTER_INFO:
            return False, f"Invalid chapter entry. The Bhagavad Gītā As It Is only has 18 chapters and you requested **{chapter}**."
        
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
                    return False, "Verse numbers start at 1, there is no verse 0"
                
                return True, f"{start}-{end}"
            except ValueError:
                return False, "Invalid verse range format. Use like **17-18** or just the single verse to find the group."
        
        # Handle single verse
        try:
            verse_num = int(verse)
            if verse_num < 1 or verse_num > chapter_info['total_verses']:
                return False, f"Chapter {chapter} only has {chapter_info['total_verses']} ślokas, double check and try again."
            
            # Check if part of grouped range
            for r_start, r_end in chapter_info['grouped_ranges']:
                if r_start <= verse_num <= r_end:
                    return True, f"{r_start}-{r_end}"
            
            return True, verse
        except ValueError:
            return False, f"**{verse}** is an invalid śloka number, double check and try again."

    def _find_verse_data(self, chapter_data: dict, verse_ref: str) -> dict:
        """Find verse data handling TEXT/TEXTS formats"""
        verse_ref = str(verse_ref)
        base_ref = verse_ref.replace('-', '-')
        
        # First try exact match
        for verse_data in chapter_data.get("Verses", []):
            text_num = verse_data.get("Text-num", "")
            if f"TEXT {base_ref}" == text_num or f"TEXTS {base_ref}" == text_num:
                return verse_data
        
        # Then try partial match (for ranges)
        for verse_data in chapter_data.get("Verses", []):
            text_num = verse_data.get("Text-num", "")
            if base_ref in text_num:
                return verse_data
        
        # Finally try just the starting verse
        start_verse = base_ref.split('-')[0]
        for verse_data in chapter_data.get("Verses", []):
            text_num = verse_data.get("Text-num", "")
            if start_verse in text_num:
                return verse_data
        
        raise ValueError(f"Verse {verse_ref} not found in chapter data")

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
            elif '-' in item and not any(c in item for c in ['ā', 'ī', 'ū', 'ṁ', 'ṣ', 'ṭ', 'ḥ', 'ś', 'ḍ']):
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
            embed.add_field(name="\u200b", value=chunk, inline=inline)

    def _create_verse_embed(self, chapter: int, verse_ref: str, latency_ms: float = None) -> discord.Embed:
        """Create embed for a specific verse (used for navigation)"""
        chapter_data = self._load_chapter_data(chapter)
        verse_data = self._find_verse_data(chapter_data, verse_ref)

        # Create embed: Orange border-left
        embed = discord.Embed(
            color=discord.Color(0xF5A623),
            description=f"**𝖢𝗁𝖺𝗉𝗍𝖾𝗋 {chapter}. {BG_CHAPTER_INFO[chapter]['chapter_title'].split('. ', 1)[-1]}**"
        )

        # Add verse text field
        verse_text = self._format_verse_text(verse_data)
        self._safe_add_field(
            embed,
            name=f"📜 ᴛᴇxᴛ {verse_ref}:",
            value=verse_text,
            inline=False
        )

        # Add Thumbnail with original artwork from BBT
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
                name="📖 ꜱʏɴᴏɴʏᴍꜱ:" if i == 0 else "\u200b",
                value=chunk,
                inline=False
            )

        # Add Translation (split into multiple fields if needed)
        translation = verse_data.get('Translation-En', '')
        translation_chunks = self._format_translation(translation)
        for i, chunk in enumerate(translation_chunks):
            self._safe_add_field(
                embed,
                name="🗒️ ᴛʀᴀɴꜱʟᴀᴛɪᴏɴ:" if i == 0 else "\u200b",
                value=f"> **{chunk}**",
                inline=False
            )

        # Add Footer with verse info
        v_text = f"𝗏𝖾𝗋𝗌𝖾 {verse_ref}" if '-' not in str(verse_ref) else f"𝗏𝖾𝗋𝗌𝖾𝗌 {verse_ref}"
        total_v = BG_CHAPTER_INFO[chapter]['total_verses']
        footer_text = f"𝖢𝗁𝖺𝗉𝗍𝖾𝗋 {chapter}, {v_text} 𝗈𝖿 {total_v}"
        if latency_ms is not None:
            footer_text += f" ➜ 𝗇𝖺𝗏𝗂𝗀𝖺𝗍𝖾𝖽 𝗂𝗇 {latency_ms:.1f} 𝗆𝗌"
        
        embed.set_footer(
            text=footer_text,
            icon_url="https://i.imgur.com/10jxmCh.png"
        )

        # Check if this is the last verse and add the ending message
        verse_end = int(verse_ref.split('-')[-1])  # Ensure it's an integer for comparison
        if verse_end == BG_CHAPTER_INFO[chapter]['total_verses']:
            ordinal, title = BG_CHAPTER_INFO[chapter]['chapter_title'].split('. ', 1)
            embed.add_field(
                name="\u200b",
                value=f"Thus end the Bhaktivedanta Purports to the {ordinal} Chapter of the Śrīmad Bhagavad-gītā in the matter of {title}.",
                inline=False
            )

        return embed

    @commands.command(name='asitis', aliases=['1972', 'bg'], no_pm=True)
    async def gita_verse(self, ctx, chapter: int, verse: str):
        """Retrieve a śloka from the Bhagavad Gītā — As It Is (Original 1972 Macmillan edition)
          To ŚRĪLA BALADEVA VIDYĀBHŪṢAṆA who presented so nicely the "Govinda-bhāṣya" commentary on Vedānta philosophy.

        - Supports Chapter Title
        - Supports Sanskrit Text
        - Supports Synonyms
        - Supports English Translation
        - Supports multiple verses
        - Navigation to previous and next śloka
        - No-support for elaborate commentaries, yet
        """
        start_time = datetime.now()
        
        # Validate input
        is_valid, verse_ref = self._validate_verse(chapter, verse)
        if not is_valid:
            return await ctx.send(f"🚫 {verse_ref}", delete_after=9)
        
        try:
            # Create embed
            embed = self._create_verse_embed(chapter, verse_ref)
            
            # Add latency to footer
            latency = (datetime.now() - start_time).total_seconds() * 1000
            embed.set_footer(text=f"{embed.footer.text} ➜ 𝗋𝖾𝗍𝗋𝗂𝖾𝗏𝖾𝖽 𝗂𝗇 {latency:.1f} 𝗆𝗌",
                             icon_url=embed.footer.icon_url)
            
            # Create view with navigation buttons
            view = NavigationButtons(self, chapter, verse_ref, ctx)
            
            # Send message
            message = await ctx.send(embed=embed, view=view)
            view.message = message

        except FileNotFoundError as e:
            await ctx.send(f"🚫 {str(e)}", delete_after=90)
        except ValueError as e:
            await ctx.send(f"🚫 Error in verse data:\n\n{str(e)}", delete_after=90)
        except Exception as e:
            await ctx.send(f"🚫 Unexpected error retrieving verse:\n\n{str(e)}", delete_after=90)
            
async def setup(bot):
    await bot.add_cog(AsItIs(bot))
