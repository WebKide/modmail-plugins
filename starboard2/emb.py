import discord
from discord.embeds import EmptyEmbed


class CustomEmbeds:

    @classmethod
    def starboard(cls, message, **kwargs):
        title = kwargs.get('title', EmptyEmbed)
        link = f'https://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'
        
        description = kwargs.get('description', f'{message.content}\n [Jump To]({link})')
        
        url = kwargs.get('url', EmptyEmbed)
        color = kwargs.get('color', 13103696)
        author = kwargs.get('author', ':star: Starboard :star:')

        embed = discord.Embed(color=color, description=description)
        embed.set_footer(text=f"Author: {message.author}", icon_url=message.author.avatar_url)
        return embed
