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
import asyncio

from bs4 import BeautifulSoup
from datetime import datetime
from discord.ext import commands
from typing import Optional, Union, Tuple, Dict, Any

class BhagavadGita(commands.Cog):
    """Discord.py plugin for retrieving Bhagavad Gītā ślokas"""
    
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

    def __init__(self, bot):
        self.bot = bot
        self.user_color = discord.Colour(0xed791d)
        self.base_url = "https://vedabase.io/en/library/bg"
        self.db = bot.plugin_db.get_partition(self)
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())



    @commands.command(name="bg")
    async def bg(self, ctx, chapter: int, verse: str):
        """Retrieve a śloka from the Bhagavad Gītā
        
        Pipeline Flow:
        1. Validation → 2. Database Check → 3. Website Scraping → 
        4. Caching into Database → 5. Response in Embed
        """
        # 1. VALIDATION
        is_valid, result = self.validate_verse_input(chapter, verse)
        await ctx.send(f"1 {chapter} {verse}")  # Step-by-step
        if not is_valid:
            return await ctx.send(result, delete_after=10)
        
        valid_chapter, verse_str = result
        await ctx.send(f"2 {result}")  # Step-by-step
        
        # 2. DATABASE CHECK
        cached_data = await self.get_cached_verse(valid_chapter, verse_str)
        if cached_data:
            await ctx.send(f"3 {valid_chapter} {verse_str}")  # Step-by-step
            return await self.send_sloka_embed(ctx, cached_data, verse)
        
        # 3. WEBSITE SCRAPING
        scraped_data = await self.scrape_verse_data(valid_chapter, verse_str)
        if scraped_data is None:
            await ctx.send(f"4 {valid_chapter} {verse_str}")  # Step-by-step
            return await ctx.send(f"Verse {valid_chapter}.{verse_str} not found or an error occurred while fetching.", delete_after=10)

        # 4. CACHING INTO DATABASE
        await ctx.send("4 caching...")  # Step-by-step
        await self.cache_verse_data(scraped_data)
        
        # 5. RESPONSE IN EMBED
        await ctx.send("5 embed...")  # Step-by-step
        await self.send_sloka_embed(ctx, scraped_data, verse)

    async def get_cached_verse(self, chapter: int, verse_str: str) -> Optional[Dict[str, Any]]:
        """Check database for cached verse with proper error handling and streamlined grouped range search"""
        try:
            # Try exact match first
            await ctx.send("6")  # Step-by-step
            cached_doc = await self.db.find_one({
                "chapter": chapter,
                "verse_range": verse_str
            })
            
            if cached_doc:
                await ctx.send("7")  # Step-by-step
                # Update last accessed time
                await self.db.update_one(
                    {"_id": cached_doc["_id"]},
                    {"$set": {"last_accessed": datetime.utcnow()}}
                )
                return cached_doc
            
            # If the request is for a single verse, check if it's part of a grouped range
            if '-' not in verse_str:
                verse_num = int(verse_str)
                await ctx.send(f"8 {verse_num}")  # Step-by-step
                # Query only for documents with a grouped range (i.e. verse_range contains a hyphen)
                async for doc in self.db.find({
                    "chapter": chapter,
                    "verse_range": {"$regex": "-"}
                }):
                    start, end = map(int, doc["verse_range"].split('-'))
                    if start <= verse_num <= end and str(verse_num) in doc.get("verses", {}):
                        # Update last accessed time for the grouped range
                        await self.db.update_one(
                            {"_id": doc["_id"]},
                            {"$set": {"last_accessed": datetime.utcnow()}}
                        )
                        return doc
        except Exception as e:
            print(f"Database error in get_cached_verse: {e}")
        
        return None


    async def cache_verse_data(self, verse_data: Dict[str, Any]) -> bool:
        """Cache verse data in database with proper error handling"""
        try:
            await ctx.send("9")  # Step-by-step
            await self.db.replace_one(
                {
                    "chapter": verse_data["chapter"],
                    "verse_range": verse_data["verse_range"]
                },
                verse_data,
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Database error in cache_verse_data: {e}")
            return False

    def validate_verse_input(self, chapter: int, verse_input: str) -> Tuple[bool, Union[str, Tuple[int, str]]]:
        """Validate chapter and verse input"""
        if chapter not in self.BG_CHAPTER_INFO:
            await ctx.send("10")  # Step-by-step
            return (False, f"Invalid chapter. Bhagavad Gītā has 18 chapters (requested {chapter})")
        
        chapter_data = self.BG_CHAPTER_INFO[chapter]
        total_verses = chapter_data['total_verses']
        
        if '-' in verse_input:
            try:
                start, end = sorted(map(int, verse_input.split('-')))
                if end > total_verses:
                    return (False, f"Chapter {chapter} has only {total_verses} verses")
                
                for r_start, r_end in chapter_data['grouped_ranges']:
                    if start >= r_start and end <= r_end:
                        return (True, (chapter, f"{r_start}-{r_end}"))  # Valid grouped request

                    if (start <= r_end and end >= r_start):  # Partial overlap detected
                        return (False, f"Requested verses {start}-{end} overlap with predefined grouped range {r_start}-{r_end}")
                
                return (True, (chapter, f"{start}-{end}"))
            
            except ValueError:
                return (False, "Invalid verse range format. Use '20-23' or single verse '21'")
        
        try:
            verse = int(verse_input)
            if verse > total_verses:
                return (False, f"Chapter {chapter} has only {total_verses} verses")
            
            for r_start, r_end in chapter_data['grouped_ranges']:
                if r_start <= verse <= r_end:
                    return (True, (chapter, f"{r_start}-{r_end}"))
            
            return (True, (chapter, str(verse)))
        
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")

    async def scrape_verse_data(self, chapter: int, verse_str: str) -> Optional[Dict[str, Any]]:
        """Scrape verse data from website with proper error handling"""
        url = f"{self.base_url}/{chapter}/{verse_str}/"
        try:
            async with self.session.get(url) as response:
                if response.status == 404:
                    print(f"Verse {chapter}.{verse_str} not found on Vedabase. (HTTP 404)")
                    return None
                if response.status != 200:
                    print(f"Error {response.status}: Failed to retrieve data from {url}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                verse_data = {
                    "chapter": chapter,
                    "verse_range": verse_str,
                    "verses": {},
                    "url": url,
                    "created_at": datetime.utcnow(),
                    "last_accessed": datetime.utcnow()
                }

                # Extract verse number from H1 heading
                h1 = soup.find('h1', {'class': 'text-center'})
                if h1:
                    verse_num = h1.text.strip().split('.')[-1].strip()
                else:
                    verse_num = verse_str.split('-')[0]  # Fallback to input

                # Devanagari text
                devanagari_div = soup.find('div', class_='av-devanagari')
                devanagari = devanagari_div.find('div', class_='text-center').get_text('\n', strip=True) if devanagari_div else "Not available"

                # Transliteration text
                verse_text_div = soup.find('div', class_='av-verse_text')
                transliteration = verse_text_div.find('div', class_='italic').get_text('\n', strip=True) if verse_text_div else "Not available"

                # Synonyms text
                synonyms_div = soup.find('div', class_='av-synonyms')
                synonyms = synonyms_div.find('div', class_='text-justify').get_text(' ', strip=True) if synonyms_div else "Not available"

                # Translation text
                translation_div = soup.find('div', class_='av-translation')
                translation = translation_div.find('div', class_='s-justify').get_text(strip=True) if translation_div else "Not available"

                verse_data["verses"][verse_num] = {
                    "devanagari": devanagari,
                    "transliteration": transliteration,
                    "synonyms": synonyms,
                    "translation": translation
                }

                return verse_data
        except Exception as e:
            print(f"Scraping error in scrape_verse_data: {e}")
            return None


    def _get_text(self, container, class_name: str, separator: str = " ") -> str:
        """Helper method to extract text from BeautifulSoup container"""
        element = container.find(class_=class_name)
        return element.get_text(separator, strip=True) if element else "Not available"

    async def send_sloka_embed(self, ctx, verse_data: Dict[str, Any], requested_verse: str):
        """Send verse data as Discord embed with proper fallbacks"""
        chapter = verse_data["chapter"]
        verse_str = verse_data["verse_range"]
        
        if '-' not in requested_verse:
            verse_num = requested_verse
            verse = verse_data["verses"].get(verse_num)
            
            # Try different formats if not found
            if not verse:
                verse = verse_data["verses"].get(str(int(verse_num)))  # Try as integer string
            
            if not verse and '-' in verse_str:
                # Check if it's part of a grouped range
                start, end = map(int, verse_str.split('-'))
                if start <= int(verse_num) <= end:
                    verse = verse_data["verses"].get(verse_num)
            
            if not verse:
                return await ctx.send("Verse not found in the retrieved data", delete_after=10)
            
            embed = discord.Embed(
                title=f"Bhagavad Gītā {chapter}.{verse_num}",
                url=verse_data["url"],
                color=self.user_color
            )
            
            fields = [
                ("Devanagari", verse["devanagari"]),
                ("Transliteration", verse["transliteration"]),
                ("Synonyms", self._truncate_text(verse["synonyms"], 1000)),
                ("Translation", verse["translation"])
            ]
            
            for name, value in fields:
                if value and value != "Not available":
                    embed.add_field(name=name, value=value, inline=False)
            
            await ctx.send(embed=embed)
        else:
            start, end = map(int, verse_str.split('-')) if '-' in verse_str else (int(verse_str), int(verse_str))
            verses = [str(v) for v in range(start, end + 1) if str(v) in verse_data["verses"]]
            
            if not verses:
                available_verses = list(verse_data["verses"].keys())
                return await ctx.send(
                    f"Requested verses not found. Available verses in this section: {', '.join(available_verses)}", 
                    delete_after=10
                )
            
            for i in range(0, len(verses), 5):
                embed = discord.Embed(
                    title=f"Bhagavad Gītā {chapter}.{verse_str} (Part {i//5 + 1})",
                    url=verse_data["url"],
                    color=self.user_color
                )
                
                for v in verses[i:i+5]:
                    verse = verse_data["verses"][v]
                    embed.add_field(
                        name=f"Verse {v}",
                        value=(
                            f"**Devanagari:** {verse['devanagari']}\n"
                            f"**Transliteration:** {verse['transliteration']}\n"
                            f"**Translation:** {self._truncate_text(verse['translation'], 200)}"
                        ),
                        inline=False
                    )
                
                await ctx.send(embed=embed)


    def _truncate_text(self, text: str, max_len: int) -> str:
        """Helper method to truncate long text"""
        return (text[:max_len] + "...") if len(text) > max_len else text

async def setup(bot):
    await bot.add_cog(BhagavadGita(bot))
