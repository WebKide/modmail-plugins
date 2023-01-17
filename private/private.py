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

import discord, requests, traceback, aiohttp, random, asyncio

from datetime import datetime as t
from pytz import timezone as z
from bs4 import BeautifulSoup, SoupStrainer
from discord.ext import commands


class Private(commands.Cog):
    """─=≡Σ(つಠ益ಠ)つ private cog for my personal discord guild, it won't work on yours! """
    def __init__(self, bot):
        self.bot = bot
        self.mods = [
            ('null', 323578534763298816), ('DKD', 358420835108913153), ('herr', 439734567197474816),
            ('TDd', 468747865351520257), ('alt', 324040201225633794), ('bvvm', 358433182304960513)
        ]

    # +------------------------------------------------------------+
    # |                 PUSH-NOTIFICATION                          |
    # +------------------------------------------------------------+
    @commands.command(description='Personal Guild cmd', aliases=['poke', 'push', 'notification'], no_pm=True)
    async def nudge(self, ctx, *, _event_today: str = None):
        """
        ─=≡Σ(つಠ益ಠ)つ command to send a Push-notification in text-channel
        
        **Usage:**
        {prefix}poke
        {prefix}nudge [event or celebration]
        {prefix}nudge extra [recorded podcast]
        """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if ctx.author.id not in (mod[1] for mod in self.mods):
            return

        channel =  ctx.channel or ctx.message.channel
        err_m = f"{ctx.message.author.mention}, update this channel's **Topic**.\n\n" \
                f"**Tip:** check other channel's Topics to get an idea of how to format it here."

        if isinstance(channel, discord.TextChannel):
            if not channel.topic:
                return await ctx.send(err_m, delete_after=23)

            if '—' in channel.topic:
                c_topic = channel.topic.replace('\n', '— ').split('—')[-1:]

                # FIRST | Date and times
                i = f":flag_in: | {str(t.now(z('Asia/Calcutta')).strftime(f'%A %b %d, **%H:**%M:%S'))} `(IST)`\n" \
                    f":flag_gb: | {str(t.now(z('Europe/London')).strftime(f'%A %b %d, **%H:**%M:%S'))} `(BST)`\n" \
                    f":flag_us: | {str(t.now(z('America/New_York')).strftime(f'%A %b %d, **%H:**%M:%S'))} `(EST)`\n" \
                    f":flag_us: | {str(t.now(z('America/Los_Angeles')).strftime(f'%A %b %d, **%H:**%M:%S'))} `(PST)`\n" \
                    f":flag_bo: | {str(t.now(z('America/La_Paz')).strftime(f'%A %b %d, **%H:**%M:%S'))} `(BOT)`\n\n"

                date_fix = i.replace('11,', '11ᵗʰ,').replace('12,', '12ᵗʰ,').replace('13,', '13ᵗʰ,')\
                            .replace('1,', '1ˢᵗ,').replace('2,', '2ⁿᵈ,').replace('3,', '3ʳᵈ,').replace('4,', '4ᵗʰ,')\
                            .replace('5,', '5ᵗʰ,').replace('6,', '6ᵗʰ,').replace('7,', '7ᵗʰ,').replace('8,', '8ᵗʰ,')\
                            .replace('9,', '9ᵗʰ,').replace('0,', '0ᵗʰ,')

                # SECOND | Currently listening
                _welcome = random.choice([
                            f"{date_fix}\U0001f538 Welcome to the **{ctx.message.guild}** podcast",
                            f"{date_fix}\U0001f538 Hello and welcome to the **{ctx.message.guild}** podcast",
                            f"{date_fix}\U0001f538 This is the **{ctx.message.guild}** podcast",
                            f"{date_fix}\U0001f538 You are currently listening to the **{ctx.message.guild}** podcast",
                            f"{date_fix}\U0001f538 It is a beautiful day to listen to the **{ctx.message.guild}** podcast",
                            f"{date_fix}\U0001f538 You are listening to the **{ctx.message.guild}** podcast",
                            f"{date_fix}\U0001f538 Moving on you are listening to the **{ctx.message.guild}** podcast",
                            f"{date_fix}\U0001f538 It is a nice day to listen to the **{ctx.message.guild}** podcast",
                            f"{date_fix}\U0001f538 It's a perfect day to listen to the **{ctx.message.guild}** podcast"
                    ])

                # THIRD | if current Host cannot do the podcast
                if _event_today is not None and _event_today.startswith('extra'):
                    _what = _event_today.split(' ')[1:]
                    _together = f" where we come together for the purpose of listening to: **{' '.join(_what)}**"
                    _p = channel.topic.split('—')[-1]
                    _nudge_ping = _p.split()[0]

                    m = f"\u200b{_welcome}{_together}\n\n{_nudge_ping} join the Voice Channel in this Room."

                else:
                    # FOURTH | Alternate special event
                    if _event_today is not None:
                        h = random.choice(['for the celebration of', 'to observe', 'to honour'])
                        v = f' where we gather together {h} **{_event_today}**.'

                    # FIFTH | continuation of previous podcast
                    else:
                        v = random.choice([
                            " where we shall continue with our favourite topic of discussion.",
                            " where we'll pick up from yesterday's topic.",
                            " where we'll continue from where we left off on the last broadcast.",
                            " where we'll continue our immersion into our favourite topic.",
                            ", let's take part in the continuation of our ongoing discussion."
                        ])

                    m = f"\u200b{_welcome}{v}\n\n{''.join(c_topic)}"

                # SIXTH | completed message
                _nudge = await ctx.send(m)

                try:
                    await asyncio.sleep(3)
                    await _nudge.add_reaction('thankful:695101751707303998')
                except discord.HTTPException:
                    pass

            else:
                await ctx.send(err_m, delete_after=23)

    # +------------------------------------------------------------+
    # |              WEB ARTICLE TO HASTEBIN                       |
    # +------------------------------------------------------------+
    '''
    @commands.command(description='Personal Guild cmd', no_pm=True)
    async def bb(self, ctx, *, _page: str = None):
        """
        ─=≡Σ(つಠ益ಠ)つ command to retrieve website and upload text
        
        **Usage:**
        {prefix}bb [article-name]
        """
        if _page is None:
            return await ctx.send('write article name as it appears in search result', delete_after=23)
        
        _HEADERS = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR '
                               '2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8; '
                               'InfoPath.3; .NET4.0C; .NET4.0E) chromeframe/8.0.552.224',
                               'Accept-Language': 'en-us'}  # define headers to emulate a web browser
        query_url = 'https://bhaktabandhav.org/'
        base = 'https://hasteb.in'
        url = f"{query_url}{_page.replace(' ', '-')}"
        _web_page = requests.get(url, headers=_HEADERS)
        _section_content = SoupStrainer('div', class_ = 'entry-content')
        x = BeautifulSoup(_web_page.content, 'html.parser', parse_only=_section_content, from_encoding='utf-8').prettify()
        i = x.replace('</p>', '').replace('<p>', '').replace('<div class="entry-content">', url).replace('<br/>', '').replace('</div>', 'End of article.').replace('  ', '')
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(base + '/documents', data=i) as responce:
                    key = (await responce.json())['key']
            await ctx.send(f'<{base}/{key}>')
        except Exception as e:
            await ctx.send(f'```py\n{e}\n```', delete_after=23)
    '''

async def setup(bot):
    await bot.add_cog(Private(bot))
    

# @commands.has_any_role('Admin', 'Mod', 'DJ', 'Owner')
