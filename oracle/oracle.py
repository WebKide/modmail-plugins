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

import discord, asyncio, random, textwrap, traceback

from discord.ext import commands
from datetime import date

dev_list = [323578534763298816]


class Oracle(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Understand any cituation with these oracle commands, but don't take them too seriously """
    def __init__(self, bot):
        self.bot = bot
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange

    # +------------------------------------------------------------+
    # |            Prediction command: EIGHTBALL                   |
    # +------------------------------------------------------------+
    @commands.command(aliases=['8ball'], no_pm=True)
    async def eightball(self, ctx, *, question=None):
        """ Ask questions to the 8ball """
        with open('data/answers.json') as f:
            choices = json.load(f)

        if not question:
            return await ctx.send('Where is your question?')

        if question.endswith("?") and question != "?":
            response = random.choice(choices)
            author = ctx.message.author

            e = discord.Embed(color=self.user_color)
            e.set_author(name=f"{author.display_name}'s question:", icon_url=author.avatar_url)
            e.description = f'```{question}```'
            e.add_field(name='\N{BILLIARDS} answer:', value=f'```css\n{response}```')
            e.set_footer(text=f"ADVICE: Don't take this too seriously | {date.today()}")

            try:
                return await ctx.send(embed=e)
            except discord.HTTPException:
                await ctx.send(f'\N{BILLIARDS} answer: ```css\n{response}```')

        else:
            await ctx.send(f"*{question}* doesn't look like a yes/no question.")

    # +------------------------------------------------------------+
    # |            Prediction command: TAROT                       |
    # +------------------------------------------------------------+
    @commands.group(invoke_without_command=True, descriptions='3 cards spread reading', no_pm=True)
    async def tarot(self, ctx):
        """ Reading of 3 cards for you """
        msg = 'Relax and concentrate on your question, breathe in and out deeply, when you’re ready ' \
            f'use **`{ctx.prefix}tarot reading`** to start your reading.'
        return await ctx.send(msg, delete_after=69)

    @tarot.command(aliases=['cards'], no_pm=True)
    async def reading(self, ctx):
        """ 3 cards spread reading """
        u = ctx.author
        deck = 'https://i.imgur.com/rUAjxYx.png'
        with open('data/tarot_major.json') as f:
            choices = json.load(f)

        try:
            s = await ctx.send(f"Let me shuffle my tarot deck... {u.display_name}")
            await ctx.channel.trigger_typing()
            await asyncio.sleep(5)

            first = "1\N{COMBINING ENCLOSING KEYCAP} ***The Past:***\nThis card represents your situation*—why " \
                    "you’re currently in the spot you’re in*. It often symbolizes a person or relationship " \
                    "in your life that has influenced your question."
            second = "2\N{COMBINING ENCLOSING KEYCAP} ***The Present:***\nThis card represents the current " \
                     "problem, often as a direct result of the situation. Pay close attention to this card " \
                     "as it may be trying to show you things that you’ve previously overlooked."
            third = "3\N{COMBINING ENCLOSING KEYCAP} ***The Future:***\nThe final card in this 3-card spread " \
                    "provides guidance to face and overcome your issue. It may provide options you hadn’t " \
                    "considered or resources and people you’d overlooked."

            e = discord.Embed(color=self.user_color)
            e.set_author(name=f'Interpretation for {u.display_name}', icon_url=u.avatar_url)
            e.set_thumbnail(url=deck)
            e.set_author(name=f'{u.name} | {u.display_name} | {u.id}')

            e.add_field(name='Situation As It Is',
                        value=f'{first}\n{random.choice(choices)}\n', inline=False)
            e.add_field(name='Course of Action to be Taken',
                        value=f'{second}\n{random.choice(choices)}\n', inline=False)
            e.add_field(name='New Situation that Will Evolve',
                        value=f'{third}\n{random.choice(choices)}\n', inline=False)
            e.set_footer(text=f"Three Card spread reading | {date.today()}", icon_url=deck)

            await s.edit(embed=e)

        except discord.Forbidden:
            await ctx.send('I need embed perms to send result.')

    # +------------------------------------------------------------+
    # |            Prediction command: ORACLE                      |
    # +------------------------------------------------------------+
    @commands.command(aliases=['crystalball', 'iching', 'i-ching'], no_pm=True)
    async def oracle(self, ctx, *, question: str = None):
        """
        Oracle prediction
        Based on the ancient divination I Ching oracle,
        [use it as a guide]
        
        Usage:
        {prefix}oracle [yes/no question?]
        """
        with open('data/oracle.json') as f:
            choices = json.load(f)

        iching = 'http://i.imgur.com/biEvXBN.png'
        u = ctx.message.author
        p = ctx.invoked_with

        if question is None:
            return await ctx.send('You have to ask a yes/no question to use this command.', delete_after=23)

        if question.endswith('?') and question != '?':
            try:
                await ctx.send(f"Let me fetch your answer... {u.display_name}")
                await ctx.channel.trigger_typing()
                await asyncio.sleep(5)
            except discord.Forbidden:
                pass

            e = discord.Embed(colour=discord.Colour(0xc5b358))
            e.set_thumbnail(url=iching)
            e.set_footer(text=f"Ancient Oracle's inspiration | {date.today()}", icon_url=iching)
            e.set_author(name=f'{p} interpretation for {u.display_name}', icon_url=u.avatar_url)
            e.description = f'Meditation:\n{random.choice(choices)}'
            return await ctx.send(embed=e)

        else:
            return await ctx.send(f"*{question}*/ndoesn't look like a yes/no question.", delete_after=69)


def setup(bot):
    bot.add_cog(Oracle(bot))
