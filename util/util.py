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
        try:
            memory_usage = bot.process.memory_full_info().uss / 1024**2
            cpu_usage = bot.process.cpu_percent() / psutil.cpu_count()
            
            cpu = f'CPU Usage:  {cpu_usage:.2f}% CPU processing'
            ram = f'RAM Usage:  {memory_usage:.2f} MiB of memory'
            
            result = f'{cpu}\n{ram}'
            await ctx.send(result)
        except Exception as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(Util(bot))
    
