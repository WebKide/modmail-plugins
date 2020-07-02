import discord, asyncio, random, textwrap, traceback, wikipedia, urllib.request, unicodedata2 as unicodedata
try:
    import inspect, requests
except:
    pass

from discord.ext import commands
from bs4 import BeautifulSoup, SoupStrainer

_HEADERS = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR '
                          '2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8; '
                          'InfoPath.3; .NET4.0C; .NET4.0E) chromeframe/8.0.552.224',
            'Accept-Language': 'en-us'}


class Misc(commands.Cog):
    """Useful commands to make your life easier"""
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange
        self.sessions = set()
        self.query_url = "https://en.oxforddictionaries.com/definition/"
        self.sess = requests.Session()

    # +------------------------------------------------------------+
    # |                     NAME                                   |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def name(self, ctx, text: str = None):
        """ Change Bot's name """
        if text is None:
            return await ctx.send("What's my new name going to be?")

        if text is not None:
            try:
                await ctx.bot.edit_profile(username=str(text[6:]))
                await ctx.send(f'Thanks for renaming me: {text}')
                await ctx.message.delete()
            except Exception as e:
                await ctx.send(f'Failed to change my name!\n```{e}```')
                pass

    # +------------------------------------------------------------+
    # |                       LOGO                                 |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def logo(self, ctx, link: str = None):
        """ Change Bot's avatar img """
        if link is None:
            return await ctx.send('You need to use an image URL as a link.')

        if link is not None:
            try:
                with urllib.request.urlopen(link) as response:
                    img = response.read()
                    await ctx.bot.edit_profile(avatar=img)
                    await ctx.send('New logo added successfully!', delete_after=5)
                    await ctx.message.delete()
            except Exception as e:
                await ctx.send(f'Failed to update logo image!\n```{e}```')
                pass

    # +------------------------------------------------------------+
    # |                     SAUCE                                  |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def sauce(self, ctx, *, command: str = None):
        """ See the source code for any command """
        if command is not None:
            i = str(inspect.getsource(self.bot.get_command(command).callback))

            if len(i) < 1980:
                source_full = i.replace('```', '`\u200b`\u200b`')
                await ctx.send('```py\n' + source_full + '```')

            if len(i) > 1981:
                source_trim = i.replace('```', '`\u200b`\u200b`')[:1980]
                await ctx.send('```py\n' + source_trim + '```')

        else:
            await ctx.send(f"Tell me what cmd's source code you want to see.")

    # +------------------------------------------------------------+
    # |                     CHARINFO                               |
    # +------------------------------------------------------------+
    @commands.command()
    async def charinfo(self, ctx, *, characters: str):
        """
        Return UNICODE characters
        Usage:
        charinfo ā
        """
        if len(characters) > 15:
            return await ctx.send('Too many characters ({}/15)'.format(len(characters)))

        else:
            fmt = '​`{2}​` — `\\U{0:>08}​`\n​```tex\n\\N{{{1}}}​```'

            def to_string(c):
                digit = format(ord(c), 'x')
                name = unicodedata.name(c, 'Name not found.')
                return fmt.format(digit, name, c)

            e = discord.Embed(color=self.user_color)
            e.description = '\n'.join(map(to_string, characters))
            # e.add_field(name='', value=f"```tex\n\\N{{{1}}}​```")
            await ctx.send(embed=e)

    # +------------------------------------------------------------+
    # |                       URBAN                                |
    # +------------------------------------------------------------+
    @commands.command()
    async def urban(self, ctx, *, search_terms: str = None):
        """Searches up a term in Urban Dictionary"""
        if search_terms is None:
            return await ctx.send('What should I search for in ud?```css\nurban ')

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
            async with ctx.session.get(url) as r:
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

            await ctx.send(embed=emb)

    # +------------------------------------------------------------+
    # |                          WIKIPEDIA                         |
    # +------------------------------------------------------------+
    @commands.command()
    async def wiki(self, ctx, *, search: str = None):
        """Addictive Wikipedia search command!"""
        if search == None:
            await ctx.channel.send(f'Usage: `{ctx.prefix}wiki [search terms]`')
            return

        results = wikipedia.search(search)
        if not len(results):
            no_results = await ctx.channel.send("Sorry, didn't find any result.")
            await asyncio.sleep(5)
            await ctx.message.delete(no_results)
            return

        newSearch = results[0]
        try:
            wik = wikipedia.page(newSearch)
        except wikipedia.DisambiguationError:
            more_details = await ctx.channel.send('Please input more details.')
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
        """ Search definitions in English """
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
            _section_content = SoupStrainer("section", attrs={"class": ["gramb", "etymology etym", "pronSection etym"]})

            # Then we parse the resulting web page with Beautiful Soup 4
            soup = BeautifulSoup(page.content, "html.parser", parse_only=_section_content, from_encoding="utf-8")

            # ================= Send HTML5 code as a message into chat ====================
            if ctx.message.content.endswith('sourcecode') and query is not 'sourcecode':
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
            if 'examples' in ctx.message.content and query is not 'examples':
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
                    if 'synonyms' in ctx.message.content and query is not 'synonyms':
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
                    if 'proverbs' in ctx.message.content and query is not 'proverbs':
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
            e.set_footer(text=f'Oxford University Press © 2018 | Duration: {self.bot.ws.latency * 1000:.2f} ms')
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

    # +------------------------------------------------------------+
    # |                                                            |
    # +------------------------------------------------------------+

    # +------------------------------------------------------------+
    # |                                                            |
    # +------------------------------------------------------------+

    # +------------------------------------------------------------+
    # |                                                            |
    # +------------------------------------------------------------+

    # +------------------------------------------------------------+
    # |                                                            |
    # +------------------------------------------------------------+
    
def setup(bot):
    bot.add_cog(Misc(bot))
