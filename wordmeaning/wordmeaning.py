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

import discord, asyncio, random, textwrap, traceback, requests, urllib.request, wikipedia

from discord.ext import commands
from bs4 import BeautifulSoup as bs, SoupStrainer as ss
from datetime import datetime as dt
from pytz import timezone as tz

_HEADERS = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR '
                          '2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8; '
                          'InfoPath.3; .NET4.0C; .NET4.0E) chromeframe/8.0.552.224',
            'Accept-Language': 'en-us'}

dev_list = [323578534763298816]

class WordMeaning(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ find definitions of English words """
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange
        self.sessions = set()
        self.query_url = "https://en.oxforddictionaries.com/definition/"
        self.sess = requests.Session()


    # +------------------------------------------------------------+
    # |                       URBAN                                |
    # +------------------------------------------------------------+
    @commands.command(aliases=['ud'])
    async def urban(self, ctx, *, search_terms: str = None):
        """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Urban Dictionary search
        retrieves up to 10 results for same word
        
        Usage:
        {prefix}urban <query>
        {prefix}ud oof 5
        """
        if search_terms is None:
            return await ctx.send('What should I search for you?')

        else:
            search_terms = search_terms.split()
            definition_number = terms = None

            try:
                definition_number = int(search_terms[-1]) - 1
                search_terms.remove(search_terms[-1])
            except ValueError:
                definition_number = 0

            if definition_number not in range(0, 11):
                pos = 0
            search_terms = "+".join(search_terms)
            url = "http://api.urbandictionary.com/v0/define?term=" + search_terms
            async with self.bot.session.get(url) as r:
                result = await r.json()
            emb = discord.Embed()
            emb.colour = (discord.Colour(0xed791d))

            if result.get('list'):
                definition = result['list'][definition_number]['definition']
                example = result['list'][definition_number]['example']
                defs = len(result['list'])
                search_terms = search_terms.split("+")
                emb.title = "{}  ({}/{})".format(" ".join(search_terms), definition_number + 1, defs)
                emb.description = definition
                emb.add_field(name='Example', value=example)

            else:
                emb.title = f"Didn't find anything for *{search_terms}*"

            try:
                await ctx.send(embed=emb)
            except Exception as e:
                tb = traceback.format_exc()
                return await ctx.send(f'```css\n[OOPS, I DID IT AGAIN]\n{e}```\n```py\nヾ(ﾟ∀ﾟ○)ﾂ三ヾ(●ﾟдﾟ)ﾉ\n\n{tb}```')

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
        if search == None:
            await ctx.channel.send(f'Usage: `{ctx.prefix}wiki [search terms]`', delete_after=23)
            return

        results = wikipedia.search(search)
        if not len(results):
            no_results = await ctx.channel.send("Sorry, didn't find any result.", delete_after=23)
            await asyncio.sleep(5)
            await ctx.message.delete(no_results)
            return

        newSearch = results[0]
        try:
            wik = wikipedia.page(newSearch)
        except wikipedia.DisambiguationError:
            more_details = await ctx.channel.send('Please input more details.', delete_after=23)
            await asyncio.sleep(5)
            await ctx.message.delete(more_details)
            return

        emb = discord.Embed()
        emb.colour = (discord.Colour(0xed791d))
        emb.title = wik.title
        emb.url = wik.url
        textList = textwrap.wrap(wik.content, 500, break_long_words=True, replace_whitespace=False)
        emb.add_field(name="Wikipedia Results", value=textList[0] + "...")
        await ctx.send(embed=emb)

    # +------------------------------------------------------------+
    # |               Oxford English Dictionary                    |
    # +------------------------------------------------------------+
    @commands.command(name='dict', description='Oxford English Dictionary', aliases=['oed'])
    async def _dict(self, ctx, *, term: str = None):
        """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Search definitions in English
        using Oxford English Dictionary database
        
        Usage:
        {prefix}dict <word> [synonyms|proverbs|examples]"""
        if term is None:  # Simple usage return for invoking an empty cmd
            sample = random.choice(['lecture', 'fantasy', 'gathering', 'gradually ', 'international', 'desire'])
            v = f'{ctx.prefix}{ctx.invoked_with} {sample}'
            usage = f'**Usage:** basic results\n{v}\n\n' \
                f'**Advanced Usage:** add any parameter\n{v} `examples` `synonyms` `proverbs` `sourcecode`'
            return await ctx.send(usage)
        await ctx.channel.trigger_typing()

        query = ''.join(term.split(' ')[0])  # We only want to search the first term, the rest is for extra result
        url = f"{self.query_url}{query.lower()}"  # we lower it so it works as part of the search link
        page = requests.get(url, headers=_HEADERS)  # requests code, use the headers to appear like a normal browser
        e = discord.Embed(color=self.user_color)  # This command is EMBED-only, it doesn't work without embed perms
        x = "https://media.discordapp.net/attachments/541059392951418880/557660549073207296/oxford_favicon.png"

        try:
            e.set_author(name=f'Definition of {query.title()} in English by Oxford Dictionaries', url=url, icon_url=x)

            # SoupStrainer is required to load 1/3 of the page, discarding unnecessary content
            # "gamb" contains definition, "etym" contains pronunciation and origin
            _section_content = ss("section", attrs={"class": ["gramb", "etymology etym", "pronSection etym"]})

            # Then we parse the resulting web page with Beautiful Soup 4
            soup = bs(page.content, "html.parser", parse_only=_section_content, from_encoding="utf-8")

            # ================= Send HTML5 code as a message into chat ====================
            if ctx.message.content.endswith('sourcecode') and query != 'sourcecode':
                # This is mostly for debugging purposes, if cmd doesn't give a result, check that the code works,
                # if `code` returns empty, it is because the command couldn't find a valid page for {query}
                defs = soup.find('section', attrs={"class": "gramb"})  # sends page parsed as HTML5
                if defs is not None:
                    block = await ctx.send(f'```html\n{defs.prettify()[:1970]}``` Chars: `{len(defs.text)}`')
                    await block.add_reaction('\N{WHITE HEAVY CHECK MARK}')

            # ============= Word and its classification and pronunciation ================
            classification = soup.find('span', attrs={"class": "pos"})  # noun, verb, adjective, adverb, etc...
            if classification is not None:
                cl = f"*`[{classification.text}]`*  " or "\u200b"
                e.title = cl  # f"{cl}{query.title()}{pr.replace('/', '')}"
            # =============================================================================
            definition = soup.find('span', attrs={"class": "ind"})  # first description
            if definition is not None:  # BUG-HUNTER, 1ˢᵗ 2ⁿᵈ 3ʳᵈ, 4ᵗʰ
                # Checks for a definition, if not found, it defaults to fail-safe description below
                e.description = f"1. {definition.text[:500]}"  # await ctx.send(first.text[:500])  # BUG-HUNTER
            # ===================== if cmd *args == 'examples' ============================
            if 'examples' in ctx.message.content and query != 'examples':
                example_1 = soup.find('div', attrs={"class": "exg"})  # first example
                if example_1 is not None:
                    ex_1 = f'*{example_1.text[1:]}*' or "\u200b"
                    try:
                        example_2 = soup.find_all('div', attrs={"class": "exg"})[1]
                        list_1 = example_2.text[1:].replace("’ ‘", "’*\n*‘")
                        ex_2 = f'\n*{list_1}'
                    except IndexError:  # ResultSet object has no attribute '.text'
                        ex_2 = "\u200b"
                    result = f"{ex_1}{ex_2}"  # This is merely aesthetic so that it ends with ... or not
                    if result[:800].endswith("’"):  # We expect it to ed well
                        complete = f'{result[:800]}*'
                    else:  # if it doesn't, then we format it properly here
                        complete = f'{result[:800]}...*'
                    e.add_field(name='Examples', value=complete, inline=False)  # BUG-HUNTER

            # ======================= First Synonyms in result =============================
            try:
                synonyms_1 = soup.find('div', attrs={"class": "synonyms"})  # .find_all('strong')  # Synonyms for search
                if synonyms_1 is not None:
                    results = synonyms_1.text
                    syns = results.replace('Synonyms', '').replace('View synonyms', '') or "#z"
                    if 'synonyms' in ctx.message.content and query != 'synonyms':
                        e.add_field(name='Synonyms', value=f'```bf\n{syns[:460]}```', inline=False)  # BUG-HUNTER
                    else:
                        synonyms_2 = soup.find('div', attrs={"class": "exs"})
                        res = synonyms_2.find_all('strong').text
                        e.add_field(name='Synonyms', value=f'```bf\n{res}```', inline=False)  # BUG-HUNTER
                    # await ctx.send(phrases.text[:270])  # BUG-HUNTER
            except AttributeError:  # ResultSet object has no attribute '.text'
                pass

            # ======================= Output proverbs and samples ==========================
            proverb = soup.find('div', attrs={"class": "trg"})
            if proverb is not None:
                try:
                    proverb.find('div', attrs={"span": "sense-registers"})  # Proverb, {query} used in sentences
                    x = proverb.text.replace("’ ‘", "’\n‘").replace(". ‘", ".\n\n‘")
                    if 'proverbs' in ctx.message.content and query != 'proverbs':
                        z = '’'.join(x.split("’")[3:-4])  # split x and output after 'More example sentences...'
                        e.add_field(name='Proverb', value=f"*{z[1:][:960]}...*", inline=False)
                    else:
                        z = '’'.join(x.split("’")[3:-2])
                        e.add_field(name='Proverb', value=f"*{z[1:][:240]}...*", inline=False)
                        # return await ctx.send(z[:1600])  # BUG-HUNTER
                except TypeError:  # TypeError: unhashable type: 'slice' in [:260]
                    pass

            # =================== Word Origin ETYMOLOGY [working] =========================
            try:
                pronunciation_2 = soup.find('span', attrs={"class": "phoneticspelling"})  # etymology & pronunciation
                if pronunciation_2 is not None:
                    try:
                        classification_2 = soup.find_all('section', attrs={"class": "etymology etym"})[1].find('p').text
                        msg = f'\n**Origin:** *{classification_2}*'
                    except IndexError:  # ResultSet object has no attribute '.text'
                        msg = ""
                    pro = f"**Pronunciation:** `({pronunciation_2.text})`" or "N/A"
                    e.add_field(name=f'Etymology of {query.title()}', value=f"{pro.replace('/', '')}{msg[:750]}",
                                inline=False)
                    # await ctx.send(msg[:750])  # BUG-HUNTER
            except IndexError:  # ResultSet object has no attribute '.text'
                pass
            # ================== copyright acknowledgments ================================
            e.set_footer(text=f'Oxford University Press © 2020 | Duration: {self.bot.ws.latency * 1000:.2f} ms')
            # ================== Fail-safe for words without a definition =================
            if not definition:
                e.description = f"Whoopsie! I couldn't find a definition for *{query}*.\n" \
                    f"Check spelling, or look for a variation of {query} as verb, noun, etc."

            try:
                return await ctx.send(embed=e)
            except Exception as e:
                tb = traceback.format_exc()
                return await ctx.send(f'```css\n[DAFUQ]\n{e}```\n```py\n、ヽ｀、ヽ｀个o(･･｡)｀ヽ、｀ヽ、\n\n{tb}```')

            # await ctx.message.add_reaction('thankful:389969145019498502')
        except Exception as e:
            tb = traceback.format_exc()
            return await ctx.send(f'```css\n[OOPS, I DID IT AGAIN]\n{e}```\n```py\nヾ(ﾟ∀ﾟ○)ﾂ三ヾ(●ﾟдﾟ)ﾉ\n\n{tb}```')


async def setup(bot):
    await bot.add_cog(WordMeaning(bot))
