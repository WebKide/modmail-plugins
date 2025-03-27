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

from bs4 import BeautifulSoup
from datetime import datetime
from discord.ext import commands
from typing import Optional, Union, Tuple

class BhagavadGita(commands.Cog):
    """Discord.py plugin for retrieving Bhagavad Gītā ślokas"""
    
    BG_CHAPTER_INFO = {
        1: {
            'total_verses': 46,
            'grouped_ranges': [(16, 18), (21, 22), (32, 35), (37, 38)]
        },
        2: {
            'total_verses': 72,
            'grouped_ranges': [(42, 43)]
        },
        3: {
            'total_verses': 43,
            'grouped_ranges': []  # Single verses
        },
        4: {
            'total_verses': 42,
            'grouped_ranges': []  # Single verses
        },
        5: {
            'total_verses': 29,
            'grouped_ranges': [(8, 9), (27, 28)]
        },
        6: {
            'total_verses': 47,
            'grouped_ranges': [(11, 12), (13, 14), (20, 23)]
        },
        7: {
            'total_verses': 30,
            'grouped_ranges': []  # Single verses
        },
        8: {
            'total_verses': 28,
            'grouped_ranges': []  # Single verses
        },
        9: {
            'total_verses': 34,
            'grouped_ranges': []  # Single verses
        },
        10: {
            'total_verses': 42,
            'grouped_ranges': [(4, 5), (12, 13)]
        },
        11: {
            'total_verses': 55,
            'grouped_ranges': [(10, 11), (26, 27), (41, 42)]
        },
        12: {
            'total_verses': 20,
            'grouped_ranges': [(3, 4), (6, 7), (13, 14), (18, 19)]
        },
        13: {
            'total_verses': 35,
            'grouped_ranges': [(1, 2), (6, 7), (8, 12)]
        },
        14: {
            'total_verses': 27,
            'grouped_ranges': [(22, 25)]
        },
        15: {
            'total_verses': 20,
            'grouped_ranges': [(3, 4)]
        },
        16: {
            'total_verses': 24,
            'grouped_ranges': [(1, 3), (11, 12), (13, 15)]
        },
        17: {
            'total_verses': 28,
            'grouped_ranges': [(7, 9), (14, 16), (23, 24)]
        },
        18: {
            'total_verses': 78,
            'grouped_ranges': [(5, 6), (26, 27)]
        }
    }

    def __init__(self, bot):
        self.bot = bot
        self.user_color = discord.Colour(0xed791d)
        self.base_url = "https://vedabase.io/en/library/bg"
        self.db = bot.plugin_db.get_partition(self)
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    @commands.command(name="bg")
    async def bg(self, ctx, chapter: int, verse: str):
        """Retrieve a śloka from the Bhagavad Gītā"""
        # 1. Input Validation
        is_valid, result = self.validate_verse_input(chapter, verse)
        if not is_valid:
            return await ctx.send(result, delete_after=10)
        
        valid_chapter, verse_str = result
        
        # 2. Cache Check
        cached = await self.check_cached_verse(valid_chapter, verse_str)
        if cached:
            return await self.send_sloka_embed(ctx, cached, verse)
        
        # 3. Web Scraping
        verse_data = await self.scrape_verse_data(valid_chapter, verse_str)
        if not verse_data:
            return await ctx.send("Failed to retrieve verse data. Please try again later.", delete_after=10)
        
        # 4. Cache Update
        await self.save_to_cache(verse_data)
        
        # 5. Send Response
        await self.send_sloka_embed(ctx, verse_data, verse)

    def validate_verse_input(self, chapter: int, verse_input: str) -> Tuple[bool, Union[str, Tuple[int, str]]]:
        """Validate chapter and verse input"""
        if chapter not in self.BG_CHAPTER_INFO:
            return (False, f"Invalid chapter. Bhagavad Gītā has 18 chapters (requested {chapter})")
        
        chapter_data = self.BG_CHAPTER_INFO[chapter]
        total_verses = chapter_data['total_verses']
        
        # Handle verse ranges
        if '-' in verse_input:
            try:
                start, end = sorted(map(int, verse_input.split('-')))
            except ValueError:
                return (False, "Invalid verse range format. Use '20-23' or single verse '21'")
            
            if end > total_verses:
                return (False, f"Chapter {chapter} has only {total_verses} verses")
            
            # Check grouped ranges
            for r_start, r_end in chapter_data['grouped_ranges']:
                if start >= r_start and end <= r_end:
                    return (True, (chapter, f"{r_start}-{r_end}"))
                if not (end < r_start or start > r_end):
                    return (False, f"Verses {start}-{end} overlap with grouped range {r_start}-{r_end}")
            
            return (True, (chapter, f"{start}-{end}"))
        
        # Handle single verse
        try:
            verse = int(verse_input)
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")
        
        if verse > total_verses:
            return (False, f"Chapter {chapter} has only {total_verses} verses")
        
        # Check if part of grouped range
        for r_start, r_end in chapter_data['grouped_ranges']:
            if r_start <= verse <= r_end:
                return (True, (chapter, f"{r_start}-{r_end}"))
        
        return (True, (chapter, str(verse)))

    async def check_cached_verse(self, chapter: int, verse_str: str) -> Optional[dict]:
        """Check cache with proper error handling"""
        try:
            cached_doc = await self.db.find_one({
                "chapter": chapter,
                "verse_range": verse_str
            })
            
            if cached_doc:
                await self.db.update_one(
                    {"_id": cached_doc["_id"]},
                    {"$set": {"last_accessed": datetime.utcnow()}}
                )
                return cached_doc
        except Exception as e:
            print(f"Cache check error: {e}")
        return None

    async def scrape_verse_data(self, chapter: int, verse_str: str) -> Optional[dict]:
        """Improved scraping with better error handling"""
        url = f"{self.base_url}/{chapter}/{verse_str}/"
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
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
                
                for container in soup.find_all(class_="r-verse"):
                    verse_num = container.find(class_="r-verse__num").get_text(strip=True)
                    
                    verse_data["verses"][verse_num] = {
                        "devanagari": self._get_text(container, "av-devanagari"),
                        "transliteration": self._get_text(container, "av-verse_text"),
                        "synonyms": self._get_text(container, "av-synonyms", "; "),
                        "translation": self._get_text(container, "av-translation")
                    }
                
                return verse_data
        except Exception as e:
            print(f"Scraping error: {e}")
            return None

    async def save_to_cache(self, verse_data: dict) -> bool:
        """Save verse data to cache"""
        try:
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
            print(f"Error saving to cache: {str(e)}")
            return False

    async def send_sloka_embed(self, ctx, verse_data: dict, requested_verse: str):
        """Send verse embed to Discord"""

    def _get_text(self, container, class_name: str, separator: str = " ") -> str:
        """Helper method to safely extract text"""
        element = container.find(class_=class_name)
        return element.get_text(separator, strip=True) if element else "Not available"

    def _truncate_text(self, text: str, max_len: int) -> str:
        """Helper method to truncate long text"""
        return text if len(text) <= max_len else f"{text[:max_len-3]}..."

    async def send_sloka_embed(self, ctx, verse_data: dict, requested_verse: str):
        """Improved embed generation with pagination support"""
        chapter = verse_data["chapter"]
        
        if '-' not in requested_verse:  # Single verse
            verse = verse_data["verses"].get(requested_verse)
            if not verse:
                return await ctx.send("Verse not found in cached data", delete_after=10)
            
            embed = discord.Embed(
                title=f"Bhagavad Gītā {chapter}.{requested_verse}",
                url=verse_data["url"],
                color=self.user_color
            )
            
            for name, value in [
                ("Devanagari", verse["devanagari"]),
                ("Transliteration", verse["transliteration"]),
                ("Synonyms", self._truncate_text(verse["synonyms"], 1000)),
                ("Translation", verse["translation"])
            ]:
                embed.add_field(name=name, value=value, inline=False)
            
            await ctx.send(embed=embed)
        else:  # Verse range
            start, end = map(int, verse_data["verse_range"].split('-'))
            verses = [v for v in range(start, end+1) if str(v) in verse_data["verses"]]
            
            if not verses:
                return await ctx.send("No verses found in this range", delete_after=10)
            
            # Split into multiple embeds if too many verses
            for i in range(0, len(verses), 5):  # 5 verses per embed
                embed = discord.Embed(
                    title=f"Bhagavad Gītā {chapter}.{verse_data['verse_range']} (Part {i//5+1})",
                    url=verse_data["url"],
                    color=self.user_color
                )
                
                for v in verses[i:i+5]:
                    verse = verse_data["verses"][str(v)]
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

async def setup(bot):
    await bot.add_cog(BhagavadGita(bot))
