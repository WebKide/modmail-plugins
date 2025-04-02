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
import re
from discord.ext import commands

class Starboard(commands.Cog):
    """A fully automated, configurable Starboard system that highlights popular messages in your Discord server"""
    def __init__(self, bot):
        self.bot = bot
        self.starboard_channels = {}
        self._load_default_settings()

    def _load_default_settings(self):
        """Set default values before channel settings are loaded"""
        self.star_emoji = '⭐'
        self.star_count = 1
        self.ignored_channels = []  # channels that will be ignored and can be modified with command

    async def _load_channel_settings(self, channel):
        """Load settings from channel topic"""
        if not channel.topic:
            return
            
        # Extract emoji from topic
        emoji_match = re.search(r'default_emoji:(\S+)', channel.topic)
        if emoji_match:
            self.star_emoji = emoji_match.group(1)
            
        # Extract star count from topic
        count_match = re.search(r'default_count:(\d+)', channel.topic)
        if count_match:
            self.star_count = int(count_match.group(1))

    @commands.command(aliases=['setstars'], no_pm=True)
    @commands.has_permissions(manage_channels=True)
    async def starconfig(self, ctx, emoji: str = None, count: int = None):
        """Configure starboard settings
        
        Examples:
        ?starconfig ⭐ 5      - Set 5 stars required
        ?starconfig 🌟        - Just change emoji
        ?starconfig reset     - Reset to defaults
        """
        channel = await self.ensure_starboard_channel(ctx.guild)
        
        if emoji and str(emoji).lower() == 'reset':
            new_topic = "Starboard channel - Reset to defaults"
            self._load_default_settings()
            await channel.edit(topic=new_topic)
            return await ctx.send("✅ Reset starboard default reactions **(⭐ 1)**")
            
        # Build new topic string in Starboard channel
        parts = []
        if channel.topic and not channel.topic.startswith("Starboard channel"):
            parts.append(channel.topic.split('\n')[0])
            
        if emoji:
            parts.append(f"default_emoji:{emoji}")
            self.star_emoji = emoji
            
        if count:
            parts.append(f"default_count:{count}")
            self.star_count = count
            
        new_topic = "Starboard channel\n" + " ".join(parts)
        await channel.edit(topic=new_topic)
        
        # Show current settings
        settings = []
        if emoji:
            settings.append(f"Emoji: {self.star_emoji}")
        if count:
            settings.append(f"Required stars: {self.star_count}")
            
        await ctx.send(f"✅ Updated starboard settings: {' '.join(settings)}")

    async def ensure_starboard_channel(self, guild):
        """Find or create starboard channel and load settings"""
        channel = discord.utils.get(guild.text_channels, name="starboard")
        
        if not channel:
            # Create the channel
            channel = await guild.create_text_channel(
                "starboard",
                topic="Starboard channel\ndefault_emoji:⭐ default_count:1",
                reason="Automatic starboard creation",
                position=0
            )
            
            # Permissions for @everyone
            everyone_perms = discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,

                # Prevent misuse of the Starboard channel
                send_messages=False,
                create_public_threads=False,
                create_private_threads=False,
                send_messages_in_threads=False,
                embed_links=False,
                attach_files=False,
                add_reactions=False,
                use_external_emojis=False,
                use_external_stickers=False,
                manage_messages=False,
                manage_threads=False,
                manage_channels=False,
                manage_permissions=False
            )
            
            # Permissions for self.bot
            bot_member = guild.get_member(self.bot.user.id)
            bot_perms = discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,
                send_messages=True,
                manage_messages=True,
                embed_links=True,
                attach_files=True,
                use_external_emojis=True,
                manage_channels=True,
                manage_permissions=True
            )
            
            # Apply permissions
            await channel.set_permissions(guild.default_role, overwrite=everyone_perms)
            if bot_member:
                await channel.set_permissions(bot_member, overwrite=bot_perms)
            
            await channel.send("# ⭐ **Welcome to the Starboard!** ⭐\n\n"
                             "Messages that get enough star reactions will appear here.")
        
        await self._load_channel_settings(channel)
        self.starboard_channels[guild.id] = channel.id
        return channel
        
    async def get_star_reaction(self, message):
        """Helper to get the star reaction from a message"""
        for reaction in message.reactions:
            if str(reaction.emoji) == self.star_emoji:
                return reaction
        return None

    def create_starboard_embed(self, message):
        """Create an embed for the starboard that handles all content types"""
        embed = discord.Embed(
            description=message.content if message.content else None,
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

        # Handle attachments (images, videos, files)
        if message.attachments:
            first_attachment = message.attachments[0]
            if first_attachment.content_type:
                if first_attachment.content_type.startswith('image/'):
                    embed.set_image(url=first_attachment.url)
                elif first_attachment.content_type.startswith('video/'):
                    embed.add_field(name="Video", value=f"[Click to view]({first_attachment.url})")
                else:
                    embed.add_field(name="Attachment", value=f"[{first_attachment.filename}]({first_attachment.url})")

        # Handle embeds from the original message
        if message.embeds:
            for msg_embed in message.embeds:
                if msg_embed.image:
                    embed.set_image(url=msg_embed.image.url)
                if msg_embed.thumbnail:
                    embed.set_thumbnail(url=msg_embed.thumbnail.url)
                if msg_embed.description:
                    embed.description = (embed.description or "") + "\n\n" + msg_embed.description
                if msg_embed.fields:
                    for field in msg_embed.fields:
                        embed.add_field(name=field.name, value=field.value, inline=field.inline)

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
            
        try:
            starboard_channel = await self.ensure_starboard_channel(guild)
        except commands.BotMissingPermissions:
            return
            
        # Ignore reactions in starboard channel
        if payload.channel_id == starboard_channel.id:
            return
            
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
            
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
        except discord.Forbidden:
            return
        except discord.HTTPException:
            return
            
        # Ignore bot's own reactions or self-starring
        #if payload.user_id == message.author.id or payload.user_id == self.bot.user.id:
        #    return
            
        star_reaction = await self.get_star_reaction(message)
        if not star_reaction or star_reaction.count < self.star_count:
            return
            
        # Check if message is already in starboard
        existing_message = await self.find_starboard_message(starboard_channel, message.id)
        if existing_message:
            await self.update_starboard_message(existing_message, star_reaction.count)
            return
                
        # Create new starboard entry
        try:
            embed = self.create_starboard_embed(message)
            files = []
            
            # Handle all attachments (including non-image files)
            for attachment in message.attachments:
                if not attachment.is_spoiler() and attachment.size < 8_000_000:  # 8MB limit
                    try:
                        files.append(await attachment.to_file())
                    except:
                        continue  # Skip if we can't process the file
            
            # Send message with embed and files
            if files:
                # If we have multiple files, we need to handle them carefully
                # Discord allows up to 10 files per message, but we'll limit to 5 for safety
                for i in range(0, len(files), 5):
                    batch = files[i:i+5]
                    if i == 0:
                        # First batch includes the embed
                        starboard_msg = await starboard_channel.send(embed=embed, files=batch)
                    else:
                        # Subsequent batches are just files
                        await starboard_channel.send(files=batch)
            else:
                starboard_msg = await starboard_channel.send(embed=embed)
                
            await starboard_msg.add_reaction(self.star_emoji)
        except Exception as e:
            print(f"Error creating starboard entry: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle when a reaction is removed"""
        if str(payload.emoji) != self.star_emoji or not payload.guild_id:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
            
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
            
        embed = self.create_starboard_embed(message)
        embed.set_field_at(1, name="Stars", value=f"{star_reaction.count}{self.star_emoji}")
        await existing_message.edit(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def check_starboard_perms(self, ctx):
        """Verify the bot has correct permissions"""
        channel = await self.ensure_starboard_channel(ctx.guild)
        required = {
            'manage_messages': "Edit star counts",
            'embed_links': "Create rich embeds",
            'read_message_history': "Fetch messages",
            'add_reactions': "Add star reactions",
            'attach_files': "Upload attachments"
        }
        
        missing = []
        for perm, desc in required.items():
            if not getattr(channel.permissions_for(ctx.guild.me), perm):
                missing.append(f"{perm} ({desc})")
        
        if missing:
            await ctx.send(f"❌ Missing permissions:\n- " + "\n- ".join(missing))
        else:
            await ctx.send("✅ All required permissions are properly set!")
    
async def setup(bot):
    await bot.add_cog(Starboard(bot))
