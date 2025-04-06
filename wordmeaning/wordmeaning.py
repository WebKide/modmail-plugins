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
                        "reaction_add", timeout=360.0, check=check
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
        """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Search Wikipedia with numbered disambiguation"""
        if not search:
            return await ctx.send(f"Usage: `{ctx.prefix}wiki <search term>`")

        try:
            wikipedia.set_lang("en")
            
            # Try to get the page directly first
            try:
                page = wikipedia.page(search, auto_suggest=False)
                return await self.send_wiki_result(ctx, page)
            except wikipedia.DisambiguationError as e:
                # Handle disambiguation pages with numbered options
                options = e.options[:10]  # Limit to first 10 options
                if not options:
                    return await ctx.send("No results found. Try a different search term.")
                
                # Create disambiguation embed
                embed = discord.Embed(
                    title=f"Disambiguation: {search}",
                    description="Please select an option by reacting with the corresponding number:",
                    color=self.user_color
                )
                
                # Add numbered options
                for i, option in enumerate(options, 1):
                    embed.add_field(
                        name=f"{i}. {option}",
                        value="\u200b",  # Zero-width space
                        inline=False
                    )
                
                if len(e.options) > 10:
                    embed.set_footer(text=f"Showing 1-10 of {len(e.options)} options")
                
                message = await ctx.send(embed=embed)
                
                # Add number reactions
                for i in range(1, min(len(options), 10) + 1):
                    await message.add_reaction(f"{i}\uFE0F\u20E3")  # Number emoji
                
                # Wait for user reaction
                def check(reaction, user):
                    return (
                        user == ctx.author and
                        reaction.message.id == message.id and
                        str(reaction.emoji) in [f"{i}\uFE0F\u20E3" for i in range(1, len(options) + 1)]
                    )
                
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=360.0, check=check
                    )
                    
                    # Get selected option index
                    selected_index = int(str(reaction.emoji)[0]) - 1
                    selected_option = options[selected_index]
                    
                    # Get the page for selected option
                    try:
                        selected_page = wikipedia.page(selected_option, auto_suggest=False)
                        await message.delete()  # Remove the disambiguation message
                        return await self.send_wiki_result(ctx, selected_page)
                    except wikipedia.PageError:
                        await ctx.send(f"Couldn't find a page for '{selected_option}'. Please try another option.")
                    except wikipedia.DisambiguationError:
                        await ctx.send(f"'{selected_option}' is still ambiguous. Please try a more specific search.")
                    
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    return
                
            except wikipedia.PageError:
                return await ctx.send("Couldn't find a specific page for that term. Try a different search.")

        except Exception as e:
            await ctx.send(f"An error occurred while searching Wikipedia: {str(e)}")

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
        
        # Convert spaces to hyphens for multi-word queries
        query = term.split(' ')[0].lower()  # First term is the word to search
        if ' ' in term:
            query = '-'.join(term.split())
        
        base_url = "https://www.oxfordlearnersdictionaries.com/definition/english/"
        
        try:
            # First try the direct URL
            url = f"{base_url}{query}"
            response = requests.get(url, headers=_HEADERS, allow_redirects=True)
            
            # If we got redirected, use the final URL
            final_url = response.url
            if response.history:
                url = final_url
            
            # Check if this is a numbered entry (like love_1)
            is_numbered = '_' in final_url.split('/')[-1]
            
            page = requests.get(url, headers=_HEADERS)
            if page.status_code != 200:
                return await ctx.send(f"Couldn't find a definition for *{query}*. Please check the spelling.")

            soup = bs(page.content, 'html.parser')
            
            # Create embed
            embed = discord.Embed(color=self.user_color)
            embed.set_author(
                name=f'Oxford Learner\'s Dictionaries: {query.replace("-", " ").title()}',
                url=url,
                icon_url="https://www.oxfordlearnersdictionaries.com/favicon.ico"
            )

            # Get word type (noun, verb, etc.)
            pos = soup.find('span', {'class': 'pos'})
            if pos:
                embed.title = f"[{pos.text}] {query.replace('-', ' ').title()}"
                if is_numbered:
                    embed.title += f" ({final_url.split('_')[-1]})"  # Add (_1) if numbered entry

            # Get pronunciation
            phonetics = soup.find('span', {'class': 'phon'})
            if phonetics:
                embed.add_field(name="Pronunciation", value=phonetics.text.strip(), inline=False)

            # Get all senses (definitions)
            senses = soup.find_all('li', {'class': 'sense'})
            if not senses:
                return await ctx.send(f"Found the word but couldn't extract definitions. Try visiting: {url}")

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
                    
                    # Format the field value
                    field_value = f"{heading_text}`{grammar_text}`{definition.text}"
                    
                    embed.add_field(
                        name=f"Definition {i}",
                        value=field_value[:1024],  # Field value limit
                        inline=False
                    )

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

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred while looking up '{query}'. Please try again later.\nError: {str(e)}")

async def setup(bot):
    await bot.add_cog(WordMeaning(bot))
    
