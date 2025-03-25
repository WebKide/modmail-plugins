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

import discord
import asyncio
import re
import random
from datetime import datetime as t
from pytz import timezone as z
from discord.ext import commands

class Private(commands.Cog):
    """Private Discord.py plugin for managing notifications and announcements.
    - Includes rich multi-timezone formatting: IST/GMT/EST/PST/BOT.
    - Requires 'Admin', 'Mod', or 'Moderator' role to use.
    - Custom UNICODE ordinal indicators.
    - Optional custom 'extra' event support.
    - Dual-channel support to send in current channel or in General channel.
    - Pings @Attentive-Listeners role and adds custom guild reaction.
    - Provides error fallback messages.
    - Only works in my personal Guild.

    USAGE:
    !radhe — Standard announcement with rich-formatting
    !gaura extra <Festival of Ekādaśī> — Custom event with rich-formatting
    """
    def __init__(self, bot):
        self.bot = bot
        self.target_channel_id = 728320469119402004  # Fixed channel ID for 'gaura' notification 358429353966698500

    # +------------------------------------------------------------+
    # |                 PUSH-NOTIFICATION                          |
    # +------------------------------------------------------------+
    @commands.command(description='Deletes original command message and sends notification', aliases=['poke'], no_pm=True)
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    async def radhe(self, ctx, *, _event_today: str = None):
        """Send a push notification in the current channel"""
        await self._send_notification(ctx, ctx.channel, _event_today)

    @commands.command(description='Sends the push notification to the General channel', aliases=['nudge'], no_pm=True)
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    async def gaura(self, ctx, *, _event_today: str = None):
        """Send a push notification to the General channel"""
        target_channel = self.bot.get_channel(self.target_channel_id)
        if not target_channel:
            return await ctx.send("Couldn't find the target channel!", delete_after=10)
        await self._send_notification(ctx, target_channel, _event_today)

    async def _send_notification(self, ctx, channel, _event_today=None):
        """Shared notification sending logic"""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        _poke = f'<@&358429415417446411> || ⁱⁿᵛᵒᵏᵉᵈ ᵇʸ **{ctx.message.author.display_name}** ||'
        err_m = f"{ctx.message.author.mention}, update this channel's **Topic**.\n\n" \
                f"**Tip:** ask a Mod for help setting up this channel for the command to work."

        _TZ = {
            "IST": "Asia/Kolkata",
            "GMT": "Europe/London",
            "EST": "America/New_York",
            "PST": "America/Los_Angeles",
            "BOT": "America/La_Paz"
        }

        INTRO = [
            f'*Turn off and tune into* the **{ctx.message.guild}** Podcast, ',
            f'Bring auspiciousness to your day with the **{ctx.message.guild}** Podcast, ',
            f'Hello and welcome to the **{ctx.message.guild}** Podcast, ',
            f'It is a beautiful day to listen to the **{ctx.message.guild}** Podcast, ',
            f'It is a nice day to listen to the **{ctx.message.guild}** Podcast, ',
            f'Make your day succesfull by listening to the **{ctx.message.guild}** Podcast, ',
            f'This is the **{ctx.message.guild}** Podcast, ',
            f'Tune into the **{ctx.message.guild}** Podcast, ',
            f'Welcome to the **{ctx.message.guild}** Podcast, '
        ]

        TEACHINGS = [
            'our Rūpānuga Guru-varga',
            'our Vaiṣṇava Ācāryas',
            'the Śrī Gauḍīya Vaiṣṇavas'
        ]

        JOIN = [
            ', to delve deeper into',
            ', to explore and connect with',
            ', so that you can learn, grow, and connect personally on'
        ]

        OUTRO = [
            'So, let\'s dive into this valuable study together and learn about this wanderful process',
            'So, sit back, relax, and listen attentively as we embark on this spiritual journey together',
            'Without further ado, sit back, relax and, listen attentively',
            'Hold on to your chairs, and simply "lend us your ears"',
            'You\'ve been eagerly waiting for this, and so have we. Sit back, relax and, listen attentively'
        ]

        if isinstance(channel, discord.TextChannel):
            if not channel.topic:
                return await ctx.send(err_m, delete_after=23)

            if '—' in channel.topic:
                _host = channel.topic.split('—')[-1]
            else:
                _host = 'and speaker'

        def get_ordinal_suffix(num):
            if 11 <= num % 32 <= 13:
                suffix = 'ᵗʰ'
            else:
                suffix = {1: 'ˢᵗ', 2: 'ⁿᵈ', 3: 'ʳᵈ'}.get(num % 10, 'ᵗʰ')
            return suffix

        def get_t_str():
            t_str = []
            for code, tz_name in _TZ.items():
                tz = z(tz_name)
                t_now = t.now(tz)
                suffix = get_ordinal_suffix(t_now.day)
                flag_moji = f":flag_{code.lower().replace('ist', 'in').replace('gmt', 'gb').replace('est', 'us').replace('pst', 'us').replace('bot', 'bo')}:"
                
                date_str = t_now.strftime('**%H**:%M:%S, %A %b %d, %Y')
                date_str = date_str.replace(f"{t_now.day},", f"{t_now.day}{suffix},")
                
                t_str.append(f"{flag_moji}「{code}」{date_str}")
            return "\n".join(t_str)

        if _event_today is not None and _event_today.startswith('extra'):
            _what = ' '.join(_event_today.split(' ')[1:])
            _notif = 'https://cdn.discordapp.com/attachments/375179500604096512/1079876674235154442/flyerdesign_27022023_172353.png'
            em = discord.Embed(colour=discord.Colour(0xff7722), description=get_t_str())
            em.add_field(name='Attentive Listeners', value=_what, inline=False)
            em.set_thumbnail(url=_notif)
            em.set_footer(text='⇐ Join the Voice Channel NOW!!')
            message = await channel.send(content=_poke, embed=em)
        else:
            def _intro():
                intro_text = f'\u200b{random.choice(INTRO)}where we explore the teachings of {random.choice(TEACHINGS)}. Join our host {_host} for a thought-provoking discussion{random.choice(JOIN)} your spiritual journey throught the path of Rūpānuga Ujjvala Mādhurya-prema.\n\n{random.choice(OUTRO)}.'
                return intro_text.encode('utf-8').decode('utf-8')

            try:
                em = discord.Embed(colour=discord.Colour(0xff7722), description=get_t_str())
                em.add_field(name='Attentive Listeners', value=_intro(), inline=False)
                em.set_thumbnail(url='https://i.imgur.com/93A0Kdk.png')
                em.set_footer(text='⇐ Join the Voice Channel NOW!!')
                message = await channel.send(content=_poke, embed=em)
            except discord.Forbidden:
                _simple = f'{_poke}\n{get_t_str()}\n\n{_intro()}'
                message = await channel.send(_simple)

        try:
            await asyncio.sleep(2)
            await message.add_reaction('thankful:695101751707303998')
        except discord.HTTPException:
            pass

        # Send confirmation to original channel
        if channel.id != ctx.channel.id:
            await ctx.send(f"Notification sent to {channel.mention}!", delete_after=10)

async def setup(bot):
    await bot.add_cog(Private(bot))
    
