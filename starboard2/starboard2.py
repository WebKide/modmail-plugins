"""
MIT License
Copyright (c) 2023 WebKide [d.id @323578534763298816]
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

from discord.ext import commands

class Starboard(commands.Cog):
    """─=≡Σ(つಠ益ಠ)つ private cog for my personal discord guild, it won't work on yours! """
    def __init__(self, bot):
        self.bot = bot
        self.star_emoji = '⭐'
        self.star_count = 1
        self.guild_id = 328341202103435264 # ID of my Guild
        self.starboard_channel_id = 729093473487028254 # ID of my Starboard channel


    # +------------------------------------------------------------+
    # |              ADD A MESSAGE TO STARBOARD                    |
    # +------------------------------------------------------------+
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name != '⭐': # replace "⭐" with your star emoji name
            return

        if payload.channel_id == self.starboard_channel_id:
            return

        if self.starboard_channel_id is None:
            return

        if payload.channel_id == self.starboard_channel_id and payload.emoji.name == self.star_emoji:
            guild = self.bot.get_guild(payload.guild_id)
            if guild is None:
                return
            member = guild.get_member(payload.user_id)
            if member is None:
                return
            message = self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if message.author == member:
                return
            starboard_channel = guild.get_channel(self.starboard_channel_id)
            starboard_message_id = await self.check_starboard(message)
            if starboard_message_id is None:
                em = self.create_embed(message, member)
                starboard_message = starboard_channel.send(embed=em)
                await starboard_message.add_reaction(self.star_emoji)
                await self.add_starboard_message(message, starboard_message.id)
            else:
                starboard_message = starboard_channel.fetch_message(starboard_message_id)
                self.update_embed(starboard_message, message)

        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return

        message = await channel.fetch_message(payload.message_id)
        if message is None:
            return

        if payload.user_id == self.bot.user.id:
            return

        if not isinstance(channel, discord.TextChannel):
            return

        if not message.reactions:
            return

        starboard_channel = self.bot.get_channel(self.starboard_channel_id)
        if not isinstance(starboard_channel, discord.TextChannel):
            return

        star_reaction = None
        for reaction in message.reactions:
            if reaction.emoji == self.star_emoji:
                star_reaction = reaction
                break

        if star_reaction is None or star_reaction.count < self.star_count:
            return

        em = discord.Embed(description=message.content)
        em.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        em.add_field(name='Jump', value=f'[to the original!]({message.jump_url})')
        em.add_field(name='Stars', value=star_reaction.count)
        em.set_footer(text=f"Starboard ID: {message.id}")
        if message.attachments:
            em.set_image(url=message.attachments[0].url)

        await starboard_channel.send(embed=em)

    # +------------------------------------------------------------+
    # |              DELETE STARBOARD MESSAGE                      |
    # +------------------------------------------------------------+
    async def on_raw_reaction_remove(payload):
        if payload.channel_id == self.starboard_channel_id:
            message_id = payload.message_id
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(message_id)
            if message.embeds:
                em = message.embeds[0]
                if em.footer.text.startswith("⭐"):
                    reactions = message.reactions
                    count = 0
                    for reaction in reactions:
                        if reaction.emoji == "⭐":
                            count = reaction.count
                            break
                    if count < self.star_count:
                        await message.delete()

    # +------------------------------------------------------------+
    # |                EDIT STARBOARD MESSAGE                      |
    # +------------------------------------------------------------+                
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        starboard_channel = self.bot.get_channel(self.starboard_channel_id)
        # Ignore edits made by the bot itself
        if message.author == bot.user:
            return

        if not isinstance(starboard_channel, discord.TextChannel):
            return

        try:
            starboard_message = starboard_channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        original_message_id = starboard_message.embeds[0].fields[0].value.split('/')[-1]
        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        message = await channel.fetch_message(original_message_id)
        if not message:
            return

        reactions = message.reactions
        star_reaction = None
        for reaction in reactions:
            if reaction.emoji == self.star_emoji:
                star_reaction = reaction
                break

        if not star_reaction:
            await starboard_message.delete()
            return

        if star_reaction.count < self.star_count:
            await starboard_message.delete()
            return

        # Check if there is already a message on the starboard for this message
        existing_message = None
        for m in await starboard_channel.history(limit=100).flatten():
            if m.embeds and m.embeds[0].footer.text == f"Starboard ID: {message.id}":
                existing_message = m
                break

        # If there's an existing message, update its star count and return
        if existing_message:
            em = existing_message.embeds[0]
            em.set_field_at(0, name="Stars", value=f"{star_reaction.count} ⭐")
            await existing_message.edit(embed=em)
            return

        # Otherwise, create a new starboard message
        em = discord.Embed(
            title=message.content,
            color=discord.Color.gold(),
            timestamp=message.created_at,
            url=message.jump_url,
        )
        em.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        em.set_footer(text=f"Starboard ID: {message.id}")
        em.add_field(name="Channel", value=message.channel.mention)
        em.add_field(name="Stars", value=f"{star_reaction.count} ⭐")
        if message.attachments:
            em.set_image(url=message.attachments[0].url)

        await starboard_channel.send(embed=em)

async def setup(bot):
    await bot.add_cog(Starboard(bot))
