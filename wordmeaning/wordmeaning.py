"""
MIT License
Copyright (c) 2020 WebKide [d.id @323578534763298816]
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

import asyncio
import random
import re
import textwrap
import traceback
from datetime import datetime as dt
from urllib.parse import quote

import discord
import requests
import wikipedia
from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss
from discord.ext import commands
from pytz import timezone as tz

_HEADERS = {
    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR '
                  '2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8; '
                  'InfoPath.3; .NET4.0C; .NET4.0E) chromeframe/8.0.552.224',
    'Accept-Language': 'en-us'
}

class WordMeaning(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ find definitions of English words """
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange
        # self.query_url = "https://en.oxforddictionaries.com/definition/"
        self.query_url = "https://www.oxfordlearnersdictionaries.com/definition/english/"
        self.sess = None

    async def cog_load(self):
        """Initialize session when cog loads"""
        import aiohttp
        self.session = aiohttp.ClientSession(headers=_HEADERS)

    async def cog_unload(self):
        """Clean up session when cog unloads"""
        if self.session:
            await self.session.close()

    # +------------------------------------------------------------+
    # |                   URBAN DICTIONARY                         |
    # +------------------------------------------------------------+
    @commands.command(aliases=['ud'])
    async def urban(self, ctx, *, search_terms: str = None):
        """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Urban Dictionary search with pagination

        Usage:
        {prefix}urban <query>
        {prefix}ud oof
        """
        if search_terms is None:
            return await ctx.send('What should I search for you?', delete_after=15)

        await ctx.channel.typing()

        # Split search terms and check for definition number
        terms = search_terms.split()
        definition_number = 0

        # Check if last term is a number (for direct definition access)
        if terms and terms[-1].isdigit():
            definition_number = int(terms[-1]) - 1
            terms = terms[:-1]

        search_query = "+".join(terms)
        url = "http://api.urbandictionary.com/v0/define?term=" + search_query

        if not terms:
            return await ctx.send('Please provide a search term along with a definition number', delete_after=15)

        search_query = '+'.join(terms)
        url = 'https://api.urbandictionary.com/v0/define?term=' + search_query

        try:
            # Fix: Use proper session handling
            session = self.session or self.bot.session
            async with session.get(url) as r:
                if r.status != 200:
                    return await ctx.send(f"Urban Dictionary API returned error {r.status}", delete_after=15)
                result = await r.json()
        except Exception as e:
            return await ctx.send(f"Error connecting to Urban Dictionary: {str(e)}", delete_after=15)

        if not result.get('list'):
            return await ctx.send(f"Didn't find anything for *{' '.join(terms)}*", delete_after=15)

        definitions = result['list']
        total_defs = len(definitions)

        # Clamp the definition number to valid range
        definition_number = max(0, min(definition_number, total_defs - 1))

        # Create paginated embed
        embed = self._create_urban_embed(terms, definitions, definition_number, total_defs)
        message = await ctx.send(embed=embed)

        # Add reactions if there are multiple definitions
        if total_defs > 1:
            try:
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")
            except discord.Forbidden:
                return  # Can't add reactions for navigation

            def check(reaction, user):
                return (
                    user == ctx.author
                    and reaction.message.id == message.id
                    and str(reaction.emoji) in ["⬅️", "➡️"]
                )

            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=360.0, check=check  # Reduce timeout
                    )

                    if str(reaction.emoji) == "➡️":
                        definition_number = (definition_number + 1) % total_defs
                    else:
                        definition_number = (definition_number - 1) % total_defs

                    embed = self._create_urban_embed(terms, definitions, definition_number, total_defs)
                    await message.edit(embed=embed)
                    try:
                        await message.remove_reaction(reaction, user)
                    except discord.Forbidden:
                        pass  # Can't remove reactions

                except asyncio.TimeoutError:
                    try:
                        await message.clear_reactions()
                    except discord.Forbidden:
                        pass  # Can't clear reactions

    # Enhanced embed creation with length checking
    def _create_urban_embed(self, terms, definitions, current_index, total):
        """Helper function to create Urban Dictionary embeds"""
        definition = definitions[current_index]
        term = " ".join(terms)

        embed = discord.Embed(
            title=f"{term} ({current_index + 1}/{total})",
            color=self.user_color,
            url=definition.get('permalink', 'https://www.urbandictionary.com/')
        )

        # Format definition and example with length limits
        def_text = definition['definition'].replace('[', '').replace(']', '')
        example_text = definition.get('example', '').replace('[', '').replace(']', '') if definition.get('example') else "No example provided"

        # Fix: Better length handling
        if len(def_text) > 2048:
            def_text = def_text[:2045] + "..."

        embed.description = def_text

        if len(example_text) > 1024:
            example_text = example_text[:1021] + "..."
        
        embed.add_field(name="Example", value=example_text, inline=False)

        # Handle missing vote counts
        thumbs_up = definition.get('thumbs_up', 0)
        thumbs_down = definition.get('thumbs_down', 0)
        embed.set_footer(text=f"👍 {thumbs_up} | 👎 {thumbs_down}")

        return embed

    # +------------------------------------------------------------+
    # |                          WIKIPEDIA                         |
    # +------------------------------------------------------------+
    @commands.command(aliases=['wikipedia'])
    async def wiki(self, ctx, *, search: str = None):
        """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Search Wikipedia with numbered disambiguation"""
        if not search:
            return await ctx.send(f"Usage: `{ctx.prefix}wiki <search term>`")

        try:
            await ctx.channel.typing()
            wikipedia.set_lang("en")

            # Try to get the page directly first
            try:
                page = wikipedia.page(search, auto_suggest=False)
                return await self.send_wiki_result(ctx, page)
            except wikipedia.DisambiguationError as e:
                # Handle disambiguation pages with numbered options
                options = e.options[:9]  # Limit to first 9 options
                if not options:
                    return await ctx.send("No results found. Try a different search term.", delete_after=15)

                # Create disambiguation embed
                embed = discord.Embed(
                    title=f"Disambiguation: {search}",
                    description="Please select an option by reacting with the corresponding number (1-9):",
                    color=self.user_color
                )

                # Add numbered options
                options_text = ''
                for i, option in enumerate(options, 1):
                    options_text += f'{i}. {option}\n'

                embed.add_field(name="Options", value=f"\u200b{options_text}", inline=False)

                if len(e.options) > 9:
                    embed.set_footer(text=f"Showing 1-9 of {len(e.options)} options | For more options, type the exact name")

                message = await ctx.send(embed=embed)

                # Fix: Better emoji handling with fallback
                number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
                
                try:
                    for i in range(len(options)):
                        await message.add_reaction(number_emojis[i])
                except discord.Forbidden:
                    return await ctx.send("I need permission to add reactions for disambiguation.", delete_after=15)

                # Wait for user reaction
                def check(reaction, user):
                    return (
                        user == ctx.author and
                        reaction.message.id == message.id and
                        str(reaction.emoji) in number_emojis[:len(options)]
                    )

                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=60.0, check=check
                    )

                    # Fix: Safer emoji to index conversion
                    try:
                        selected_index = number_emojis.index(str(reaction.emoji))
                        if selected_index >= len(options):
                            raise IndexError("Invalid selection")
                    except (ValueError, IndexError):
                        return await ctx.send("Invalid selection. Please try again.", delete_after=15)

                    selected_option = options[selected_index]

                    # Get the page for selected option
                    try:
                        selected_page = wikipedia.page(selected_option, auto_suggest=False)
                        await message.delete()
                        return await self.send_wiki_result(ctx, selected_page)
                    except wikipedia.PageError:
                        await ctx.send(f"Couldn't find a page for '{selected_option}'. Please try another option.", delete_after=15)
                    except wikipedia.DisambiguationError:
                        await ctx.send(f"'{selected_option}' is still ambiguous. Please try a more specific search.", delete_after=15)

                except asyncio.TimeoutError:
                    try:
                        await message.clear_reactions()
                    except discord.Forbidden:
                        pass
                    return

            except wikipedia.PageError:
                return await ctx.send("Couldn't find a specific page for that term. Try a different search.", delete_after=15)

        except Exception as e:
            await ctx.send(f"An error occurred while searching Wikipedia: {str(e)}", delete_after=15)

    async def send_wiki_result(self, ctx, page):
        """Helper function to send wiki results"""
        embed = discord.Embed(
            title=page.title,
            color=self.user_color,
            url=page.url,
            description=wikipedia.summary(page.title, sentences=3)
        )

        if page.images:
            embed.set_thumbnail(url=page.images[0])

        await ctx.send(embed=embed)

    # +------------------------------------------------------------+
    # |               Oxford English Dictionary                    |
    # +------------------------------------------------------------+
    @commands.group(name='dict', aliases=['oed'], invoke_without_command=True)
    async def dictionary(self, ctx, *, term: str = None):
        """Base dictionary command with subcommands"""
        if term is None or ctx.invoked_subcommand is not None:
            sample = random.choice(['lecture', 'fantasy', 'gathering', 'gradually', 'international', 'desire'])
            embed = discord.Embed(
                title="Dictionary Help",
                description=(
                    f"**Usage:** `{ctx.prefix}dict <word>`\n"
                    f"**Example:** `{ctx.prefix}dict {sample}`\n\n"
                    "**Subcommands:**\n"
                    f"`{ctx.prefix}dict examples <word>` - Show usage examples\n"
                    f"`{ctx.prefix}dict synonyms <word>` - Show synonyms\n"
                    f"`{ctx.prefix}dict proverbs <word>` - Show proverbs/idioms"
                ),
                color=self.user_color
            )
            return await ctx.send(embed=embed)

        await self._lookup_word(ctx, term)

    @dictionary.command(name='examples')
    async def dict_examples(self, ctx, *, term: str):
        """Show dictionary examples for a word"""
        await self._lookup_word(ctx, term, show_examples=True)

    @dictionary.command(name='synonyms')
    async def dict_synonyms(self, ctx, *, term: str):
        """Show synonyms for a word"""
        await self._lookup_word(ctx, term, show_synonyms=True)

    @dictionary.command(name='proverbs')
    async def dict_proverbs(self, ctx, *, term: str):
        """Show proverbs/idioms for a word"""
        await self._lookup_word(ctx, term, show_proverbs=True)

    # Improved Oxford dictionary lookup with async requests
    async def _lookup_word(self, ctx, term: str, show_examples=False, show_synonyms=False, show_proverbs=False):
        """Shared lookup function for all dictionary commands"""
        await ctx.channel.typing()

        # Convert spaces to hyphens for multi-word queries
        query = '-'.join(term.split())
        url = f"{self.query_url}{query.lower()}"

        try:
            # Fix: Use async session instead of blocking requests
            session = self.session or self.bot.session
            async with session.get(url, headers=_HEADERS) as response:
                if response.status == 404:
                    return await ctx.send(f"Couldn't find a definition for *{query.replace('-', ' ')}*. Please check the spelling.", delete_after=15)
                elif response.status != 200:
                    return await ctx.send(f"Dictionary service returned error {response.status}", delete_after=15)

                html_content = await response.text()

            soup = bs(html_content, 'html.parser')
            
            embed = discord.Embed(color=self.user_color)
            embed.set_author(
                name=f'Oxford Dictionary: {query.replace("-", " ").title()}',
                url=url,
                icon_url="https://www.oxfordlearnersdictionaries.com/favicon.ico"
            )

            # Get word type (noun, verb, etc.) - Fix: Better selector handling
            pos = soup.find('span', {'class': 'pos'}) or soup.find('span', class_='pos')
            if pos:
                embed.title = f"[{pos.text}] {query.replace('-', ' ').title()}"
            else:
                embed.title = query.replace('-', ' ').title()

            # Get pronunciation - Fix: Multiple selector attempts
            phonetics = (soup.find('span', {'class': 'phon'}) or 
                        soup.find('span', class_='phon') or
                        soup.find('div', class_='phonetics'))
            if phonetics:
                embed.add_field(name="Pronunciation", value=phonetics.text.strip(), inline=False)

            # Get definitions - Fix: Better error handling for missing content
            senses = soup.find_all('li', {'class': 'sense'}) or soup.find_all('div', class_='sense')
            if not senses:
                # Try alternative selectors
                senses = soup.find_all('div', class_='def-block') or soup.find_all('span', class_='def')
                
            if not senses:
                return await ctx.send(f"Found the word but couldn't extract definitions. Try visiting: {url}", delete_after=15)

            # Add first 3 definitions with better parsing
            definition_text = ""
            for i, sense in enumerate(senses[:3], 1):
                definition = (sense.find('span', {'class': 'def'}) or 
                             sense.find('span', class_='def') or
                             sense.find('div', class_='def'))
                if definition:
                    grammar = sense.find('span', {'class': 'grammar'})
                    grammar_text = f" {grammar.text}" if grammar else ""
                    def_clean = definition.text.strip()
                    definition_text += f"{i}.{grammar_text} {def_clean}\n\n"

            if definition_text:
                embed.description = definition_text.strip()[:2048]  # Respect embed limits
            else:
                return await ctx.send(f"Found the word but couldn't extract definitions. Try visiting: {url}", delete_after=15)

            # Examples (only if requested or in base command)
            if show_examples or (not any([show_examples, show_synonyms, show_proverbs])):
                examples = []
                for sense in senses[:2]:
                    sense_examples = (sense.find_all('span', {'class': 'x'}) or 
                                    sense.find_all('span', class_='x') or
                                    sense.find_all('div', class_='example'))
                    examples.extend([ex.text.strip() for ex in sense_examples[:2] if ex.text.strip()])

                if examples:
                    example_text = "\n".join([f"• {ex}" for ex in examples[:4]])
                    embed.add_field(name="Examples", value=example_text[:1024], inline=False)

            # Synonyms (only if requested)
            if show_synonyms:
                synonyms = (soup.find('div', {'class': 'synonyms'}) or 
                           soup.find('div', class_='synonyms') or
                           soup.find('span', class_='syn'))
                if synonyms:
                    syn_text = synonyms.text.strip()[:1024]
                    if syn_text:
                        embed.add_field(name="Synonyms", value=syn_text, inline=False)

            # Proverbs/Idioms (only if requested)
            if show_proverbs:
                idioms = soup.find('span', {'id': lambda x: x and x.endswith('idmgs_1')})
                if idioms:
                    idiom_spans = idioms.find_all('span', {'class': 'idm'})[:3]
                    if idiom_spans:
                        idiom_text = "\n".join([f"• {idm.text.strip()}" for idm in idiom_spans if idm.text.strip()])
                        if idiom_text:
                            embed.add_field(name="Idioms", value=idiom_text[:1024], inline=False)

            # Fix: Ensure embed has content before sending
            if not embed.description and not embed.fields:
                return await ctx.send(f"Found the word but couldn't extract any usable content. Try visiting: {url}", delete_after=15)

            await ctx.send(embed=embed)

        except asyncio.TimeoutError:
            await ctx.send(f"Request timed out while looking up '{query}'. Please try again.", delete_after=15)
        except Exception as e:
            await ctx.send(f"An error occurred while looking up '{query}': {str(e)}", delete_after=15)

    # +------------------------------------------------------------+
    # |              Rhyme Finder RhymeZone API                    |
    # +------------------------------------------------------------+
    @commands.command(aliases=['rhyme', 'rhymes'])
    async def rhymefinder(self, ctx, *, phrase: str = None):
        """Find rhymes for the last word in a phrase

        Usage:
        {prefix}rhyme <word or phrase>
        {prefix}rhymes beautiful day
        """
        if phrase is None:
            return await ctx.send('What word should I find rhymes for?', delete_after=15)

        await ctx.channel.typing()

        # Extract the last word from the phrase
        words = phrase.strip().split()
        target_word = words[-1].lower()

        # Clean the word (remove punctuation)
        target_word = re.sub(r'[^\w\s]', '', target_word)

        if not target_word:
            return await ctx.send('Please provide a valid word to find rhymes for.', delete_after=15)

        try:
            # Get rhymes from RhymeZone API
            rhymes = await self._get_rhymes(target_word)

            if not rhymes:
                # Try to get near rhymes if no perfect rhymes found
                rhymes = await self._get_near_rhymes(target_word)

            if not rhymes:
                return await ctx.send(f"Couldn't find any rhymes for '*{target_word}*'. Try a different word!", delete_after=15)

            # Create paginated rhyme display
            await self._display_rhymes(ctx, target_word, rhymes, phrase)

        except Exception as e:
            await ctx.send(f"An error occurred while finding rhymes: {str(e)}", delete_after=15)

    async def _get_rhymes(self, word: str):
        """Get perfect rhymes from RhymeZone API"""
        url = f"https://api.datamuse.com/words?rel_rhy={quote(word)}&max=100"

        try:
            session = self.session or self.bot.session
            async with session.get(url) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                # Extract just the words, sorted by frequency score
                rhymes = [item['word'] for item in data if 'word' in item]
                return rhymes[:75]  # Limit to 75 rhymes for pagination

        except Exception:
            return []

    async def _get_near_rhymes(self, word: str):
        """Get near rhymes (slant rhymes) if perfect rhymes not found"""
        url = f"https://api.datamuse.com/words?rel_nry={quote(word)}&max=50"

        try:
            session = self.session or self.bot.session
            async with session.get(url) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                # Extract just the words
                rhymes = [item['word'] for item in data if 'word' in item]
                return rhymes[:45]  # Fewer near rhymes

        except Exception:
            return []

    async def _display_rhymes(self, ctx, target_word: str, rhymes: list, original_phrase: str):
        """Display rhymes with pagination"""
        total_rhymes = len(rhymes)
        rhymes_per_page = 15
        current_page = 0
        total_pages = (total_rhymes + rhymes_per_page - 1) // rhymes_per_page

        def create_rhyme_embed(page_num):
            start_idx = page_num * rhymes_per_page
            end_idx = min(start_idx + rhymes_per_page, total_rhymes)
            page_rhymes = rhymes[start_idx:end_idx]

            embed = discord.Embed(
                title=f"🎵 Rhymes for '{target_word}'",
                color=self.user_color
            )

            if len(original_phrase.split()) > 1:
                embed.description = f"*From phrase: \"{original_phrase}\"*\n\n"
            else:
                embed.description = ""

            # Format rhymes in columns for better display
            rhyme_text = ""
            for i, rhyme in enumerate(page_rhymes):
                rhyme_text += f"• {rhyme.capitalize()}"
                # Add newline every 3 items for better formatting
                if (i + 1) % 3 == 0:
                    rhyme_text += "\n"
                else:
                    rhyme_text += "   "

            embed.add_field(
                name=f"Rhymes ({start_idx + 1}-{end_idx} of {total_rhymes})",
                value=rhyme_text.strip() or "No rhymes on this page",
                inline=False
            )

            # Add rhyme type indicator
            if start_idx == 0:
                rhyme_type = "Perfect Rhymes" if total_rhymes > 20 else "Near Rhymes"
                embed.set_footer(text=f"Type: {rhyme_type} | Page {page_num + 1}/{total_pages}")
            else:
                embed.set_footer(text=f"Page {page_num + 1}/{total_pages}")

            return embed

        # Send initial embed
        embed = create_rhyme_embed(current_page)
        message = await ctx.send(embed=embed)

        # Add navigation if multiple pages
        if total_pages > 1:
            try:
                await message.add_reaction("➡️")
                if total_pages > 2:  # Add left arrow if more than 2 pages
                    await message.add_reaction("⬅️")
            except discord.Forbidden:
                return  # Can't add reactions

            def check(reaction, user):
                return (
                    user == ctx.author and
                    reaction.message.id == message.id and
                    str(reaction.emoji) in ["⬅️", "➡️"]
                )

            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=300.0, check=check
                    )

                    if str(reaction.emoji) == "➡️":
                        current_page = (current_page + 1) % total_pages
                    elif str(reaction.emoji) == "⬅️":
                        current_page = (current_page - 1) % total_pages

                    embed = create_rhyme_embed(current_page)
                    await message.edit(embed=embed)

                    try:
                        await message.remove_reaction(reaction, user)
                    except discord.Forbidden:
                        pass

                except asyncio.TimeoutError:
                    try:
                        await message.clear_reactions()
                    except discord.Forbidden:
                        pass
                    break

    # Add this helper method for better rhyme quality assessment
    def _score_rhyme_quality(self, word1: str, word2: str):
        """Simple rhyme quality scorer based on suffix matching"""
        word1, word2 = word1.lower(), word2.lower()

        # Find longest common suffix
        min_len = min(len(word1), len(word2))
        common_suffix = 0

        for i in range(1, min_len + 1):
            if word1[-i] == word2[-i]:
                common_suffix = i
            else:
                break

        # Score based on suffix length and word length ratio
        score = common_suffix / max(len(word1), len(word2))
        return score

    # Enhanced version of _get_rhymes with quality filtering
    async def _get_rhymes_enhanced(self, word: str):
        """Get rhymes with quality filtering"""
        # First try perfect rhymes
        url = f"https://api.datamuse.com/words?rel_rhy={quote(word)}&max=100"

        try:
            session = self.session or self.bot.session
            async with session.get(url) as response:
                if response.status != 200:
                    return []

                data = await response.json()

                # Filter and sort rhymes by quality
                rhymes = []
                for item in data:
                    if 'word' in item:
                        rhyme_word = item['word']
                        # Skip if same word or too similar
                        if rhyme_word.lower() != word.lower():
                            quality = self._score_rhyme_quality(word, rhyme_word)
                            rhymes.append((rhyme_word, quality))

                # Sort by quality score (descending) and take top results
                rhymes.sort(key=lambda x: x[1], reverse=True)
                return [rhyme[0] for rhyme in rhymes[:75]]

        except Exception:
            return []

async def setup(bot):
    await bot.add_cog(WordMeaning(bot))
