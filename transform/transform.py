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

import discord, asyncio, random, textwrap, traceback, unicodedata2 as ud2, string

from discord.ext import commands

dev_list = [323578534763298816]


class Transform(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ modify text in various ways... """
    def __init__(self, bot):
        self.bot = bot
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange


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
                name = ud2.name(c, 'Name not found.')
                return fmt.format(digit, name, c)

            e = discord.Embed(color=self.user_color)
            e.description = '\n'.join(map(to_string, characters))
            # e.add_field(name='', value=f"```tex\n\\N{{{1}}}​```")
            await ctx.send(embed=e)


    # +------------------------------------------------------------+
    # |                     Word/Name-generator                    |
    # +------------------------------------------------------------+
    vowels = ['a', 'e', 'i', 'o', 'u']
    consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']

    def generate_word():
        syllables = []
        for i in range(random.randint(2, 4)):
            if i % 2 == 0:  # even number, add a consonant
                syllables.append(random.choice(consonants))
            else:  # odd number, add a vowel
                syllables.append(random.choice(vowels))
        return ''.join(syllables)

    @commands.command(aliases=['genword', 'nameai'])
    async def wordai(self, ctx, results: int = 2):
        """ Generate words artificially """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        finally:
            try:
                if results is None:
                    results = 2
                for i in range(results):
                    word = generate_word()
                    word = word.capitalize()
                    await ctx.send(f'```py\n{word}```')
            except Exception as e:
                await ctx.send(f'```py\n{e}```', delete_after=69)
    
    '''
    @commands.command(aliases=['genword', 'nameai'])
    async def wordai(self, ctx, results: int = 2):
        """ Generate names using AI Generator """
        vow = ['a', 'i', 'u', 'e', 'o', 'y', '', 'a', 'i', 'u', 'e', 'o', '']
        con = [
            'qu', 'w', 'wh', 'r', 't', 'th', 'y', 'p', 'mp', 's', 'ss', 'd', 'f', 'g', 'gü',
            'ß', 'h', 'j', 'ji', 'k', '', 'l', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ''
        ]
        word_length = 23  # max length of artificially generated name
        artificially_generated_names = []
        for i in range(results):
            word = ''.join(random.choice(con if j%2 else vow) for j in range(word_length))
            artificially_generated_names.append(word.title())
        
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        finally:
            await ctx.send(', '.join(artificially_generated_names))
        '''


    # +------------------------------------------------------------+
    # |              Shrink text and make it tiny                  |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def tiny(self, ctx, *, text: str = None):
        """ Convert any text into ᵗⁱⁿʸ text """
        if text is None:
            return await ctx.send("You have to input some text first.", delete_after=23)

        if text.lower() is not None:
            msg = ""
            char = "abcdefghijklmnopqrstuvwxyz0123456789+-+()."
            tran = "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖ٩ʳˢᵗᵘᵛʷˣʸᶻ₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎•"
            table = str.maketrans(char, tran)
            tinify = text.translate(table)
            result = f'{msg}{tinify[::1]}'
            await ctx.send(result)


    # +------------------------------------------------------------+
    # |                       Clap                                 |
    # +------------------------------------------------------------+
    @commands.command()
    async def clap(self, ctx, *, msg: str = None):
        """ Clap that message! """
        if msg is not None:
            if len(msg.split(' ')) > 1:
                text = msg.replace(' ', ' 👏 ')
                await ctx.send(text)
            else:    await ctx.send('👏')

        else:
            try:    await ctx.send('👏')
            except discord.HTTPException as e:
                if ctx.author.id == 323578534763298816:
                    await ctx.send(f'```py\n{e}```', delete_after=15)
                else:    pass

    # +------------------------------------------------------------+
    # |                       Pray                                 |
    # +------------------------------------------------------------+
    @commands.command()
    async def pray(self, ctx, *, msg: str = None):
        """ Pray that message! """
        if msg is not None:
            if len(msg.split(' ')) > 1:
                text = msg.replace(' ', ' 🙏 ')
                await ctx.send(text)
            else:    await ctx.send(':clap:')

        else:
            try:    await ctx.send('🙏')
            except discord.HTTPException as e:
                if ctx.author.id == 323578534763298816:
                    await ctx.send(f'​`​`​`{e}​`​`​`', delete_after=15)
                else:    pass

    # +------------------------------------------------------------+
    # |                     SMALLCAPS                              |
    # +------------------------------------------------------------+
    @commands.command(aliases=['sc'], no_pm=True)
    async def smallcaps(self,ctx,*, msg: str = None):
        """ ᴄᴏɴᴠᴇʀᴛ ᴀ ᴛᴇxᴛ ᴛᴏ ꜱᴍᴀʟʟ ᴄᴀᴘꜱ """
        if msg is not None:
            alpha = list(string.ascii_lowercase)     
            converter = ['ᴀ', 'ʙ', 'ᴄ', 'ᴅ', 'ᴇ', 'ꜰ', 'ɢ', 'ʜ', 'ɪ', 'ᴊ', 'ᴋ', 'ʟ', 'ᴍ', 'ɴ', 'ᴏ', 'ᴘ', 'ǫ', 'ʀ', 'ꜱ', 'ᴛ', 'ᴜ', 'ᴠ', 'ᴡ', 'x', 'ʏ', 'ᴢ']
            i = ''
            exact = msg.lower()
            for letter in exact:
                if letter in alpha:
                    index = alpha.index(letter)
                    i += converter[index]
                else:    i += letter
            return await ctx.send(i)
        else:    await ctx.send(f'**Usage:**\n`{ctx.prefix}{ctx.invoked_with} [text]`', delete_after=23)

    # +------------------------------------------------------------+
    # |                     ZALGO                                  |
    # +------------------------------------------------------------+
    def zalgoify(self, text):
        text = text.replace('@', '')[:108]
        random_shit = map(chr, range(768, 879))
        marks = list(random_shit)
        result = text.split()
        zalgo = ' '.join(''.join(c + ''.join(random.choice(marks) for _ in range(i // 2 + 1)) * c.isalnum() for c in word) for i, word in enumerate(result))
        return zalgo

    @commands.command(no_pm=True)
    async def zalgo(self, ctx, *, msg: str = None):
        """S̏p͜ȉt́ o̕u͢ṭ Z͒̕aͣ͟l̾͡g̳̍o̓̀"""
        if msg is not None:
            zalgo_msg = self.zalgoify(msg)
            await ctx.send(f'```py\n{zalgo_msg}```')
        else:
            await ctx.send(f'**Usage:**\n`{ctx.prefix}{ctx.invoked_with} [text]`', delete_after=23)


async def setup(bot):
    await bot.add_cog(Transform(bot))
