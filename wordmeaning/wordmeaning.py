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
        """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Search definitions in English
        using Oxford English Dictionary database
        
        Usage:
        {prefix}dict <word> [synonyms|proverbs|examples]"""
        if term is None:
            sample = random.choice(['lecture', 'fantasy', 'gathering', 'gradually', 'international', 'desire'])
            v = f'{ctx.prefix}{ctx.invoked_with} {sample}'
            usage = f'**Usage:** basic results\n{v}\n\n' \
                   f'**Advanced Usage:** add any parameter\n{v} `examples` `synonyms` `proverbs` `sourcecode`'
            return await ctx.send(usage)
        
        await ctx.channel.typing()

        query = term.split(' ')[0].lower()  # First term is the word to search
        url = f"{self.query_url}{query}"
        
        try:
            page = requests.get(url, headers=_HEADERS)
            page.raise_for_status()  # Raise exception for bad status codes
            
            embed = discord.Embed(color=self.user_color)
            embed.set_author(
                name=f'Definition of {query.title()} in English by Oxford Dictionaries',
                url=url,
                icon_url="https://media.discordapp.net/attachments/541059392951418880/557660549073207296/oxford_favicon.png"
            )

            # Parse only relevant sections for performance
            _section_content = ss("section", attrs={"class": ["gramb", "etymology etym", "pronSection etym"]})
            soup = bs(page.content, "html.parser", parse_only=_section_content, from_encoding="utf-8")

            # Word classification (noun, verb, etc.)
            classification = soup.find('span', attrs={"class": "pos"})
            if classification:
                embed.title = f"*`[{classification.text}]`*"

            # Definition
            definition = soup.find('span', attrs={"class": "ind"})
            if definition:
                embed.description = f"1. {definition.text[:500]}"
            else:
                embed.description = f"Whoopsie! I couldn't find a definition for *{query}*.\n" \
                                    f"Check spelling, or look for a variation of {query} as verb, noun, etc."

            # Examples
            if 'examples' in term.lower() and query != 'examples':
                examples = soup.find_all('div', attrs={"class": "exg"})
                if examples:
                    example_text = "\n".join([f"*{ex.text[1:]}*" for ex in examples[:3]])
                    embed.add_field(name='Examples', value=example_text[:1024], inline=False)

            # Synonyms
            if 'synonyms' in term.lower() and query != 'synonyms':
                synonyms = soup.find('div', attrs={"class": "synonyms"})
                if synonyms:
                    syns_text = synonyms.text.replace('Synonyms', '').replace('View synonyms', '').strip()
                    if syns_text:
                        embed.add_field(name='Synonyms', value=f'```bf\n{syns_text[:460]}```', inline=False)

            # Proverbs
            if 'proverbs' in term.lower() and query != 'proverbs':
                proverb = soup.find('div', attrs={"class": "trg"})
                if proverb:
                    try:
                        x = proverb.text.replace("’ ‘", "’\n‘").replace(". ‘", ".\n\n‘")
                        z = '’'.join(x.split("’")[3:-4])
                        embed.add_field(name='Proverb', value=f"*{z[1:][:960]}...*", inline=False)
                    except (TypeError, IndexError):
                        pass

            # Etymology and pronunciation
            pronunciation = soup.find('span', attrs={"class": "phoneticspelling"})
            if pronunciation:
                etymology = ""
                try:
                    etymology_section = soup.find_all('section', attrs={"class": "etymology etym"})
                    if len(etymology_section) > 1:
                        etymology = f"\n**Origin:** *{etymology_section[1].find('p').text}*"
                except (IndexError, AttributeError):
                    pass
                
                embed.add_field(
                    name=f'Etymology of {query.title()}',
                    value=f"**Pronunciation:** `({pronunciation.text.replace('/', '')})`{etymology[:750]}",
                    inline=False
                )

            embed.set_footer(text=f'Oxford University Press © {dt.now().year} | Latency: {self.bot.latency*1000:.2f}ms')
            await ctx.send(embed=embed)

        except requests.HTTPError:
            await ctx.send(f"Couldn't find a definition for *{query}*. Please check the spelling.")
        except Exception as e:
            tb = traceback.format_exc()
            await ctx.send(f'```css\n[DICTIONARY ERROR]\n{e}```\n```py\n{tb[:1000]}```')

async def setup(bot):
    await bot.add_cog(WordMeaning(bot))
    
