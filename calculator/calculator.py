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


import discord, operator, re, ast

from discord.ext import commands
from sympy import pi, E, sin, cos, tan, Abs, Integer, sympify

class Calculator(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ powerful calculator command """
    def __init__(self, bot):
        self.bot = bot
        self.user_color = discord.Colour(0xed791d) ## orange
        self.mod_color = discord.Colour(0x7289da) ## blurple

    @commands.command(description='Scientific calculator', aliases=['calculate', 'maths'])
    async def calc(self, ctx, *, formulas: str=None):
        person = ctx.message.author
        if formulas is None:
            msg = f'\u200BUsage: `{ctx.prefix}{ctx.invoked_with} [any Maths formula]`'
            return await ctx.send(msg, delete_after=9)

        # replace some specific strings
        formulas = formulas.replace(',', '').replace('x', '*') \
            .replace('minus', '-').replace('plus', '+').replace('into', '*') \
            .replace('sub', '-').replace('pi', '3.141592653589793') \
            .replace('π', '3.141592653589793').replace('divide', '/') \
            .replace('multiply', '*').replace('add', '+').replace('div', '/') \
            .replace('mult', '*').replace('mul', '*').replace('÷', '/') \
            .replace('  ', '').replace(' ', '').replace('\n', '')

        # define a regular expression to match only mathematical characters
        regex = re.compile('[^0-9+\-*/().]')
        # sanitize the input
        formulas = regex.sub('', formulas)

        try:
            node = ast.parse(formulas, mode='eval')
            fixed = ast.fix_missing_locations(node)
            compiled = compile(fixed, '<string>', 'eval')
            result = eval(compiled)

            formatted_result = '{:.2f}'.format(result)

        except Exception as e:
            return await ctx.send(f'```Error: {str(e)}```', delete_after=9)

        _answer = f'**```js\n​{formatted_result}\n```**'
        _name = f"Calculation for {person.display_name}'s"
        e = discord.Embed(title=_name, colour=self.user_color)
        e.description = description=f'```bf\n[{formulas}]```'
        e.add_field(name="\N{ABACUS} Round Answer:", value=_answer, inline=False)
        e.add_field(name="\N{ABACUS} Answer:", value=f'**```js\n​{result}\n```**', inline=False)
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Calculator(bot))
