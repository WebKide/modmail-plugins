import discord
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import re

class BhagavadGita(commands.Cog):
    """The Bhagavad Gītā as it is."""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_color = discord.Colour(0xed791d)  # Orange color
        self.base_url = "https://vedabase.io/en/library/bg"
        self.db = bot.plugin_db.get_partition(self)  # MongoDB partition for this cog

    async def _fetch_sloka_page(self, url):
        """Fetch the HTML content of a śloka page."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return None

    def _parse_sloka_data(self, html):
        """Parse the śloka data from the HTML content."""
        soup = BeautifulSoup(html, "html.parser")

        # Extract Devanagari text (Śloka)
        devanagari_div = soup.find("div", class_="av-devanagari")
        sloka_sanskrit = ""
        if devanagari_div:
            sloka_sanskrit = devanagari_div.find("div", class_="em:mb-4 em:leading-8 em:text-lg text-center").get_text(strip=True)

        # Extract Verse text (Transliteration)
        verse_text_div = soup.find("div", class_="av-verse_text")
        verse_english = ""
        if verse_text_div:
            verse_english = verse_text_div.find("div", class_="em:mb-4 em:leading-8 em:text-base text-center italic").get_text(strip=True)

        # Extract Synonyms
        synonyms_div = soup.find("div", class_="av-synonyms")
        synonyms = ""
        if synonyms_div:
            synonym_spans = synonyms_div.find_all("span", class_="inline")
            synonyms = "; ".join(span.get_text(strip=True) for span in synonym_spans)

        # Extract Translation
        translation_div = soup.find("div", class_="av-translation")
        translation_english = ""
        if translation_div:
            translation_english = translation_div.find("div", class_="em:mb-4 em:leading-8 em:text-base s-justify").get_text(strip=True)

        # Return parsed data as a dictionary
        return {
            "sloka_sanskrit": sloka_sanskrit,
            "verse_english": verse_english,
            "synonyms": synonyms,
            "translation_english": translation_english
        }

    async def _get_sloka_from_db(self, chapter, verse):
        """Retrieve a śloka from the MongoDB database."""
        query = {"chapter": chapter, "verse": verse}
        return await self.db.find_one(query)

    async def _save_sloka_to_db(self, chapter, verse, data, url):
        """Save a śloka to the MongoDB database."""
        document = {
            "chapter": chapter,
            "verse": verse,
            "data": data,
            "url": url,
            "last_accessed": datetime.utcnow()
        }
        await self.db.find_one_and_update(
            {"chapter": chapter, "verse": verse},
            {"$set": document},
            upsert=True
        )

    async def _search_sloka(self, chapter, verse):
        """Search for a śloka, either in the database or by scraping the webpage."""
        # Check if the śloka is already in the database
        cached_sloka = await self._get_sloka_from_db(chapter, verse)
        if cached_sloka:
            return cached_sloka["data"], cached_sloka["url"]

        # If not found, scrape the webpage
        url = f"{self.base_url}/{chapter}/{verse}/"
        html = await self._fetch_sloka_page(url)
        if html:
            parsed_data = self._parse_sloka_data(html)
            if parsed_data:
                await self._save_sloka_to_db(chapter, verse, parsed_data, url)
                return parsed_data, url

        return None, None

    @commands.command(name="bg")
    async def bg(self, ctx, chapter: int, verse: str):
        """Retrieve a śloka from the Bhagavad Gītā."""
        try:
            # Search for the śloka
            data, url = await self._search_sloka(chapter, verse)
            if data:
                # Create the embed
                e = discord.Embed(color=self.user_color)
                e.add_field(name="Bg:", value=f"{chapter}.{verse}", inline=True)
                e.add_field(name="Śloka:", value=data["sloka_sanskrit"], inline=True)
                e.add_field(name="Verse:", value=data["verse_english"], inline=True)
                e.add_field(name="Synonyms:", value=data["synonyms"], inline=True)
                e.add_field(name="Translation:", value=data["translation_english"], inline=True)
                e.set_footer(text="Use wisely")

                await ctx.send(embed=e)
            else:
                await ctx.send("No śloka found or there was an error in the process.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(BhagavadGita(bot))
    
