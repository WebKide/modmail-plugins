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

import discord, random, wikipedia, os

from discord.ext import commands
from chatbot import Chat, register_call

_chatbotai_channel_id = 761306707313295391
_confused = [
            "I don't know about ",
            "I don't understand what you mean by ",
            "Seems that I cannot find anything about "
        ]


class ChatbotAI(commands.Cog):
    """ (∩｀-´)⊃━☆ﾟ.*･｡ﾟ dafuq is this? """
    def __init__(self, bot):
        self.bot = bot

    @register_call('whoIs')
    async def who_is(self, query, session_id='general'):
        try:
            return wikipedia.summary(query)
        except Exception:
            for new_query in wikipedia.search(query):
                try:
                    return wikipedia.summary(new_query)
                except Exception:
                    pass
        return random.choice(_confused) + query
        
    temp_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chatbotTemplate', 'chatbottemplate.template')
    chat = Chat(temp_file_path)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message not in _chatbotai_channel_id:
            return
        
        if message.author.bot:
            return
        
        msg = message.content.lower().replace('*', '').replace(',', ' ').replace('.', ' ').replace('_', ' ').replace('  ', '')
        # author message content now in lowercase and clean
        
        if msg.startswith('ok bot '):
            result = chat.respond(msg)
            if (len(result) <= 2048):
                await message.channel.send(result)
            else:
                cropped = result[:2000]
                await message.channel.send(f'{cropped}...')

def setup(bot):
    bot.add_cog(ChatbotAI(bot))
