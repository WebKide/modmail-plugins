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
from chatterbot import ChatBot as cb
from chatterbot.trainers import ChatterBotCorpusTrainer as cbt

_chatterbot_channel_id = 761449153447985162


class ChatterBot(commands.Cog):
    """ (∩｀-´)⊃━☆ﾟ.*･｡ﾟ dafuq is this? """
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = bot.get_channel(_chatterbot_channel_id)
        self.chatbot = cb('ok bot ')
        self.trainer = cbt(self.chatbot)
        self.training = self.trainer.train('chatterbot.corpus.english.greetings', 'chatterbot.corpus.english.conversations')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message not in self.channel_id:
            return
        
        if message.author.bot:
            return
        
        msg = message.content.lower().replace('*', '').replace(',', ' ').replace('.', ' ').replace('_', ' ').replace('  ', '')
        # author message content now in lowercase and clean
        
        if msg.startswith('ok bot '):
            response = self.chatbot.get_response(msg)
            if (len(response) <= 1039):
                await message.channel.send(response)
            if (len(response) > 1040):
                cropped = response[:1008]
                await message.channel.send(f'{cropped}...')
            else:
                _confused = ['I do not understand.', 'Sorry, can you repeat?', 'Pardon me?']
                await message.channel.send(f'random.choice(_confused)')

def setup(bot):
    bot.add_cog(ChatterBot(bot))
    
