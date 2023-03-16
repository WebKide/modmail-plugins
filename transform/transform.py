"""
MIT License
Copyright (c) 2020-2023 WebKide [d.id @323578534763298816]
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
from collections import defaultdict  # wordai

dev_list = [323578534763298816]


class Transform(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ modify text in various ways... """
    def __init__(self, bot):
        self.bot = bot
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange
        self.transitions = defaultdict(lambda: defaultdict(int))  # wordai
        self.build_transitions()  # wordai


    # +------------------------------------------------------------+
    # |                     Word/Name-generator                    |
    # +------------------------------------------------------------+
    def build_transitions(self):
        vow = ['a', 'i', 'u', 'e', 'o', 'y', '', 'a', 'i', 'u', 'e', 'o', '']
        con = [
            'qu', 'w', 'wh', 'r', 't', 'th', 'y', 'p', 'mp', 's', 'ss', 'd', 'f', 'g', 'gü',
            'ß', 'h', 'j', 'ji', 'k', '', 'l', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ''
        ]
        for _ in range(999):
            word = f'{random.choice(vow)}{random.choice(con)}{random.choice(vow)}' \
                   f'{random.choice(vow)}{random.choice(con)}{random.choice(vow)}' \
                   f'{random.choice(con)}{random.choice(vow)}{random.choice(con)}'
            for i in range(len(word) - 2):
                pair = word[i:i+2]
                next_letter = word[i+2]
                self.transitions[pair][next_letter] += 1

    @commands.command(aliases=['word_ai'])
    async def wordai(self, ctx, results: int = 15):
        """ Generate words artificially """
        words = []
        for _ in range(results):
            word = ''
            pair = random.choice(list(self.transitions.keys()))
            while len(word) < 9:
                next_letters = list(self.transitions[pair].keys())
                weights = list(self.transitions[pair].values())
                next_letter = random.choices(next_letters, weights=weights)[0]
                word += next_letter
                pair = pair[1] + next_letter
            word = word.title()
            words.append(word)
        await ctx.send(', '.join(words))
    
    @commands.command(no_pm=True)
    async def wordaig(self, ctx, results: int = 23):
        """ Generate names using AI Generator """
        vow = ['a', 'i', 'u', 'e', 'o', 'y', '', 'a', 'i', 'u', 'e', 'o', '']
        con = [
            'qu', 'w', 'wh', 'r', 't', 'th', 'y', 'p', 'mp', 's', 'ss', 'd', 'f', 'g', 'gü',
            'ß', 'h', 'j', 'ji', 'k', '', 'l', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ''
        ]
        word_length = random.randint(3, 9)  # max length of artificially generated name
        artificially_generated_names = []
        for i in range(results):
            word = ''.join(random.choice(con if j%2 else vow) for j in range(word_length))
            artificially_generated_names.append(word.title())
        
        await ctx.send(', '.join(artificially_generated_names))

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
            e = discord.Embed(color=self.user_color)
            e.add_field(name='Input:', value=f'```py\n{text}```', inline=False)
            e.add_field(name='Result:', value=f'**```css\n{result}```**', inline=False)
            await ctx.send(embed=e)

    # +------------------------------------------------------------+
    # |              Change any text into cursive                  |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def cursive(self, ctx, *, text: str = None):
        """ Convert any text into 𝒸𝓊𝓇𝓈𝑒𝒾𝓋𝑒 text """
        if text is None:
            return await ctx.send("You have to input some text first.", delete_after=23)

        if text.lower() is not None:
            msg = ""
            char = "abcdefghijklmnopqrstuvwxyz0123456789+-+()."
            tran = "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫+-+()."
            table = str.maketrans(char, tran)
            tinify = text.translate(table)
            result = f'{msg}{tinify[::1]}'
            e = discord.Embed(color=self.user_color)
            e.add_field(name='Input:', value=f'```py\n{text}```', inline=False)
            e.add_field(name='Result:', value=f'**```css\n{result}```**', inline=False)
            await ctx.send(embed=e)

    # +------------------------------------------------------------+
    # |              Change any text into cursive                  |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def bold(self, ctx, *, text: str = None):
        """ Convert any text into 𝕓𝕠𝕝𝕕 text """
        if text is None:
            return await ctx.send("You have to input some text first.", delete_after=23)

        if text is not None:
            msg = ""
            char = "aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ0123456789+-+()."
            tran = "𝕒𝔸𝕓𝔹𝕔ℂ𝕕𝔻𝕖𝔼𝕗𝔽𝕘𝔾𝕙ℍ𝕚𝕀𝕛𝕁𝕜𝕂𝕝𝕃𝕞𝕄𝕟ℕ𝕠𝕆𝕡ℙ𝕢ℚ𝕣ℝ𝕤𝕊𝕥𝕋𝕦𝕌𝕧𝕍𝕨𝕎𝕩𝕏𝕪𝕐𝕫ℤ𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡+-+()."
            table = str.maketrans(char, tran)
            tinify = text.translate(table)
            result = f'{msg}{tinify[::1]}'
            e = discord.Embed(color=self.user_color)
            e.add_field(name='Input:', value=f'```py\n{text}```', inline=False)
            e.add_field(name='Result:', value=f'**```css\n{result}```**', inline=False)
            await ctx.send(embed=e)

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
                else:
                    i += letter
            return await ctx.send(i)
        else:
            await ctx.send(f'**Usage:**\n`{ctx.prefix}{ctx.invoked_with} [text]`', delete_after=23)

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
            _error = f'**Usage:**\n`{ctx.prefix}{ctx.invoked_with} [text here]`'
            await ctx.send(_error, delete_after=23)


async def setup(bot):
    await bot.add_cog(Transform(bot))
