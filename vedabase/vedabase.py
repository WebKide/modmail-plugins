#  v0.03
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
from discord.ext import commands
from typing import Union

from .util.scrapers import VedabaseScraper
from .util.formatters import VedabaseFormatter  # Try relative import
from .util.validators import VedabaseValidator
from .util.info_dict import BG_CHAPTER_INFO, CC_BOOK_INFO, SB_CANTO_INFO

from discord import app_commands, ButtonStyle
from discord.ui import View, Button
from enum import Enum

class SearchType(Enum):
    EXACT_WORD = "exact-word"
    EXACT = "exact"
    CONTAINS = "contains"
    STARTS_WITH = "starts"


class VedaBase(commands.Cog):
    """Retrieve ślokas from Bhagavad Gītā, Caitanya-caritāmṛta and Śrīmad Bhāgavatam from Vedabase.io"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scraper = VedabaseScraper(bot)
        self.formatter = VedabaseFormatter()
        self.validator = VedabaseValidator(BG_CHAPTER_INFO, CC_BOOK_INFO, SB_CANTO_INFO)

    # +------------------------------------------------------------+
    # |                     Bhagavad Gītā Command                  |
    # +------------------------------------------------------------+
    @commands.command(aliases=['gita', 'bhagavad_gita', 'bhagavad-gita'], no_pm=True)
    async def bhagavadgita(self, ctx, chapter: int, verse: str):
        """Retrieve a Bhagavad Gītā śloka from Vedabase.io"""
        is_valid, validated_verse_or_error = self.validator.validate_bg_input(chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        try:
            embed = await self.scraper.get_bg_embed(chapter, validated_verse_or_error)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.handle_error(ctx, e, "BG")

    # +------------------------------------------------------------+
    # |                 Caitanya-caritāmṛta Command                |
    # +------------------------------------------------------------+
    @commands.command(aliases=['cc', 'caritamrta', 'caitanya-caritamrta'], no_pm=True)
    async def caitanyacaritamrta(self, ctx, book: str, chapter: int, verse: str):
        """Retrieve a Caitanya-caritāmṛta śloka from Vedabase.io"""
        is_valid, validated_verse_or_error = self.validator.validate_cc_input(book, chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        try:
            embed = await self.scraper.get_cc_embed(book, chapter, validated_verse_or_error)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.handle_error(ctx, e, "CC")

    # +------------------------------------------------------------+
    # |                 Śrīmad Bhāgavatam Command                  |
    # +------------------------------------------------------------+
    @commands.command(aliases=['sb', 'bhagavatam', 'srimad-bhagavatam'], no_pm=True)
    async def srimadbhagavatam(self, ctx, canto: str, chapter: int, verse: str):
        """Retrieve a Śrīmad Bhāgavatam śloka from Vedabase.io"""
        is_valid, validated_verse_or_error = self.validator.validate_sb_input(canto, chapter, verse)
        if not is_valid:
            return await ctx.send(validated_verse_or_error)
        
        try:
            embed = await self.scraper.get_sb_embed(canto, chapter, validated_verse_or_error)
            await ctx.send(embed=embed)
        except Exception as e:
            await self.handle_error(ctx, e, "SB")

    async def handle_error(self, ctx, error, scripture_type):
        """Centralized error handling"""
        await ctx.send(f"🚫 Error retrieving {scripture_type} verse: \n{str(error)}")
        if hasattr(self.bot, 'logger'):
            self.bot.logger.error(f"{scripture_type} command failed: \n\n{error}", exc_info=True)

    def cog_unload(self):
        """Cleanup resources when cog is unloaded"""
        self.scraper.close()

    # +------------------------------------------------------------+
    # |                 Vedabase Search Commands                   |
    # +------------------------------------------------------------+
    @commands.hybrid_group(name="search", description="Search Vedabase for words and synonyms")
    async def search_group(self, ctx):
        """Group command for Vedabase searches"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a search type: `exact-word`, `exact`, `contains`, or `starts-with`")

    @search_group.command(name="exact-word", description="Search for exact word matches")
    async def search_exact_word(self, ctx, word: str):
        """Search for exact word matches"""
        await self._perform_search(ctx, word, SearchType.EXACT_WORD)

    @search_group.command(name="exact", description="Search for exact matches")
    async def search_exact(self, ctx, word: str):
        """Search for exact matches"""
        await self._perform_search(ctx, word, SearchType.EXACT)

    @search_group.command(name="contains", description="Search for words containing the term")
    async def search_contains(self, ctx, word: str):
        """Search for words containing the term"""
        await self._perform_search(ctx, word, SearchType.CONTAINS)

    @search_group.command(name="starts-with", description="Search for words starting with the term")
    async def search_starts_with(self, ctx, word: str):
        """Search for words starting with the term"""
        await self._perform_search(ctx, word, SearchType.STARTS_WITH)

    async def _perform_search(self, ctx, word: str, search_type: SearchType):
        """Common method to handle all search types"""
        try:
            results = await self.scraper.search_synonyms(word, search_type.value)
            if not results:
                return await ctx.send("No results found for this search.")
            
            embed = self.formatter.format_search_results(word, results, search_type)
            
            # Create "View More" button
            view = View()
            vedabase_url = f"https://vedabase.io/en/search/synonyms/?original={word}&search={search_type.value}"
            view.add_item(Button(
                style=ButtonStyle.link,
                label="View Full Results on Vedabase",
                url=vedabase_url
            ))
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            await self.handle_error(ctx, e, "SEARCH")
            
async def setup(bot):
    await bot.add_cog(VedaBase(bot))
    
