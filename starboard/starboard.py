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
import time
from discord.ext import commands
from typing import Optional, List, Dict

class Starboard(commands.Cog):
    """A fully automated, configurable Starboard system that highlights popular messages in your Discord server"""
    
    def __init__(self, bot):
        self.bot = bot
        self.starboard_channels = {}
        self._load_default_settings()
        self.cooldowns: Dict[int, float] = {}  # {message_id: last_processed_time}

    def _load_default_settings(self):
        """Set default values before channel settings are loaded"""
        self.default_emoji = '⭐'
        self.default_count = 1
        self.default_ignore = []

    async def _get_channel_settings(self, channel: discord.TextChannel) -> dict:
        """Load settings from channel topic"""
        settings = {
            'emoji': self.default_emoji,
            'count': self.default_count,
            'ignore': self.default_ignore.copy()
        }
        
        if not channel.topic:
            return settings
            
        # Extract emoji from topic
        emoji_match = re.search(r'default_emoji:(\S+)', channel.topic)
        if emoji_match:
            settings['emoji'] = emoji_match.group(1)
            
        # Extract star count from topic
        count_match = re.search(r'default_count:(\d+)', channel.topic)
        if count_match:
            settings['count'] = int(count_match.group(1))
            
        # Extract ignored channels from topic
        ignore_match = re.search(r'default_ignore:\(([\d, ]+)\)', channel.topic)
        if ignore_match:
            try:
                settings['ignore'] = [int(x.strip()) for x in ignore_match.group(1).split(',')]
            except (ValueError, AttributeError):
                pass
                
        return settings

    @commands.Cog.listener()
    async def on_channel_topic_update(self, before: str, after: str, channel: discord.TextChannel):
        """Update settings when channel topic is edited"""
        if channel.name == "starboard":
            # No need to do anything specific here as settings are loaded dynamically
            pass

    @commands.command(aliases=['setstars'], no_pm=True)
    @commands.has_permissions(manage_channels=True)
    async def starconfig(self, ctx, emoji: Optional[str] = None, count: Optional[int] = None):
        """Configure starboard settings or show current configuration
        
        Examples:
        ?starconfig ⭐ 5      - Set 5 stars required
        ?starconfig 🌟        - Just change emoji
        ?starconfig reset     - Reset to defaults
        ?starconfig           - Show current settings
        """
        channel = await self.ensure_starboard_channel(ctx.guild)
        settings = await self._get_channel_settings(channel)
        
        # Show current settings if no arguments
        if emoji is None and count is None:
            embed = discord.Embed(
                title="Starboard Settings",
                color=discord.Color.gold()
            )
            embed.add_field(name="Emoji", value=settings['emoji'], inline=True)
            embed.add_field(name="Required Stars", value=settings['count'], inline=True)
            if settings['ignore']:
                ignored = ', '.join(f"<#{cid}>" for cid in settings['ignore'])
                embed.add_field(name="Ignored Channels", value=ignored, inline=False)
            embed.set_footer(text=f"Configure with {ctx.prefix}starconfig [emoji] [count]")
            return await ctx.send(embed=embed)
            
        if emoji and str(emoji).lower() == 'reset':
            new_topic = "Starboard channel - Reset to defaults"
            self._load_default_settings()
            await channel.edit(topic=new_topic)
            return await ctx.send("✅ Reset starboard to defaults (⭐ 1)")
            
        # Build new topic string
        parts = []
        if channel.topic and not channel.topic.startswith("Starboard channel"):
            parts.append(channel.topic.split('\n')[0])
            
        # Keep existing ignore settings unless we're resetting
        ignore_str = f"default_ignore:({','.join(map(str, settings['ignore']))})" if settings['ignore'] else ""
            
        if emoji:
            parts.append(f"default_emoji:{emoji}")
            settings['emoji'] = emoji
            
        if count:
            parts.append(f"default_count:{count}")
            settings['count'] = count
            
        if ignore_str:
            parts.append(ignore_str)
            
        new_topic = "Starboard channel\n" + " ".join(parts)
        await channel.edit(topic=new_topic)
        
        # Show updated settings
        settings_msg = []
        if emoji:
            settings_msg.append(f"Emoji: {settings['emoji']}")
        if count:
            settings_msg.append(f"Required stars: {settings['count']}")
            
        await ctx.send(f"✅ Updated starboard settings: {' '.join(settings_msg)}")

    async def ensure_starboard_channel(self, guild: discord.Guild) -> discord.TextChannel:
        """Ensure starboard channel exists with correct permissions"""
        channel = discord.utils.get(guild.text_channels, name="starboard")
        
        if not channel:
            # Create channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    read_message_history=True,
                    send_messages=False,
                    manage_messages=False,
                    add_reactions=False,
                    embed_links=False,
                    attach_files=False,
                    mention_everyone=False,
                    use_application_commands=False,
                    create_public_threads=False,
                    create_private_threads=False,
                    send_messages_in_threads=False,
                    use_external_emojis=False,
                    use_external_stickers=False,
                    manage_threads=False,
                    manage_webhooks=False,
                    manage_channels=False
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    manage_messages=True,
                    add_reactions=True,
                    manage_channels=True,
                    use_external_emojis=True,
                    mention_everyone=False,
                    manage_webhooks=False
                )
            }

            channel = await guild.create_text_channel(
                "starboard",
                position=0,
                overwrites=overwrites,
                topic=f"Starboard channel\ndefault_emoji:{self.default_emoji} default_count:{self.default_count}"
            )
        
        return channel
        
    async def get_star_reaction(self, message: discord.Message, emoji: str) -> Optional[discord.Reaction]:
        """Get the star reaction from a message if it exists"""
        for reaction in message.reactions:
            if str(reaction.emoji) == emoji:
                return reaction
        return None

    def create_starboard_embed(self, message: discord.Message, emoji: str, count: int) -> discord.Embed:
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
        embed.add_field(name="Stars", value=f"{count}{emoji}")
        embed.set_footer(text=f"Starboard ID: {message.id}")

        # Handle attachments
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

    async def update_starboard_message(self, starboard_message: discord.Message, count: int, emoji: str):
        """Update an existing starboard message"""
        embed = starboard_message.embeds[0]
        embed.set_field_at(1, name="Stars", value=f"{count}{emoji}")
        await starboard_message.edit(embed=embed)

    async def find_starboard_message(self, channel: discord.TextChannel, original_message_id: int) -> Optional[discord.Message]:
        """Find existing starboard message for a given original message"""
        async for message in channel.history(limit=200):
            if message.embeds and message.embeds[0].footer.text == f"Starboard ID: {original_message_id}":
                return message
        return None

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle when a reaction is added"""
        # Early returns for invalid cases
        if not payload.guild_id:
            return
        if payload.member and payload.member.bot:
            return

        # Simple cooldown implementation
        current_time = time.time()
        if payload.message_id in self.cooldowns:
            if current_time - self.cooldowns[payload.message_id] < 5.0:  # 5 second cooldown
                return
        self.cooldowns[payload.message_id] = current_time

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        try:
            starboard_channel = await self.ensure_starboard_channel(guild)
            settings = await self._get_channel_settings(starboard_channel)
            
            # Ignore reactions in starboard channel or ignored channels
            if payload.channel_id == starboard_channel.id or payload.channel_id in settings['ignore']:
                return
                
            if str(payload.emoji) != settings['emoji']:
                return

            channel = guild.get_channel(payload.channel_id)
            if not channel or not channel.permissions_for(guild.me).manage_messages:
                return
                
            try:
                message = await channel.fetch_message(payload.message_id)
            except discord.NotFound:
                return
                
            # Ignore self-starring
            if payload.user_id == message.author.id or payload.user_id == self.bot.user.id:
                return
                
            star_reaction = await self.get_star_reaction(message, settings['emoji'])
            if not star_reaction or star_reaction.count < settings['count']:
                return
                
            # Check if message is already in starboard
            existing_message = await self.find_starboard_message(starboard_channel, message.id)
            if existing_message:
                await self.update_starboard_message(existing_message, star_reaction.count, settings['emoji'])
                return
                    
            # Create new starboard entry
            try:
                embed = self.create_starboard_embed(message, settings['emoji'], star_reaction.count)
                files = []
                
                # Handle file attachments
                if message.attachments:
                    for attachment in message.attachments:
                        if not attachment.is_spoiler() and attachment.size < 8_000_000:
                            files.append(await attachment.to_file())
                
                if files:
                    starboard_msg = await starboard_channel.send(embed=embed, files=files)
                else:
                    starboard_msg = await starboard_channel.send(embed=embed)
                    
                await starboard_msg.add_reaction(settings['emoji'])
            except Exception as e:
                print(f"Error creating starboard entry: {e}")

        except Exception as e:
            print(f"Error in on_raw_reaction_add: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Handle when a reaction is removed"""
        if not payload.guild_id:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
            
        starboard_channel = await self.ensure_starboard_channel(guild)
        settings = await self._get_channel_settings(starboard_channel)
            
        if str(payload.emoji) != settings['emoji'] or payload.channel_id == starboard_channel.id:
            return
            
        channel = guild.get_channel(payload.channel_id)
        if not channel or channel.id in settings['ignore']:
            return
            
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
            
        star_reaction = await self.get_star_reaction(message, settings['emoji'])
        existing_message = await self.find_starboard_message(starboard_channel, message.id)
        if not existing_message:
            return
            
        if star_reaction and star_reaction.count >= settings['count']:
            await self.update_starboard_message(existing_message, star_reaction.count, settings['emoji'])
        # Don't delete when stars go below threshold - just leave it

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        """Handle when a message is edited"""
        if not payload.guild_id:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
            
        starboard_channel = await self.ensure_starboard_channel(guild)
        settings = await self._get_channel_settings(starboard_channel)
            
        channel = guild.get_channel(payload.channel_id)
        if not channel or channel.id == starboard_channel.id or channel.id in settings['ignore']:
            return
            
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
            
        star_reaction = await self.get_star_reaction(message, settings['emoji'])
        if not star_reaction:
            return
            
        existing_message = await self.find_starboard_message(starboard_channel, message.id)
        if not existing_message:
            return
            
        embed = self.create_starboard_embed(message, settings['emoji'], star_reaction.count)
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
            'add_reactions': "Add star reactions"
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
    
