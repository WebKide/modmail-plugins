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
import aiohttp
import random
import asyncio
import time

from bs4 import BeautifulSoup
from fake_useragent import UserAgent  # pip install fake-useragent
from typing import Tuple, Union
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
        self.ua = UserAgent()
        self.session = None
        self.last_request_time = 0
        self.request_delay = 2  # seconds between requests
        
    async def ensure_session(self):
        """Initialize session with proper headers if not exists"""
        if not self.session or self.session.closed:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://vedabase.io/',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)

    async def scrape_with_retry(self, url, max_retries=3):
        """Robust scraping with retry logic"""
        await self.ensure_session()
        
        for attempt in range(max_retries):
            try:
                # Respect crawl delay
                elapsed = time.time() - self.last_request_time
                if elapsed < self.request_delay:
                    await asyncio.sleep(self.request_delay - elapsed)
                
                self.last_request_time = time.time()
                
                # Rotate user agent
                self.session.headers.update({'User-Agent': self.ua.random})
                
                async with self.session.get(url) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 5))
                        await asyncio.sleep(retry_after)
                        continue
                        
                    if response.status == 403:
                        raise ValueError("Access forbidden - potentially blocked")
                        
                    if response.status != 200:
                        continue
                        
                    return await response.text()
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1 + random.random())
                
        raise ValueError(f"Failed after {max_retries} attempts")

    # +------------------------------------------------------------+
    # |                     Bhagavad gītā CMD                      |
    # +------------------------------------------------------------+
    @commands.command(aliases=['gita'], no_pm=True)
    async def bg(self, ctx, chapter: int, verse: str):
        """Retrieve a Bhagavad Gita śloka from Vedabase.io
        - Supports Devanagari, Sanskrit, Synonyms and Translation
        """
        
        # Input Validation
        is_valid, validated_verse_or_error = self.validate_input(chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        verse = validated_verse_or_error
        url = f"{self.base_url}/{chapter}/{verse}/"
        
        try:
            # Use scrape_with_retry instead of direct session call
            html = await self.scrape_with_retry(url)
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

            # Create and send embed
            embed = discord.Embed(
                title="Bhagavad Gītā — As It Is",
                colour=discord.Colour(0x1cfbc3),
                url=url,
                description=chapter_title,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Retrieved")

            # Add fields with smart splitting
            await self._add_field_safe(embed, "Devanagari", devanagari)
            await self._add_field_safe(embed, f"Text {verse}", f"**{verse_text}**")
            await self._add_field_safe(embed, "Synonyms", f"> {synonyms}")
            await self._add_field_safe(embed, "Translation", f"**```\n{translation}\n```**")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"🚫 Error retrieving verse: \n{str(e)}")
            if hasattr(self.bot, 'logger'):
                self.bot.logger.error(f"BG command failed: \n\n{e}", exc_info=True)

    def cog_unload(self):
        if self.session:
            self.bot.loop.create_task(self.session.close())

    # +------------------------------------------------------------+
    # |                 FUNCTION TO SCRAPE WEBSITE                 |
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
        
        elif class_name == 'av-verse_text':
            text_div = section.find('div', class_='italic')
            if text_div:
                for br in text_div.find_all('br'):
                    br.replace_with('\n')
                return text_div.get_text(strip=False)

        elif class_name == 'av-synonyms':
            text_div = section.find('div', class_='text-justify')
            if text_div:
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
                return text

        elif class_name == 'av-translation':
            text_div = section.find('div', class_='s-justify')
            if text_div:
                return text_div.get_text(strip=True)
        
        return "Not found: 404"

    def _split_content(self, text: str, max_len: int = 1020) -> list:
        """Smart content splitting at natural breaks"""
        if len(text) <= max_len:
            return [text]
        
        chunks = []
        while text:
            split_pos = max(
                text.rfind('\n', 0, max_len),
                text.rfind(';', 0, max_len),
                text.rfind(' ', 0, max_len)
            )
            
            if split_pos <= 0:
                split_pos = max_len
            
            chunks.append(text[:split_pos].strip())
            text = text[split_pos:].strip()
        
        return chunks

    async def _add_field_safe(self, embed, name, value, inline=False):
        """Add field with automatic splitting if needed"""
        chunks = self._split_content(value)
        embed.add_field(name=name, value=chunks[0], inline=inline)
        for chunk in chunks[1:]:
            embed.add_field(name="↳ Continued", value=chunk, inline=inline)

async def setup(bot):
    await bot.add_cog(BhagavadGita(bot))
    
