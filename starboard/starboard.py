"""
MIT License
Copyright (c) 2023-2025 WebKide [d.id @323578534763298816]
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
    """Starboard system that reposts popular messages"""
    def __init__(self, bot):
        self.bot = bot
        self.star_emoji = '⭐'
        self.star_count = 1  # Minimum stars required
        self.starboard_channels = {}  # Cache of guild_id: channel_id mappings

    async def ensure_starboard_channel(self, guild):
        """Find or create the starboard channel in the given guild"""
        # Try to find existing starboard channel
        starboard_channel = discord.utils.get(guild.text_channels, name="starboard")
        
        if starboard_channel is None:
            # Create the channel if it doesn't exist
            try:
                starboard_channel = await guild.create_text_channel(
                    "starboard",
                    reason="Automatic starboard channel creation",
                    position=0  # Puts it at the top of the channel list
                )
                # Set default permissions
                await starboard_channel.set_permissions(
                    guild.default_role,
                    send_messages=False,
                    add_reactions=True,
                    read_message_history=True
                )
                await starboard_channel.send("⭐ **Welcome to the starboard!** ⭐\n"
                                           "Messages that get enough star reactions will appear here.")
            except discord.Forbidden:
                raise commands.BotMissingPermissions(["manage_channels"])
        
        return starboard_channel

    async def get_star_reaction(self, message):
        """Helper to get the star reaction from a message"""
        for reaction in message.reactions:
            if str(reaction.emoji) == self.star_emoji:
                return reaction
        return None

    def create_starboard_embed(self, message):
        """Create an embed for the starboard"""
        embed = discord.Embed(
            description=message.content,
            color=discord.Color.gold(),
            timestamp=message.created_at
        )
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url
        )
        embed.add_field(name="Original", value=f"[Jump!]({message.jump_url})")
        embed.add_field(name="Stars", value=f"1{self.star_emoji}")
        embed.set_footer(text=f"Starboard ID: {message.id}")
        
        if message.attachments:
            # Use first image if available
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    embed.set_image(url=attachment.url)
                    break
        
        return embed

    async def update_starboard_message(self, starboard_message, star_count):
        """Update an existing starboard message"""
        embed = starboard_message.embeds[0]
        embed.set_field_at(1, name="Stars", value=f"{star_count}{self.star_emoji}")
        await starboard_message.edit(embed=embed)

    async def find_starboard_message(self, channel, original_message_id):
        """Find existing starboard message for a given original message"""
        async for message in channel.history(limit=200):
            if message.embeds and message.embeds[0].footer.text == f"Starboard ID: {original_message_id}":
                return message
        return None

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle when a reaction is added"""
        # Ignore if not our star emoji or in DMs
        if str(payload.emoji) != self.star_emoji or not payload.guild_id:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
            
        # Get or create starboard channel
        try:
            starboard_channel = await self.ensure_starboard_channel(guild)
            self.starboard_channels[guild.id] = starboard_channel.id
        except commands.BotMissingPermissions:
            return
            
        # Ignore if reaction is in starboard channel
        if payload.channel_id == starboard_channel.id:
            return
            
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
            
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
            
        # Ignore bot's own reactions or self-starring
        if payload.user_id == message.author.id or payload.user_id == self.bot.user.id:
            return
            
        star_reaction = await self.get_star_reaction(message)
        if not star_reaction or star_reaction.count < self.star_count:
            return
            
        # Check if message is already in starboard
        existing_message = await self.find_starboard_message(starboard_channel, message.id)
        if existing_message:
            await self.update_starboard_message(existing_message, star_reaction.count)
            return
                
        # If not, create new starboard entry
        embed = self.create_starboard_embed(message)
        starboard_msg = await starboard_channel.send(embed=embed)
        await starboard_msg.add_reaction(self.star_emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle when a reaction is removed"""
        if str(payload.emoji) != self.star_emoji or not payload.guild_id:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
            
        # Get starboard channel from cache or find it
        starboard_channel = self.bot.get_channel(self.starboard_channels.get(guild.id))
        if not starboard_channel:
            starboard_channel = discord.utils.get(guild.text_channels, name="starboard")
            if not starboard_channel:
                return
            self.starboard_channels[guild.id] = starboard_channel.id
            
        if payload.channel_id == starboard_channel.id:
            return
            
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
            
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
            
        star_reaction = await self.get_star_reaction(message)
        existing_message = await self.find_starboard_message(starboard_channel, message.id)
        if not existing_message:
            return
            
        if star_reaction and star_reaction.count >= self.star_count:
            await self.update_starboard_message(existing_message, star_reaction.count)
        else:
            await existing_message.delete()

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        """Handle when a message is edited"""
        if not payload.guild_id:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
            
        # Get starboard channel from cache or find it
        starboard_channel = self.bot.get_channel(self.starboard_channels.get(guild.id))
        if not starboard_channel:
            starboard_channel = discord.utils.get(guild.text_channels, name="starboard")
            if not starboard_channel:
                return
            self.starboard_channels[guild.id] = starboard_channel.id
            
        channel = self.bot.get_channel(payload.channel_id)
        if not channel or channel.id == starboard_channel.id:
            return
            
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
            
        star_reaction = await self.get_star_reaction(message)
        if not star_reaction:
            return
            
        existing_message = await self.find_starboard_message(starboard_channel, message.id)
        if not existing_message:
            return
            
        # Update the starboard message with new content
        embed = self.create_starboard_embed(message)
        embed.set_field_at(1, name="Stars", value=f"{star_reaction.count}{self.star_emoji}")
        await existing_message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Starboard(bot))
    
