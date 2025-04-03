#  v0.02
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
from fake_useragent import UserAgent
from typing import Tuple, Union
from discord.ext import commands
from datetime import datetime
from .info_dict import BG_CHAPTER_INFO, CC_BOOK_INFO, SB_CANTO_INFO


class VedaBase(commands.Cog):
    """ Retrieve ślokas from Bhagavad Gītā, Caitanya-caritāmṛta and Śrīmad Bhāgavatam from Vedabase.io

    - Supports Devanāgarī, Sanskrit/Bengali, Synonyms and Translation
    - Supports multiple verses grouped together
    - Supports formatted word-for-word with bold-italics
    - Robust scraping for web-crawler function
    """
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://vedabase.io/en/library/"
        self.ua = UserAgent(use_cache_server=False)  # Disable caching self.ua = UserAgent()
        self.session = None
        self.last_request_time = 0
        self.request_delay = 5  # seconds between requests
        
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

    def get_chapter_title(self, scripture: str, chapter_ref: Union[int, str]) -> str:
        """Retrieve the formatted chapter title based on scripture type"""
        if scripture == 'bg':
            if chapter_ref not in BG_CHAPTER_INFO:
                return f"Number {chapter_ref}"
            return BG_CHAPTER_INFO[chapter_ref].get('chapter_title', f"Number {chapter_ref}")
        elif scripture == 'cc':
            book = str(chapter_ref).lower()
            return CC_BOOK_INFO.get(book, {}).get('title', f"Book {book}")
        elif scripture == 'sb':
            canto = str(chapter_ref)
            return f"Canto {canto} - {SB_CANTO_INFO.get(canto, {}).get('title', 'Unknown')}"
        return f"Number {chapter_ref}"

    # +------------------------------------------------------------+
    # |                     Common Helper Methods                   |
    # +------------------------------------------------------------+
    def _get_verse_section(self, soup, class_name):
        """Helper method to extract verse sections"""
        section = soup.find('div', class_=class_name)
        if not section:
            return "Not available"
        
        if class_name == 'av-devanagari':  # Devanāgarī for SB and BG
            text_div = section.find('div', class_='text-center')
            if text_div:
                for br in text_div.find_all('br'):
                    br.replace_with('\n')
                return text_div.get_text(strip=False)
        
        elif class_name == 'av-bengali':  # Bengali for CC
            text_div = section.find('div', class_='text-center')
            if text_div:
                for br in text_div.find_all('br'):
                    br.replace_with('\n')
                return text_div.get_text(strip=False)

        elif class_name == 'av-verse_text':
            verse_parts = []
            for italic_div in section.find_all('div', class_='italic'):
                for br in italic_div.find_all('br'):
                    br.replace_with('\n')
                verse_parts.append(italic_div.get_text(strip=False))
            return '\n'.join(verse_parts)

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
                    em.replace_with(f"_**{em.get_text(strip=True)}**_")
                
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
                parts = [f"{p};" for p in parts[:-1]] + [parts[-1]]
                return parts
        
        chunks = []
        while text:
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
        
        if isinstance(value, list):
            value = ' '.join(value)
        
        chunks = self._split_content(str(value))
        embed.add_field(name=name, value=chunks[0], inline=inline)
        for chunk in chunks[1:]:
            embed.add_field(name="↳", value=chunk, inline=inline)

    # +------------------------------------------------------------+
    # |                     Input Validation                        |
    # +------------------------------------------------------------+
    def validate_bg_input(self, chapter: int, verse_input: str):
        """Validate BG chapter and verse input"""
        if chapter not in BG_CHAPTER_INFO:
            return (False, f"Invalid chapter number. The Bhagavad Gītā has 18 chapters (requested {chapter}).")
        
        chapter_data = BG_CHAPTER_INFO[chapter]
        total_verses = chapter_data['total_verses']

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

    def validate_cc_input(self, book: str, chapter: int, verse_input: str):
        """Validate CC book, chapter and verse input"""
        book = book.lower()
        if book not in CC_BOOK_INFO and book not in {'1', '2', '3'}:
            return (False, "Invalid book. Use 'adi' or '1', 'madhya' or '2', 'antya' or '3'.")
        
        # Note: CC doesn't have predefined verse counts, so we'll just validate format
        if '-' in verse_input:
            try:
                start, end = sorted(map(int, verse_input.split('-')))
                if start < 1:
                    return (False, "Verse numbers must be positive.")
                return (True, f"{start}-{end}")
            except ValueError:
                return (False, "Invalid verse range format. Use for example '20-23' or a single verse like '21'.")
        
        try:
            verse_num = int(verse_input)
            if verse_num < 1:
                return (False, "Verse numbers must be positive.")
            return (True, str(verse_num))
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")

    def validate_sb_input(self, canto: str, chapter: int, verse_input: str):
        """Validate SB canto, chapter and verse input"""
        if canto not in SB_CANTO_INFO and not (canto.isdigit() and 1 <= int(canto) <= 12):
            return (False, "Invalid canto. Śrīmad Bhāgavatam has 12 cantos (1-12).")
        
        if '-' in verse_input:
            try:
                start, end = sorted(map(int, verse_input.split('-')))
                if start < 1:
                    return (False, "Verse numbers must be positive.")
                return (True, f"{start}-{end}")
            except ValueError:
                return (False, "Invalid verse range format. Use for example '20-23' or a single verse like '21'.")
        
        try:
            verse_num = int(verse_input)
            if verse_num < 1:
                return (False, "Verse numbers must be positive.")
            return (True, str(verse_num))
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")

    # +------------------------------------------------------------+
    # |                     Bhagavad Gītā Command                   |
    # +------------------------------------------------------------+
    @commands.command(aliases=['gita', 'bhagavad_gita', 'bhagavad-gita'], no_pm=True)
    async def bhagavadgita(self, ctx, chapter: int, verse: str):
        """Retrieve a Bhagavad Gītā śloka from Vedabase.io"""
        is_valid, validated_verse_or_error = self.validate_bg_input(chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        verse = validated_verse_or_error
        url = f"{self.base_url}bg/{chapter}/{verse}/"
        
        try:
            html = await self.scrape_with_retry(url)
            soup = BeautifulSoup(html, 'html.parser')
            chapter_title = self.get_chapter_title('bg', chapter)

            devanagari = self._get_verse_section(soup, 'av-devanagari')
            verse_text = self._get_verse_section(soup, 'av-verse_text')
            synonyms = self._get_verse_section(soup, 'av-synonyms')
            translation = self._get_verse_section(soup, 'av-translation')

            distance = self.bot or self.bot.message
            duration = f'Śloka retrieved in {distance.ws.latency * 1000:.2f} ms'
            
            embed = discord.Embed(
                colour=discord.Colour(0x50e3c2),
                url=url,
                description=f"**{chapter_title}**"
            )
            embed.set_footer(text=duration)
            embed.set_author(name=f"Bhagavad Gītā ⁿᵉʷ — Śloka [ {chapter}.{verse} ]", url=url, icon_url="https://imgur.com/Yx661rW.png")

            await self._add_field_safe(embed, "देवनागरी:", devanagari)
            await self._add_field_safe(embed, f"TEXT {verse}:", f"**```py\n{verse_text}\n```**")
            await self._add_field_safe(embed, "SYNONYMS:", synonyms)
            await self._add_field_safe(embed, "TRANSLATION:", f"> **{translation}**")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"🚫 Error retrieving verse: \n{str(e)}")
            if hasattr(self.bot, 'logger'):
                self.bot.logger.error(f"BG command failed: \n\n{e}", exc_info=True)

    # +------------------------------------------------------------+
    # |                 Caitanya-caritāmṛta Command                 |
    # +------------------------------------------------------------+
    @commands.command(aliases=['cc', 'caritamrta', 'caitanya-caritamrta'], no_pm=True)
    async def caitanyacaritamrta(self, ctx, book: str, chapter: int, verse: str):
        """Retrieve a Caitanya-caritāmṛta śloka from Vedabase.io"""
        is_valid, validated_verse_or_error = self.validate_cc_input(book, chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        # Normalize book name (convert '1' to 'adi', etc.)
        book = book.lower()
        if book in {'1', '2', '3'}:
            book = {v['num']: k for k, v in CC_BOOK_INFO.items() if 'num' in v}.get(int(book), book)
        
        verse = validated_verse_or_error
        url = f"{self.base_url}cc/{book}/{chapter}/{verse}/"
        
        try:
            html = await self.scrape_with_retry(url)
            soup = BeautifulSoup(html, 'html.parser')
            book_title = self.get_chapter_title('cc', book)

            bengali = self._get_verse_section(soup, 'av-bengali')
            verse_text = self._get_verse_section(soup, 'av-verse_text')
            synonyms = self._get_verse_section(soup, 'av-synonyms')
            translation = self._get_verse_section(soup, 'av-translation')

            distance = self.bot or self.bot.message
            duration = f'Śloka retrieved in {distance.ws.latency * 1000:.2f} ms'
            
            embed = discord.Embed(
                colour=discord.Colour(0x3b88c3),  # Different color for CC
                url=url,
                description=f"**{book_title} - Chapter {chapter}**"
            )
            embed.set_footer(text=duration)
            embed.set_author(name=f"Caitanya-caritāmṛta — Śloka [ {book}.{chapter}.{verse} ]", url=url, icon_url="https://imgur.com/Yx661rW.png")

            await self._add_field_safe(embed, "देवनागरी/বাংলা:", bengali)
            await self._add_field_safe(embed, f"TEXT {verse}:", f"**```py\n{verse_text}\n```**")
            await self._add_field_safe(embed, "SYNONYMS:", synonyms)
            await self._add_field_safe(embed, "TRANSLATION:", f"> **{translation}**")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"🚫 Error retrieving verse: \n{str(e)}")
            if hasattr(self.bot, 'logger'):
                self.bot.logger.error(f"CC command failed: \n\n{e}", exc_info=True)

    # +------------------------------------------------------------+
    # |                 Śrīmad Bhāgavatam Command                  |
    # +------------------------------------------------------------+
    @commands.command(aliases=['sb', 'bhagavatam', 'srimad-bhagavatam'], no_pm=True)
    async def srimadbhagavatam(self, ctx, canto: str, chapter: int, verse: str):
        """Retrieve a Śrīmad Bhāgavatam śloka from Vedabase.io"""
        is_valid, validated_verse_or_error = self.validate_sb_input(canto, chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        verse = validated_verse_or_error
        url = f"{self.base_url}sb/{canto}/{chapter}/{verse}/"
        
        try:
            html = await self.scrape_with_retry(url)
            soup = BeautifulSoup(html, 'html.parser')
            canto_title = self.get_chapter_title('sb', canto)

            devanagari = self._get_verse_section(soup, 'av-devanagari')
            verse_text = self._get_verse_section(soup, 'av-verse_text')
            synonyms = self._get_verse_section(soup, 'av-synonyms')
            translation = self._get_verse_section(soup, 'av-translation')

            distance = self.bot or self.bot.message
            duration = f'Śloka retrieved in {distance.ws.latency * 1000:.2f} ms'
            
            embed = discord.Embed(
                colour=discord.Colour(0x9b59b6),  # Different color for SB
                url=url,
                description=f"**{canto_title} - Chapter {chapter}**"
            )
            embed.set_footer(text=duration)
            embed.set_author(name=f"Śrīmad Bhāgavatam — Śloka [ {canto}.{chapter}.{verse} ]", url=url, icon_url="https://imgur.com/Yx661rW.png")

            await self._add_field_safe(embed, "देवनागरी:", devanagari)
            await self._add_field_safe(embed, f"TEXT {verse}:", f"**```py\n{verse_text}\n```**")
            await self._add_field_safe(embed, "SYNONYMS:", synonyms)
            await self._add_field_safe(embed, "TRANSLATION:", f"> **{translation}**")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"🚫 Error retrieving verse: \n{str(e)}")
            if hasattr(self.bot, 'logger'):
                self.bot.logger.error(f"SB command failed: \n\n{e}", exc_info=True)

    def cog_unload(self):
        if hasattr(self, 'ua'):
            self.ua = None  # Helps with garbage collection
        if self.session:
            self.bot.loop.create_task(self.session.close())

async def setup(bot):
    await bot.add_cog(VedaBase(bot))
