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

import discord, asyncio, random, textwrap, traceback, unicodedata2 as unicodedata

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
                name = unicodedata.name(c, 'Name not found.')
                return fmt.format(digit, name, c)

            e = discord.Embed(color=self.user_color)
            e.description = '\n'.join(map(to_string, characters))
            # e.add_field(name='', value=f"```tex\n\\N{{{1}}}​```")
            await ctx.send(embed=e)


    # +------------------------------------------------------------+
    # |                     Word/Name-generator                    |
    # +------------------------------------------------------------+
    @commands.command(aliases=['word_ai'])
    async def wordai(self, ctx, results: int = None):
        """ Generate words artificially """
        vow = ['a', 'i', 'u', 'e', 'o', 'y', '', 'a', 'i', 'u', 'e', 'o', '']
        con = [
            'qu', 'w', 'wh', 'r', 't', 'th', 'y', 'p', 'mp', 's', 'ss', 'd', 'f', 'g', 'gü',
            'ß', 'h', 'j', 'ji', 'k', '', 'l', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ''
        ]
        word = f'{random.choice(vow)}{random.choice(con)}{random.choice(vow)}' \
               f'{random.choice(vow)}{random.choice(con)}{random.choice(vow)}' \
               f'{random.choice(con)}{random.choice(vow)}{random.choice(con)}'
        word = word.title()
        
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        finally:
            for int in results:
                if results is None:
                    return await ctx.send(name, delete_after=69)
                if results is not None:
                    x = random.randint(3, 9)
                    name = word[:x]
                    await ctx.sen(name)


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
                    await ctx.send(f'​`​`​`{e}​`​`​`', delete_after=15)
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

def setup(bot):
    bot.add_cog(Transform(bot))
