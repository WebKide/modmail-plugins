import re

import discord
from discord.ext import commands


def calculate(expression):
    """Calculates the result of an arithmetic expression"""
    # Remove any whitespace from the expression
    expression = expression.replace(" ", "")
    # Create two stacks, one for operators and one for operands
    operators = []
    operands = []
    # Define the precedence of operators
    precedence = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}
    # Split the expression into tokens
    tokens = re.findall(r"\d+|\+|-|\*|/|\^|\(|\)", expression)
    # Loop through each token
    for token in tokens:
        # If the token is an operand, append it to the operands stack
        if token.isdigit():
            operands.append(int(token))
        # If the token is an operator
        elif token in precedence:
            # Pop operators from the stack until the stack is empty or the top operator has lower precedence
            while operators and operators[-1] != "(" and precedence[token] <= precedence[operators[-1]]:
                operator = operators.pop()
                # Perform the operation and append the result to the operands stack
                right_operand = operands.pop()
                left_operand = operands.pop()
                result = apply_operator(left_operand, right_operand, operator)
                operands.append(result)
            # Push the operator onto the operators stack
            operators.append(token)
        # If the token is a left parenthesis, push it onto the operators stack
        elif token == "(":
            operators.append(token)
        # If the token is a right parenthesis
        elif token == ")":
            # Pop operators from the stack and perform the operations until a left parenthesis is found
            while operators[-1] != "(":
                operator = operators.pop()
                right_operand = operands.pop()
                left_operand = operands.pop()
                result = apply_operator(left_operand, right_operand, operator)
                operands.append(result)
            # Pop the left parenthesis from the stack
            operators.pop()
    # Perform any remaining operations
    while operators:
        operator = operators.pop()
        right_operand = operands.pop()
        left_operand = operands.pop()
        result = apply_operator(left_operand, right_operand, operator)
        operands.append(result)
    # The final result is the only element in the operands stack
    return operands[0]

def apply_operator(left_operand, right_operand, operator):
    """Applies an operator to two operands"""
    if operator == "+":
        return left_operand + right_operand
    elif operator == "-":
        return left_operand - right_operand
    elif operator == "*":
        return left_operand * right_operand
    elif operator == "/":
        return left_operand / right_operand
    elif operator == "^":
        return left_operand ** right_operand


class Calculator(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ PEMDAS calculator """
    def __init__(self, bot):
        self.bot = bot
        self.user_color = discord.Colour(0xed791d)

    @commands.command(description='Calculator', no_pm=True)
    async def calc(self, ctx, *, formulas: str=None):
        person = ctx.message.author
        if formulas is None:
            msg = f'\u200BUsage: `{ctx.prefix}{ctx.invoked_with} [any Maths formula]`'
            return await ctx.send(msg, delete_after=9)

        # replace some specific strings
        formula = formulas.replace(',', '').replace('x', '*').replace('minus', '-').replace('plus', '+') \
            .replace('into', '*').replace('sub', '-').replace('pi', '3.141592653589793') \
            .replace('π', '3.141592653589793').replace('divide', '/').replace('multiply', '*') \
            .replace('add', '+').replace('div', '/').replace('mult', '*').replace('mul', '*') \
            .replace('÷', '/').replace('  ', '').replace(' ', '').replace('\n', '')

        try:
            # parse the formula
            pemdas_result = '{:.2f}'.format(calculate(formula))

        except Exception as e:
            return await ctx.send(f'```Error: {str(e)}```', delete_after=9)

        e = discord.Embed(title=f"Calculation for {person.display_name}'s", colour=self.user_color)
        e.description = description=f'```bf\n[{formula}]```'
        e.add_field(name="\N{ABACUS} Answer:", value=f'**```js\n​{formula}\n```**', inline=False)
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Calculator(bot))
