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
from bs4 import BeautifulSoup
import aiohttp
from discord.ext import commands
from datetime import datetime

# Chapter info dict
BG_CHAPTER_INFO = {
    1: {'total_verses': 46, 'grouped_ranges': [(16, 18), (21, 22), (32, 35), (37, 38)]},
    2: {'total_verses': 72, 'grouped_ranges': [(42, 43)]},
    3: {'total_verses': 43, 'grouped_ranges': []},
    4: {'total_verses': 42, 'grouped_ranges': []},
    5: {'total_verses': 29, 'grouped_ranges': [(8, 9), (27, 28)]},
    6: {'total_verses': 47, 'grouped_ranges': [(11, 12), (13, 14), (20, 23)]},
    7: {'total_verses': 30, 'grouped_ranges': []},
    8: {'total_verses': 28, 'grouped_ranges': []},
    9: {'total_verses': 34, 'grouped_ranges': []},
    10: {'total_verses': 42, 'grouped_ranges': [(4, 5), (12, 13)]},
    11: {'total_verses': 55, 'grouped_ranges': [(10, 11), (26, 27), (41, 42)]},
    12: {'total_verses': 20, 'grouped_ranges': [(3, 4), (6, 7), (13, 14), (18, 19)]},
    13: {'total_verses': 35, 'grouped_ranges': [(1, 2), (6, 7), (8, 12)]},
    14: {'total_verses': 27, 'grouped_ranges': [(22, 25)]},
    15: {'total_verses': 20, 'grouped_ranges': [(3, 4)]},
    16: {'total_verses': 24, 'grouped_ranges': [(1, 3), (11, 12), (13, 15)]},
    17: {'total_verses': 28, 'grouped_ranges': [(7, 9), (14, 16), (23, 24)]},
    18: {'total_verses': 78, 'grouped_ranges': [(5, 6), (26, 27)]}
}

class BhagavadGita(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://vedabase.io/en/library/bg"
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command(aliases=['gita'], no_pm=True)
    async def bg(self, ctx, chapter: int, verse: str):
        """Retrieve a Bhagavad Gita verse from Vedabase.io"""
        
        # --- Input Validation Start ---
        is_valid, validated_verse_or_error = self.validate_input(chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        # Use the possibly modified verse string (e.g. a snapped grouped range)
        verse = validated_verse_or_error
        # --- Input Validation End ---

        url = f"{self.base_url}/{chapter}/{verse}/"
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return await ctx.send(f"Couldn't retrieve verse {chapter}.{verse}. Status: {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Get chapter title from breadcrumbs
                breadcrumbs = soup.find('nav', {'aria-label': 'Breadcrumb'})
                chapter_title = "Unknown Chapter"
                if breadcrumbs:
                    last_crumb = breadcrumbs.find_all('li')[-1]
                    chapter_title = last_crumb.text.strip().replace('»', '').strip()

                # Get verse data
                devanagari = self._get_verse_section(soup, 'av-devanagari')
                verse_text = self._get_verse_section(soup, 'av-verse_text')
                synonyms = self._get_verse_section(soup, 'av-synonyms')
                translation = self._get_verse_section(soup, 'av-translation')

                # Create embed
                embed = discord.Embed(
                    title=f"Chapter {chapter}: {chapter_title}",
                    colour=discord.Colour(0x1cfbc3),
                    url=url,
                    description=chapter_title,
                    timestamp=datetime.utcnow()
                )

                embed.set_author(
                    name="Bhagavad Gītā — As It Is",
                    url="https://vedabase.io/en/library/bg/",
                    icon_url="https://asitis.com/gif/bgcover.jpg"  # Book cover
                )
                embed.set_footer(text="Retrieved")

                embed.add_field(name="Devanagari", value=devanagari, inline=False)
                embed.add_field(name=f"Text {verse}", value=f"**{verse_text}**", inline=False)
                embed.add_field(name="Synonyms", value=f"> {synonyms}", inline=False)
                embed.add_field(name="Translation", value=f"**{translation}**", inline=False)

                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    def validate_input(self, chapter: int, verse_input: str):
        """
        Validate chapter and verse input against BG_CHAPTER_INFO.
        Returns a tuple (is_valid, result) where result is either an error message
        or the validated/modified verse string.
        """
        # Check if chapter exists
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
                
                # Check if the requested range falls inside any predefined grouped range
                for r_start, r_end in chapter_data['grouped_ranges']:
                    if start >= r_start and end <= r_end:
                        # If valid grouped range, use the complete grouped range
                        return (True, f"{r_start}-{r_end}")
                    # If there is partial overlap, flag an error
                    if (start <= r_end and end >= r_start):
                        return (False, f"Requested verses {start}-{end} overlap with predefined grouped range {r_start}-{r_end}.")
                
                # If no grouped range issues, assume the input is fine.
                return (True, f"{start}-{end}")
            except ValueError:
                return (False, "Invalid verse range format. Use for example '20-23' or a single verse like '21'.")
        
        # Handle a single verse
        try:
            verse_num = int(verse_input)
            if verse_num < 1 or verse_num > total_verses:
                return (False, f"Chapter {chapter} has only {total_verses} verses.")
            
            # Check if this verse belongs to any grouped range
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
        
        # Handle different section types differently
        if class_name == 'av-devanagari':
            text_div = section.find('div', class_='text-center')
            if text_div:
                # Replace <br> tags with newlines
                for br in text_div.find_all('br'):
                    br.replace_with('\n')
                return text_div.get_text(strip=False)
        
        elif class_name == 'av-verse_text':
            text_div = section.find('div', class_='italic')
            if text_div:
                for br in text_div.find_all('br'):
                    br.replace_with('\n')
                return text_div.get_text(strip=False)
        
        elif class_name == 'av-synonyms':
            text_div = section.find('div', class_='text-justify')
            if text_div:
                # Clean up synonyms text
                text = text_div.get_text(' ', strip=True)
                return ' '.join(text.split())  # Normalize whitespace
        
        elif class_name == 'av-translation':
            text_div = section.find('div', class_='s-justify')
            if text_div:
                return text_div.get_text(strip=True)
        
        return "Not available"

async def setup(bot):
    await bot.add_cog(BhagavadGita(bot))
