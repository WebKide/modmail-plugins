"""
MIT License
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
import math
import operator
from sympy import pi, E, sin, cos, tan, Abs, Integer, sympify
from discord.ext import commands

class Calculator(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ powerful calculator commands """
    def __init__(self, bot):
        self.bot = bot
        self.user_color = discord.Colour(0xed791d) ## orange
        self.mod_color = discord.Colour(0x7289da) ## blurple

    @commands.command(description='Scientific calculator', aliases=['calculate', 'maths'])
    async def calc(self, ctx, *, formulas: str=None):
        person = ctx.message.author
        if formulas is None:
            msg = f'\u200BUsage: `{ctx.prefix}{ctx.invoked_with} [any Maths formula]`'
            return await ctx.send(msg, delete_after=23)

        formula = formulas.replace(',', '').replace('x', '*').replace('minus', '-').replace('plus', '+') \
            .replace('into', '/').replace('sub', '-').replace('pi', 'pi').replace('π', 'pi').replace('Pi', 'pi') \
            .replace('divide', '/').replace('multiply', '*').replace('add', '+').replace('div', '/') \
            .replace('mult', '*').replace('mul', '*').replace('÷', '/').replace('  ', '').replace(' ', '')

        try:
            result = sympify(formula).evalf()
            rounded_result = round(result, 2)
            formatted_result = "{:.2f}".format(rounded_result)
        except Exception as e:
            return await ctx.send(f'```Error: {str(e)}```', delete_after=9)

        em = discord.Embed(title=f"Calculator for {person.display_name}", colour=self.user_color, description=formulas)
        em.add_field(name="Answer", value=formatted_result, inline=False)
        await ctx.send(embed=em)


async def setup(bot):
    await bot.add_cog(Calculator(bot))
