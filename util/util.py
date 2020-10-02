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

import psutil, discord, textwrap, traceback

from discord.ext import commands


class Util(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Check various Bot's env stats """
    def __init__(self, bot):
        self.bot = bot
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange

    # +------------------------------------------------------------+
    # |                        UTIL                                |
    # +------------------------------------------------------------+
    @commands.command(description="Bot's enviroment stats", no_pm=True)
    async def util(self, ctx):
        """ Show Bot's env stats """
        pp = psutil.Process()
        x = psutil.virtual_memory()
        
        cpu_u = pp.cpu_percent() / psutil.cpu_count()
		m_us = pp.memory_full_info().uss / 1024**2
		m_pe = pp.memory_percent()
        
		mt = x.total / 1024**2
		mf = x.free / 1024**2
		ma = x.active / 1024**2
		mu = x.used / 1024**2
		mv = x.available / 1024**2
		mc = x.cached / 1024**2
        
		c = f'CPU Usage:  {cpu_u:.2f}% CPU processing'
		r = f'RAM Usage:  {m_us:.2f} MiB of memory'
		p = f'RAM Percentage:  {m_pe:.2f}% MiB'
		q = f'Total Memory:  {mt:.2f} MiB'
		w = f'Free Memory:  {mf:.2f} MiB'
		e = f'Active Memory:  {ma:.2f} MiB'
		t = f'Used Memory:  {mu:.2f} MiB'
		y = f'Available Memory:  {mv:.2f} MiB'
		u = f'Cached Memory:  {mc:.2f} MiB'
        
		result = f'@_Geek(stats, bot):\n\n{c}\n{r}\n{p}\n\n{q}\n{w}\n{e}\n{t}\n{y}\n{u}'
        
		THRESHOLD = 100 * 1024 * 1024  # 100MB

		try:
		    await ctx.send(f'```py\n{result}```')
		    if x.available <= THRESHOLD:
		        await ctx.send('**`SYSTEM WARNING!`**')
		    else:
		        pass # silently
		except Exception as e:
		    await ctx.send(f'```py\n{e}```')


def setup(bot):
    bot.add_cog(Util(bot))
    
