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

import discord, math, operator

from discord.ext import commands
from pyparsing import (
    Literal, CaselessLiteral, Word, Combine, Group, Optional, ZeroOrMore, Forward, nums, alphas, oneOf
)

class NumericStringParserForPython3:
    """
    A safe mathematical expression parser using pyparsing.
    """
    def pushFirst(self, strg, loc, toks):
        self.exprStack.append(toks[0])

    def pushUMinus(self, strg, loc, toks):
        if toks and toks[0] == '-':
            self.exprStack.append('unary -')

    def __init__(self):
        point = Literal(".")
        e = CaselessLiteral("E")
        fnumber = Combine(Word("+-" + nums, nums) +
                   Optional(point + Optional(Word(nums))) +
                   Optional(e + Word("+-" + nums, nums)))
        ident = Word(alphas, alphas + nums + "_$")
        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        pi = CaselessLiteral("PI")
        expr = Forward()
        atom = ((Optional(oneOf("- +")) +
                (pi | e | fnumber | ident + lpar + expr + rpar).setParseAction(self.pushFirst)) | \
               Optional(oneOf("- +")) + Group(lpar + expr + rpar))
        factor = Forward()
        factor << atom + ZeroOrMore((expop + factor).setParseAction(self.pushFirst))
        term = factor + ZeroOrMore((multop + factor).setParseAction(self.pushFirst))
        expr << term + ZeroOrMore((addop + term).setParseAction(self.pushFirst))
        self.bnf = expr
        self.opn = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "^": operator.pow
        }
        self.fn = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "abs": abs,
            "trunc": lambda a: int(a),
            "round": round,
            "sgn": lambda a: abs(a) > 1e-12 and (1 if a > 0 else -1) or 0
        }

    def evaluateStack(self, s):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluateStack(s)
        if op in "+-*/^":
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi
        elif op == "E":
            return math.e
        elif op in self.fn:
            return self.fn[op](self.evaluateStack(s))
        elif op[0].isalpha():
            return 0
        else:
            return float(op)

    def eval(self, num_string, parseAll=True):
        self.exprStack = []
        results = self.bnf.parseString(num_string, parseAll)
        return self.evaluateStack(self.exprStack[:])


class Calculator(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ powerful calculator commands """
    def __init__(self, bot):
        self.bot = bot
        self.nsp = NumericStringParserForPython3()
        self.user_color = discord.Colour(0xed791d)  # orange
        self.mod_color = discord.Colour(0x7289da)  # blurple

    @commands.command(description='Scientific calculator', aliases=['calculate', 'maths'])
    async def calc(self, ctx, *, formulas: str = None):
        """ ✔ Do some math """
        if formulas is None:
            msg = f'Usage: `{ctx.prefix}{ctx.invoked_with} [any Maths formula]`'
            return await ctx.send(msg, delete_after=23)

        # Replace most common words and symbols with their mathematical equivalents
        replacements = {
            ',': '', 'x': '*', 'minus': '-', 'plus': '+', 'into': '/', 'sub': '-',
            'pi': 'PI', 'π': 'PI', 'divide': '/', 'multiply': '*', 'add': '+',
            'div': '/', 'mult': '*', 'mul': '*', '÷': '/', '  ': ' ', '   ': ' '
        }
        formula = formulas
        for old, new in replacements.items():
            formula = formula.replace(old, new)

        try:
            answer = self.nsp.eval(formula)
        except Exception as e:
            # Provide informative error message
            msg = f'\N{THINKING FACE} Invalid input: `{formula}`\nError: {str(e)}'
            e = discord.Embed(color=self.user_color)
            e.description = f'\u200B{msg}'
            e.add_field(name='Examples', value="`2 + 2`, `3 * 4`, `sin(90)`, `pi * 2`", inline=False)
            return await ctx.send(embed=e, delete_after=23)

        # Correct input prints correct answer
        success = round(answer, 2)

        e = discord.Embed(color=self.user_color)
        e.add_field(name='Input:', value=f'```py\n{formula}```', inline=True)
        e.add_field(name='Result:', value=f'```css\n{success}```', inline=True)
        e.set_footer(text='Calculated using pyparsing')

        try:
            await ctx.send(embed=e)
        except discord.Forbidden:  # FORBIDDEN (status code: 403): Missing Permissions
            await ctx.send(f'```rust\n>Input: {formula}\nResult: {success}```')


async def setup(bot):
    await bot.add_cog(Calculator(bot))
        
