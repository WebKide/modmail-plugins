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

import discord, sympy

from discord.ext import commands


class Calculator(commands.Cog)::
    def __init__(self):
        self.exprStack = []
        self.ops = {
            "+" : sympy.Add,
            "-" : sympy.Subtract,
            "*" : sympy.Multiply,
            "/" : sympy.Divide,
            "^" : sympy.Pow,
            "sin": sympy.sin,
            "cos": sympy.cos,
            "tan": sympy.tan,
            "exp": sympy.exp,
            "log": sympy.log,
            "ln": sympy.ln
        }

    def evaluateStack(self, s):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluateStack(s)
        elif isinstance(op, sympy.Basic):
            return op
        elif op in self.ops:
            if op in ["sin", "cos", "tan", "exp", "ln"]:
                return self.ops[op](self.evaluateStack(s))
            elif op == "log":
                arg2 = self.evaluateStack(s)
                arg1 = self.evaluateStack(s)
                return self.ops[op](arg1, arg2)
            else:
                arg2 = self.evaluateStack(s)
                arg1 = self.evaluateStack(s)
                return self.ops[op](arg1, arg2)
        else:
            return sympy.S(op)

    def parse(self, num_string):
        self.exprStack=[]
        results = []
        for tok in num_string.split():
            if tok in self.ops:
                results.append(tok)
            elif tok == "pi":
                results.append(sympy.pi)
            elif tok == "e":
                results.append(sympy.E)
            else:
                results.append(tok)
        return results

    def eval(self, num_string):
        expr = self.parse(num_string)
        for tok in expr:
            if isinstance(tok, sympy.Basic):
                self.exprStack.append(tok)
            elif tok == 'unary -':
                self.exprStack.append(tok)
            elif tok in self.ops:
                numargs = self.ops[tok].nargs
                if numargs == 1:
                    self.exprStack.append(tok)
                elif numargs == 2:
                    self.exprStack.append(tok)
        return self.evaluateStack(self.exprStack[:])

    
    
    

class Calculator(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ powerful calculator commands """
    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot):
        self.bot = bot
        self.nsp=NumericStringParserForPython3()
        self.user_color = discord.Colour(0xed791d) ## orange
        self.mod_color = discord.Colour(0x7289da) ## blurple

    @commands.command(description='Scientific calculator', aliases=['calculate', 'maths'])
    async def calc(self, ctx, *, formulas: str=None):
        """ ✔ Do some math
        thanks to Paul McGuire's fourFn.py. """
        person = ctx.message.author
        if formulas is None:
            msg = f'\u200BUsage: `{ctx.prefix}{ctx.invoked_with} [any Maths formula]`'
            return await ctx.send(msg, delete_after=23)

        formula = formulas.replace(',', '').replace('x', '*').replace('minus', '-').replace('plus', '+') \
                    .replace('into', '/').replace('sub', '-').replace('pi', 'PI').replace('π', 'PI').replace('Pi', 'PI') \
                    .replace('divide', '/').replace('multiply', '*').replace('add', '+').replace('div', '/') \
                    .replace('mult', '*').replace('mul', '*').replace('÷', '/').replace('  ', ' ').replace(' ', '*')

        if formula == None:
            # How can it calculate an empty message? Reee!
            msg = f'\u200BUsage: `{ctx.prefix}{ctx.invoked_with} [any maths formula]`'
            e = discord.Embed(color=self.user_color)
            e.description = msg

            try:
                await ctx.send(embed=e, delete_after=23)
            except discord.HTTPException:
                await ctx.send(msg, delete_after=23)
            return

        try:
            answer=self.nsp.eval(formula)
        except:
            # If there's a problem in the input, show examples
            msg = f'\N{THINKING FACE} wrong {formula} input.\nTry any of these:'
            e = discord.Embed(color=self.user_color)
            e.description = f'\u200B{msg}'
            e.add_field(name='multiplication', value="`num` * `num`", inline=True)
            e.add_field(name='division', value="`num` / `num`", inline=True)
            e.add_field(name='addition', value="`num` + `num`", inline=True)
            e.add_field(name='rest', value="`num` - `num`", inline=True)
            e.add_field(name='exponential', value="`num` ^ `num`")
            e.add_field(name='integer', 
                        value="[`num` + `num` | `num` - `num`] `num` 0 `num`..`num` 9 `num` +")

            try:
                await ctx.send(embed=e, delete_after=23)
            except discord.HTTPException:
                await ctx.send(msg, delete_after=23)
            return

        # Correct input prints correct answer
        distance = self.bot or self.bot.message
        duration = f'Calculated in {distance.ws.latency * 1000:.2f} ms'
        success = round(answer, 2)

        e = discord.Embed(color=self.user_color)
        e.add_field(name='Input:', value=f'```py\n{formula}```', inline=True)
        e.add_field(name='Result:', value=f'```css\n{success}```', inline=True)
        e.set_footer(text=duration)

        try:
            await ctx.send(embed=e)
        except discord.Forbidden:  # FORBIDDEN (status code: 403): Missing Permissions
            await ctx.send(f'```rust\n>Input: {formula}\nResult: {success}```')
'''

async def setup(bot):
    await bot.add_cog(Calculator(bot))
