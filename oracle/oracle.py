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

from datetime import datetime, date
from discord.ext import commands

from .eightball import ball_answers
from .iching import oracle_answer
from .tarot import card_deck
from .futhark import runes_list

dev_list = [323578534763298816]
#  I removed the lists from here to make the code easier to read, the lists are now 
#  their own Python files instead of JSON, the reason is that I don't want to use:
#      with open('futhark_runes_list.json') as f:
#          runes_list = json.load(f)


class Oracle(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Understand any cituation with these oracle commands,\nbut don't take them too seriously """
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
        author = ctx.message.author

        if not question:
            return await ctx.send(f'What is your question {author.mention}?', delete_after=6)  # 

        if question.endswith("?") and question != "?":
            response = random.choice(ball_answers)

            e = discord.Embed(color=self.user_color)
            e.set_author(name=f"{author.display_name}'s question:", icon_url=author.avatar.url)
            e.description = f'```{question}```'
            e.add_field(name='\N{BILLIARDS} answer:', value=f'```css\n{response}```')
            e.set_footer(text=f"ADVICE: Don't take this too seriously | {date.today()}")

            try:
                return await ctx.send(embed=e)
            except discord.HTTPException:
                await ctx.send(f'\N{BILLIARDS} answer: ```css\n{response}```')

        else:
            await ctx.send(f"*{question}* doesn't look like a yes/no question.", delete_after=6)

    # +------------------------------------------------------------+
    # |            Prediction command: TAROT                       |
    # +------------------------------------------------------------+
    @commands.group(invoke_without_command=True, descriptions='3 cards spread reading', no_pm=True)
    async def tarot(self, ctx):
        """ Basic Tarot spread
        Usage:
        {prefix}tarot reading
        """
        try:
            i = await ctx.send("☺️ Please relax and focus on your question...")
            await asyncio.sleep(3)
            
            await i.edit(content="👃 Inhale deeply through your nose...")
            await asyncio.sleep(6)
            
            await i.edit(content="👄 Exhale fully through your mouth...")
            await asyncio.sleep(6)
            
            last = f"When you feel ready, type:\n**`{ctx.prefix}tarot reading`**\n\nI will shuffle the cards and pick three for you."
            return await i.edit(content=last, delete_after=23)
        
        except Exception as e:
            return await ctx.send(f'```py\n{e}```', delete_after=69)

    @tarot.command(no_pm=True)
    async def reading(self, ctx, *, question: str = None):
        """ 3 cards spread reading """
        u = ctx.author
        deck = 'https://i.imgur.com/rUAjxYx.png'

        try:
            s = await ctx.send(f"Allow me to shuffle my Tarot deck... {u.display_name}")
            await ctx.channel.typing()
            await asyncio.sleep(7)

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
            e.set_author(name=f'Interpretation for {u.display_name}', icon_url=u.avatar.url)
            e.set_thumbnail(url=deck)
            e.set_author(name=f'{u.name} | {u.display_name} | {u.id}')

            e.add_field(name='Situation As It Is',
                        value=f'{first}\n{random.choice(card_deck)}\n', inline=False)
            e.add_field(name='Course of Action to be Taken',
                        value=f'{second}\n{random.choice(card_deck)}\n', inline=False)
            e.add_field(name='New Situation that Will Evolve',
                        value=f'{third}\n{random.choice(card_deck)}\n', inline=False)
            e.set_footer(text=f"Three Card spread reading | {date.today()}", icon_url=deck)

            await s.edit(content=None, embed=e)

        except discord.Forbidden:
            await ctx.send('I need embed perms in this channel to send the full result.', delete_after=5)

    # +------------------------------------------------------------+
    # |            Prediction command: iCHING                      |
    # +------------------------------------------------------------+
    @commands.command(aliases=['crystalball', 'oracle', 'i-ching'], no_pm=True)
    async def iching(self, ctx, *, question: str = None):
        """ Ancient Oracle prediction
        Based on the ancient divination I Ching oracle,
        [use it as a guide]
        
        Usage:
        {prefix}oracle [yes/no question?]
        """
        iching = 'http://i.imgur.com/biEvXBN.png'
        u = ctx.message.author
        p = ctx.invoked_with

        if question is None:
            return await ctx.send('You have to ask a yes/no question to use this command.', delete_after=23)

        if question.endswith('?') and question != '?':
            try:
                _wait = f'Allow me to shuffle 3 ancient Chinese coins to answer your question... **{u.display_name}**'
                _result = await ctx.send(_wait)
                await ctx.channel.typing()
                await asyncio.sleep(7)
                
                e = discord.Embed(colour=discord.Colour(0xc5b358))
                e.set_thumbnail(url=iching)
                e.set_footer(text=f"Ancient Oracle's inspiration | {date.today()}", icon_url=iching)
                e.set_author(name=f'{p} interpretation for {u.display_name}', icon_url=u.avatar.url)
                e.description = f'Meditation:\n{random.choice(oracle_answer)}'
                return await _result.edit(content=None, embed=e)
            except discord.Forbidden:
                pass

        else:
            msg = f"**{question}** doesn't look like a yes/no question."
            return await ctx.send(msg, delete_after=8)


    # +--------------------------new-------------------------------+
    # |         Prediction command: FUTHARK RUNES                  |
    # +------------------------------------------------------------+
    @commands.command(aliases=['futhark', 'runes'], description='draw a rune for meaning', no_pm=True)
    async def rune(self, ctx, *, query: str = None):
        """ 𝔼𝕝𝕕𝕖𝕣 𝔽𝕦𝕥𝕙𝕒𝕣𝕜 𝕍𝕚𝕜𝕚𝕟𝕘 ℝ𝕦𝕟𝕖𝕤
        A very old divination system to bring clarity to your day,
        [use it as a guide]
        
        Usage:
        {prefix}rune [yes/no question?]
        """
        u = ctx.message.author
        
        try:
            await ctx.channel.typing()
            await asyncio.sleep(11)
        except discord.Forbidden:
            pass

        _runes_desc = 'The Futhark Runes represent various aspects of the human experience, ' \
              'from health and wealth to relationships and the divine. Each Rune ' \
              'embodies a natural force, or energy. These Runes have three sets of ' \
              'eight letters:\nFreyr’s aett in Magenta.\nHeimdall’s aett in Yellow.\nTyr’s ' \
              'aett in Cyan.'
        rune = random.choice(runes_list)
        rune_draw = random.choice(list(rune['rune_draw'].keys()))
        r_meaning = rune['rune_draw'][rune_draw]
        #  in case the meaning of the Rune is larger than 1000 characters, we drop the excess...
        truncated_rune = r_meaning[:1000] + '...' if len(r_meaning) > 1000 else r_meaning

        e = discord.Embed(
            title=f'🧿 {rune_draw} draw meaning:',
            description=truncated_rune,
            color=int(rune['colour'], 16),  # base of 16 to convert the hexadecimal str to an int
            timestamp=datetime.utcnow()
        )
        e.set_author(name='𝔼𝕝𝕕𝕖𝕣 𝔽𝕦𝕥𝕙𝕒𝕣𝕜 𝕍𝕚𝕜𝕚𝕟𝕘 ℝ𝕦𝕟𝕖𝕤', icon_url=rune['rune_img'])
        #  e.set_thumbnail(url=rune['rune_img'])
        #  e.set_image(url='img_url.png')
        if query is None:
            e.set_footer(text='Use for guidance only!!')
        if query is not None:
            e.add_field(name=f'**{u.display_name}** asked:', value=f'{query}', inline=False)
            e.set_footer(text='Use for guidance only!!', icon_url=u.avatar.url)

        e.add_field(name='Interpretation:', value=f'>>> {_runes_desc}', inline=False)

        try:
            await ctx.send(embed=e)
        except Exception as e:
            await ctx.send(f'An error occurred:\n\n```py\n{e}```', delete_after=23)


async def setup(bot):
    await bot.add_cog(Oracle(bot))
