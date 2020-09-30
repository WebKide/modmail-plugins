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

import discord, random
from discord.ext import commands


class OnMessage(commands.Cog):
    """ (∩｀-´)⊃━☆ﾟ.*･｡ﾟ non-commands, bot responds to specific text in channel """
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # => Only respond with a 33% chance
        #if random.randint(1, 3) != 1:
        #    return


        if message.content.startswith('I am '):
            hello = random.choice(['Hello ', 'Hi there ', 'Howdy '])
            iam = f'I am {bot.user.mention}<:bot_tag:729987217396727868>, pleased to meet you.'  # upload the BOT emoji as :bot_tag: in your Discord guild
            msg = message.content[5:]
            await message.channel.send(f'{hello}' + f'*{msg}*' + f', {iam}')

def setup(bot):
    bot.add_cog(OnMessage(bot))
