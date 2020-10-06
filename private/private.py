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

import discord, traceback, random

from datetime import datetime as t
from pytz import timezone as z
from discord.ext import commands

_mods = [('ﾠ ﾠ#1502', 323578534763298816), ('DKD', 358420835108913153), ('VDD', 723061140816527412)]


class Private(commands.Cog):
    """─=≡Σ(つಠ益ಠ)つ this is a private cog for my personal discord guild, so it won't work for yours! """
    def __init__(self, bot):
        self.bot = bot

    # +------------------------------------------------------------+
    # |                 PUSH-NOTIFICATION                          |
    # +------------------------------------------------------------+
    @commands.command(description='Personal Guild command', no_pm=True, aliases=['notification', 'push', 'poke', 'everyone'])
    async def nudge(self, ctx, *, unique_event: str = None):
        """ ─=≡Σ(つಠ益ಠ)つ command to send a Push-notification reminder """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if ctx.author.id not in (mod[1] for mod in _mods):
            return

        u = ctx.message.author.mention
        channel =  ctx.channel or ctx.message.channel

        if isinstance(channel, discord.TextChannel):
            try:
                channel_topic = channel.topic.replace('\n', '— ').split('—')[-1:]
                x = t.now(z('Asia/Calcutta')).strftime(f'%A %B %d')
                i =  '\U0001f538'
                g = ctx.message.guild
                if unique_event is not None:
                    v = f" to gather together for the celebration of **{unique_event}**."
                else:
                    v = random.choice([
                        " to continue with yesterday's topic.",
                        " where we'll pick up from yesterday's topic.",
                        " where we'll continue from where we left off yesterday.",
                        " to partake in the continuation of yesterday's topic."
                    ])
                m = f"{i} {str(x)} (IST) is a perfect day to listen to the **{g}** podcast{v}\n{''.join(channel_topic)}"
                _msg = m.replace('1 ', '1ˢᵗ ').replace('2 ', '2ⁿᵈ ')\
                        .replace('3 ', '3ʳᵈ ').replace('4 ', '4ᵗʰ ')\
                        .replace('5 ', '5ᵗʰ ').replace('6 ', '6ᵗʰ ')\
                        .replace('7 ', '7ᵗʰ ').replace('8 ', '8ᵗʰ ')\
                        .replace('9 ', '9ᵗʰ ').replace('0 ', '0ᵗʰ ')
                await ctx.send(_msg)
            except Exception as e:
                error_msg = f"{u}, update this channel's Topic for this `command` to work!\n\n`{e}`\n\n"
                help_msg = "Tip: check other channel's Topics to get an idea of how to format their content."
                await ctx.send(error_msg + help_msg, delete_after=23)
        else:
            pass


def setup(bot):
    bot.add_cog(Private(bot))
    
