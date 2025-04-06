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

import discord
import asyncio
import random
import textwrap
import traceback
import requests
import wikipedia
from discord.ext import commands
from bs4 import BeautifulSoup as bs, SoupStrainer as ss
from datetime import datetime as dt
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
        self.query_url = "https://en.oxforddictionaries.com/definition/"
        self.sess = requests.Session()

    # +------------------------------------------------------------+
    # |                       URBAN                                |
    # +------------------------------------------------------------+
    @commands.command(aliases=['ud'])
    async def urban(self, ctx, *, search_terms: str = None):
        """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Urban Dictionary search with pagination
        
        Usage:
        {prefix}urban <query>
        {prefix}ud oof
        """
        if search_terms is None:
            return await ctx.send('What should I search for you?')

        await ctx.channel.typing()
        
        # Split search terms and check for definition number
        terms = search_terms.split()
        definition_number = 0
        
        # Check if last term is a number (for direct definition access)
        if terms[-1].isdigit():
            definition_number = int(terms[-1]) - 1
            terms = terms[:-1]
        
        search_query = "+".join(terms)
        url = "http://api.urbandictionary.com/v0/define?term=" + search_query
        
        async with self.bot.session.get(url) as r:
            result = await r.json()
        
        if not result.get('list'):
            return await ctx.send(f"Didn't find anything for *{' '.join(terms)}*")
        
        definitions = result['list']
        total_defs = len(definitions)
        
        # Clamp the definition number to valid range
        definition_number = max(0, min(definition_number, total_defs - 1))
        
        # Create paginated embed
        embed = self._create_urban_embed(terms, definitions, definition_number, total_defs)
        message = await ctx.send(embed=embed)
        
        # Add reactions if there are multiple definitions
        if total_defs > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            
            def check(reaction, user):
                return (
                    user == ctx.author
                    and reaction.message.id == message.id
                    and str(reaction.emoji) in ["⬅️", "➡️"]
                )
            
            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=60.0, check=check
                    )
                    
                    if str(reaction.emoji) == "➡️":
                        definition_number = (definition_number + 1) % total_defs
                    else:
                        definition_number = (definition_number - 1) % total_defs
                    
                    embed = self._create_urban_embed(terms, definitions, definition_number, total_defs)
                    await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)
                    
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    break

    def _create_urban_embed(self, terms, definitions, current_index, total):
        """Helper function to create Urban Dictionary embeds"""
        definition = definitions[current_index]
        term = " ".join(terms)
        
        embed = discord.Embed(
            title=f"{term} ({current_index + 1}/{total})",
            color=self.user_color,
            url=definition.get('permalink', 'https://www.urbandictionary.com/')
        )
        
        # Format definition and example
        def_text = definition['definition'].replace('[', '').replace(']', '')
        example_text = definition['example'].replace('[', '').replace(']', '') if definition['example'] else "No example provided"
        
        embed.description = def_text[:2048]  # Limit to embed description max length
        embed.add_field(name="Example", value=example_text[:1024], inline=False)
        
        embed.set_footer(text=f"👍 {definition['thumbs_up']} | 👎 {definition['thumbs_down']}")
        return embed

    # +------------------------------------------------------------+
    # |                          WIKIPEDIA                         |
    # +------------------------------------------------------------+
    @commands.command(aliases=['wikipedia'])
    async def wiki(self, ctx, *, search: str = None):
        """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Wikipedia search command
        
        Usage:
        {prefix}wikipedia <term>
        {prefix}wiki origami
        """
        if search is None:
            return await ctx.send(f'Usage: `{ctx.prefix}wiki [search terms]`', delete_after=23)

        try:
            # Set language to English and disable suggestion redirects
            wikipedia.set_lang("en")
            
            # Search for the term
            results = wikipedia.search(search)
            if not results:
                return await ctx.send("Sorry, didn't find any result.", delete_after=23)
            
            # Get the page for the first result
            try:
                page = wikipedia.page(results[0], auto_suggest=False)
            except wikipedia.DisambiguationError as e:
                options = "\n".join(e.options[:5])  # Show first 5 options
                return await ctx.send(
                    f"**Disambiguation Error:** This term may refer to:\n\n{options}\n\n"
                    f"Please be more specific with your search."
                )
            
            # Create embed
            embed = discord.Embed(
                title=page.title,
                color=self.user_color,
                url=page.url,
                description=wikipedia.summary(search, sentences=2)
            )
            
            if page.images:
                embed.set_thumbnail(url=page.images[0])
            
            await ctx.send(embed=embed)
            
        except wikipedia.PageError:
            await ctx.send("Sorry, I couldn't find a page for that term.", delete_after=23)
        except Exception as e:
            tb = traceback.format_exc()
            await ctx.send(f'```css\n[WIKI ERROR]\n{e}```\n```py\n{tb[:1000]}```')

    # +------------------------------------------------------------+
    # |               Oxford English Dictionary                    |
    # +------------------------------------------------------------+
    @commands.command(name='dict', description='Oxford English Dictionary', aliases=['oed'])
    async def _dict(self, ctx, *, term: str = None):
        """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Search definitions in English using Oxford Learner's Dictionaries"""
        if term is None:
            sample = random.choice(['lecture', 'fantasy', 'gathering', 'gradually', 'international', 'desire'])
            return await ctx.send(
                f"**Usage:** `{ctx.prefix}dict <word>`\n"
                f"**Example:** `{ctx.prefix}dict {sample}`\n"
                f"Add `examples`, `synonyms`, or `proverbs` for more details"
            )

        await ctx.channel.typing()
        query = term.split(' ')[0].lower()
        base_url = "https://www.oxfordlearnersdictionaries.com/definition/english/"
        
        # Track current entry number for pagination
        current_entry = 0
        max_entries_to_check = 3  # Check up to _1, _2, _3
        
        # Store all found entries and their data
        entries = []
        
        # First try the base URL (without _1, _2, etc.)
        initial_url = f"{base_url}{query}"
        initial_page = requests.get(initial_url, headers=_HEADERS)
        
        # Check if we got redirected to a numbered entry (like love_1)
        if initial_page.history and '_' in initial_page.url.split('/')[-1]:
            final_url = initial_page.url
            word_id = final_page.url.split('/')[-1]
            base_query = word_id.split('_')[0]
            entry_num = int(word_id.split('_')[1]) if '_' in word_id else 0
            entries.append({'url': final_url, 'num': entry_num, 'query': base_query})
        elif initial_page.status_code == 200:
            # Base URL worked, treat as entry 0
            entries.append({'url': initial_url, 'num': 0, 'query': query})
        
        # Now check for numbered entries (_1, _2, etc.)
        for i in range(1, max_entries_to_check + 1):
            numbered_url = f"{base_url}{query}_{i}"
            numbered_page = requests.get(numbered_url, headers=_HEADERS)
            if numbered_page.status_code == 200:
                entries.append({'url': numbered_url, 'num': i, 'query': query})
        
        if not entries:
            return await ctx.send(f"Couldn't find a definition for *{query}*. Please check the spelling.")
        
        # Sort entries by their number
        entries.sort(key=lambda x: x['num'])
        
        # Function to create embed for a specific entry
        async def create_dict_embed(entry):
            url = entry['url']
            query = entry['query']
            entry_num = entry['num']
            
            try:
                page = requests.get(url, headers=_HEADERS)
                soup = bs(page.content, 'html.parser')
                
                embed = discord.Embed(color=self.user_color)
                embed.set_author(
                    name=f'Oxford Learner\'s Dictionaries: {query.title()}',
                    url=url,
                    icon_url="https://www.oxfordlearnersdictionaries.com/favicon.ico"
                )
                
                # Add entry number indicator if not the base entry
                if entry_num > 0:
                    embed.title = f"Entry {entry_num}"
                
                # Get word type (noun, verb, etc.)
                pos = soup.find('span', {'class': 'pos'})
                
                # Get all senses (definitions)
                senses = soup.find_all('li', {'class': 'sense'})
                if not senses:
                    return None
                
                # Add definitions as fields
                for i, sense in enumerate(senses[:3], 1):  # Limit to 3 senses
                    definition = sense.find('span', {'class': 'def'})
                    if definition:
                        # Get grammar info (like [uncountable])
                        grammar = sense.find('span', {'class': 'grammar'})
                        grammar_text = f"{grammar.text} " if grammar else ""
                        
                        # Get sense heading if available (like "romantic" for love)
                        sense_heading = sense.find_previous('h2', {'class': 'shcut'})
                        heading_text = f"**{sense_heading.text}**\n" if sense_heading else ""
                        
                        # Format the field
                        field_name = f"{pos.text} {query.title()}" if pos else query.title()
                        field_value = f"{heading_text}`{grammar_text}`{definition.text}"
                        
                        embed.add_field(
                            name=field_name,
                            value=field_value[:1024],  # Field value limit
                            inline=False
                        )
                
                # Get pronunciation
                phonetics = soup.find('span', {'class': 'phon'})
                if phonetics:
                    embed.add_field(name="Pronunciation", value=phonetics.text.strip(), inline=False)
                
                # Examples
                if 'examples' in term.lower():
                    examples = []
                    for sense in senses[:2]:  # Get examples from first 2 senses
                        sense_examples = sense.find_all('span', {'class': 'x'})
                        examples.extend([ex.text.strip() for ex in sense_examples[:2]])
                    
                    if examples:
                        example_text = "\n".join([f"• {ex}" for ex in examples[:4]])
                        embed.add_field(name="Examples", value=example_text[:1024], inline=False)
                
                # Related matches
                related = soup.find('div', {'id': 'relatedentries'})
                if related:
                    all_matches = related.find('dt', text='All matches')
                    if all_matches:
                        matches = []
                        for item in all_matches.find_next('dd').find_all('li')[:5]:  # First 5 matches
                            match_text = item.text.strip()
                            if match_text and not match_text.startswith('See more'):
                                matches.append(f"• {match_text}")
                        
                        if matches:
                            embed.add_field(
                                name="All Matches",
                                value="\n".join(matches)[:1024],
                                inline=False
                            )
                
                return embed
            
            except Exception as e:
                print(f"Error creating embed for {url}: {e}")
                return None
        
        # Create initial embed for first entry
        current_index = 0
        embed = await create_dict_embed(entries[current_index])
        if not embed:
            return await ctx.send(f"Found entries but couldn't extract definitions. Try visiting: {entries[0]['url']}")
        
        message = await ctx.send(embed=embed)
        
        # Add pagination if multiple entries
        if len(entries) > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            
            def check(reaction, user):
                return (
                    user == ctx.author
                    and reaction.message.id == message.id
                    and str(reaction.emoji) in ["⬅️", "➡️"]
                )
            
            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=60.0, check=check
                    )
                    
                    if str(reaction.emoji) == "➡️":
                        current_index = (current_index + 1) % len(entries)
                    else:
                        current_index = (current_index - 1) % len(entries)
                    
                    new_embed = await create_dict_embed(entries[current_index])
                    if new_embed:
                        await message.edit(embed=new_embed)
                    await message.remove_reaction(reaction, user)
                    
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    break

async def setup(bot):
    await bot.add_cog(WordMeaning(bot))
    
