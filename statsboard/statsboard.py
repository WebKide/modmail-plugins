"""
MIT License
Copyright (c) 2019-2025 WebKide [d.id @323578534763298816]
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

import asyncio
import datetime
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional

import discord
import psutil
from discord.ext import commands, tasks

logger = logging.getLogger("Modmail")

class StatsBoard(commands.Cog):
    """Enhanced automatic Modmail bot stats display system"""

    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()
        self.stats_message = None
        self.stats_channel = None
        self.commands_used = defaultdict(int)
        self.messages_sent = 0
        self.config_file = Path('data/stats_config.json')
        self.config = self.load_config()
        self.initialized = False
        self._initialization_lock = asyncio.Lock()
        self._uptime = datetime.datetime.utcnow()
        self._last_embed_hash = None  # For change detection
        self._guild_id = None  # Store target guild ID

        # Emoji status indicators
        self.status_emojis = {
            'online': '🟢',
            'idle': '🟡', 
            'dnd': '🔴',
            'invisible': '⚫',
            'offline': '⚫'
        }

        # Configuration validation
        self._validate_config()

    # region Core Functions
    def _validate_config(self):
        """Validate and fix configuration issues"""
        required_keys = ['channel_name', 'channel_id', 'message_id', 'enabled', 'guild_id', 'update_interval']
        defaults = {
            'channel_name': 'bot-stats',
            'channel_id': None,
            'message_id': None, 
            'enabled': False,
            'guild_id': None,
            'update_interval': 30  # Increase to 60 to reduce API calls if 30 is an issue
        }

        for key in required_keys:
            if key not in self.config:
                self.config[key] = defaults[key]

        self.save_config()

    @property
    def uptime(self):
        """Get the uptime with fallback protection"""
        return getattr(self, '_uptime', datetime.datetime.utcnow())

    @property 
    def target_guild(self) -> Optional[discord.Guild]:
        """Get the target guild for stats display"""
        if self.config.get('guild_id'):
            return self.bot.get_guild(self.config['guild_id'])
        return self.bot.guilds[0] if self.bot.guilds else None

    def load_config(self) -> Dict[str, Any]:
        """Load configuration with error handling"""
        defaults = {
            'channel_name': 'bot-stats',
            'channel_id': None,
            'message_id': None,
            'enabled': False,
            'guild_id': None,
            'update_interval': 30
        }

        try:
            if not self.config_file.exists():
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_file, 'w') as f:
                    json.dump(defaults, f, indent=4)
                return defaults

            with open(self.config_file) as f:
                config = json.load(f)
                # Merge with defaults to handle missing keys
                for key, value in defaults.items():
                    if key not in config:
                        config[key] = value
                return config

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Config load failed: {e}. Using defaults.")
            return defaults

    def save_config(self):
        """Save configuration with error handling"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            logger.error(f"Failed to save config: {e}")

    def cog_unload(self):
        """Proper cleanup when cog is unloaded"""
        try:
            if hasattr(self, 'update_stats') and self.update_stats.is_running():
                self.update_stats.cancel()
        except Exception as e:
            logger.error(f"Error stopping stats task: {e}")

    async def get_stats_channel(self) -> Optional[discord.TextChannel]:
        """Get or create the stats channel with proper error handling"""
        guild = self.target_guild
        if not guild:
            logger.error("No target guild available")
            return None

        # Try to get existing channel
        if self.config['channel_id']:
            channel = guild.get_channel(self.config['channel_id'])
            if channel and isinstance(channel, discord.TextChannel):
                return channel
            else:
                logger.warning(f"Configured channel {self.config['channel_id']} not found")

        # Check permissions before creating
        if not guild.me.guild_permissions.manage_channels:
            logger.error("Bot lacks permission to create channels, which is required to run this plugin")
            return None

        # Set up permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                send_messages=False,
                add_reactions=False,
                manage_messages=False,
                view_channel=True
            ),
            guild.me: discord.PermissionOverwrite(
                manage_channels=True,
                send_messages=True,
                manage_messages=True,
                embed_links=True,
                read_message_history=True
            )
        }

        try:
            channel = await guild.create_text_channel(
                name=self.config['channel_name'],
                overwrites=overwrites,
                topic="Automated server statistics - Updated every few minutes",
                reason='Automatic stats channel creation'
            )
            self.config['channel_id'] = channel.id
            self.config['guild_id'] = guild.id
            self.save_config()
            logger.info(f"Created stats channel: {channel.name}")
            return channel

        except discord.HTTPException as e:
            logger.error(f"Failed to create stats channel: {e}")
            return None
    # endregion

    # region Event Listeners
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Track command usage statistics"""
        if ctx.command:
            self.commands_used[ctx.command.qualified_name] += 1

    @commands.Cog.listener() 
    async def on_message(self, message):
        """Track message statistics"""
        if not message.author.bot:
            self.messages_sent += 1
    # endregion

    # region Stats Generation
    def get_guild_info(self, guild: discord.Guild) -> Dict[str, Any]:
        """Get basic guild information"""
        return {
            'creation_date': guild.created_at.strftime('%b %d, %Y'),
            'owner': guild.owner.mention if guild.owner else "Unknown",
            'boost_level': guild.premium_tier,
            'boost_count': guild.premium_subscription_count,
            'verification_level': str(guild.verification_level).title(),
            'member_count': guild.member_count or len(guild.members)
        }

    def get_bot_status_emoji(self) -> str:
        """Get appropriate status emoji based on bot's current status"""
        status = str(self.bot.status)
        return self.status_emojis.get(status, self.status_emojis['offline'])

    def get_voice_stats(self, guild: discord.Guild) -> Dict[str, int]:
        """Get comprehensive voice channel statistics"""
        voice_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
        active_channels = [c for c in voice_channels if len(c.members) > 0]
        total_voice_members = sum(len(c.members) for c in voice_channels)

        return {
            'total_voice': len(voice_channels),
            'active_voice': len(active_channels),
            'voice_members': total_voice_members,
            'stage_channels': len([c for c in guild.channels if isinstance(c, discord.StageChannel)])
        }

    def get_role_stats(self, guild: discord.Guild) -> Dict[str, Any]:
        """Get role statistics with safety checks"""
        roles = guild.roles
        bot_member = guild.get_member(self.bot.user.id)

        return {
            'total_roles': len(roles),
            'highest_role': roles[-1].name if roles else 'None',
            'bot_role': bot_member.top_role.name if bot_member else 'None',
            'hoisted_roles': len([r for r in roles if r.hoist])
        }

    def get_channel_stats(self, guild: discord.Guild) -> Dict[str, int]:
        """Get comprehensive channel statistics"""
        channels_by_type = defaultdict(int)
        for channel in guild.channels:
            channels_by_type[type(channel).__name__] += 1

        text_channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]

        return {
            'total_text': len(text_channels),
            'total_voice': channels_by_type.get('VoiceChannel', 0),
            'total_stage': channels_by_type.get('StageChannel', 0), 
            'total_forum': channels_by_type.get('ForumChannel', 0),
            'total_categories': channels_by_type.get('CategoryChannel', 0),
            'nsfw_channels': len([c for c in text_channels if getattr(c, 'nsfw', False)])
        }

    def get_member_stats(self, guild: discord.Guild) -> Dict[str, Any]:
        """Get detailed member statistics with online status"""
        members = guild.members
        if not members:  # Fallback for large guilds
            return {
                'total': guild.member_count or 0,
                'bots': 0,
                'humans': guild.member_count or 0,
                'status': {'online': 0, 'idle': 0, 'dnd': 0, 'offline': 0}
            }

        bots = sum(1 for m in members if m.bot)
        humans = len(members) - bots

        status_counts = defaultdict(int)
        for member in members:
            status_counts[str(member.status)] += 1

        return {
            'total': len(members),
            'bots': bots,
            'humans': humans,
            'status': {
                'online': status_counts['online'],
                'idle': status_counts['idle'], 
                'dnd': status_counts['dnd'],
                'offline': status_counts['offline'] + status_counts['invisible']
            }
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system performance statistics with error handling"""
        try:
            # Get memory info
            memory_info = self.process.memory_full_info()
            memory_mb = memory_info.uss / (1024 * 1024)

            # Get CPU percentage (not divided by CPU count for proper percentage)
            cpu_percent = self.process.cpu_percent()

            # Get thread count
            thread_count = self.process.num_threads()

            return {
                'memory_mb': memory_mb,
                'cpu_percent': cpu_percent,
                'thread_count': thread_count,
                'total_commands': sum(self.commands_used.values()),
                'unique_commands': len(self.commands_used)
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"System stats error: {e}")
            return {
                'memory_mb': 0,
                'cpu_percent': 0,
                'thread_count': 0,
                'total_commands': sum(self.commands_used.values()),
                'unique_commands': len(self.commands_used)
            }

    def format_uptime(self) -> str:
        """Format uptime in a readable way"""
        delta = datetime.datetime.utcnow() - self.uptime
        total_seconds = int(delta.total_seconds())

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600) 
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        else:
            return f"{minutes}m {seconds}s"

    def create_stats_embed(self) -> Optional[discord.Embed]:
        """Generate comprehensive stats embed with error handling"""
        guild = self.target_guild
        if not guild:
            return discord.Embed(
                title="❌ No Guild Data Available",
                description="Bot is not connected to any servers, there is an error in the connection.",
                color=discord.Color.red()
            )

        try:
            # Gather all statistics
            guild_info = self.get_guild_info(guild)
            voice_stats = self.get_voice_stats(guild)
            role_stats = self.get_role_stats(guild)
            channel_stats = self.get_channel_stats(guild)
            member_stats = self.get_member_stats(guild)
            system_stats = self.get_system_stats()

            # Create embed
            embed = discord.Embed(
                title=f"📊 {guild.name} Statistics",
                description=f"Live server statistics • Last updated: <t:{int(datetime.datetime.utcnow().timestamp())}:R>",
                timestamp=datetime.datetime.utcnow(),
                color=guild.me.color if guild.me and guild.me.color.value != 0 else discord.Color.blurple()
            )

            # Set author with status
            status_emoji = self.get_bot_status_emoji()
            embed.set_author(
                name=f"{status_emoji} {self.bot.user.name} Statistics",
                icon_url=self.bot.user.display_avatar.url
            )

            # Set thumbnail
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)

            # Server Information
            embed.add_field(
                name="🏛️ Server Info",
                value=(
                    f"**Created:** {guild_info['creation_date']}\n"
                    f"**Owner:** {guild_info['owner']}\n"
                    f"**Verification:** {guild_info['verification_level']}"
                ),
                inline=True
            )

            embed.add_field(
                name="💎 Boosts",
                value=(
                    f"**Level:** {guild_info['boost_level']}\n"
                    f"**Count:** {guild_info['boost_count']}\n"
                    f"**Members:** {guild_info['member_count']:,}"
                ),
                inline=True
            )

            # Member Statistics
            embed.add_field(
                name="👥 Members",
                value=(
                    f"**Total:** {member_stats['total']:,}\n"
                    f"**Humans:** {member_stats['humans']:,}\n"
                    f"**Bots:** {member_stats['bots']:,}"
                ),
                inline=True
            )

            # Online Status
            status = member_stats['status']
            embed.add_field(
                name="📶 Online Status", 
                value=(
                    f"🟢 {status['online']:,} 🟡 {status['idle']:,}\n"
                    f"🔴 {status['dnd']:,} ⚫ {status['offline']:,}"
                ),
                inline=True
            )

            # Channel Statistics
            embed.add_field(
                name="💬 Channels",
                value=(
                    f"**Text:** {channel_stats['total_text']}\n"
                    f"**Voice:** {channel_stats['total_voice']}\n"
                    f"**Categories:** {channel_stats['total_categories']}"
                ),
                inline=True
            )

            # Voice Activity
            embed.add_field(
                name="🎤 Voice Activity", 
                value=(
                    f"**Active:** {voice_stats['active_voice']}/{voice_stats['total_voice']}\n"
                    f"**Members:** {voice_stats['voice_members']}\n"
                    f"**Stages:** {voice_stats['stage_channels']}"
                ),
                inline=True
            )

            # Role Information
            embed.add_field(
                name="🎭 Roles",
                value=(
                    f"**Total:** {role_stats['total_roles']}\n"
                    f"**Hoisted:** {role_stats['hoisted_roles']}\n"
                    f"**My Role:** {role_stats['bot_role']}"
                ),
                inline=True
            )

            # Bot Performance
            embed.add_field(
                name="🤖 Bot Performance",
                value=(
                    f"**Uptime:** {self.format_uptime()}\n"
                    f"**Latency:** {self.bot.latency*1000:.1f}ms\n"
                    f"**Commands:** {system_stats['total_commands']:,}"
                ),
                inline=True
            )

            # System Resources
            embed.add_field(
                name="⚙️ System Resources",
                value=(
                    f"**Memory:** {system_stats['memory_mb']:.1f} MB\n"
                    f"**CPU:** {system_stats['cpu_percent']:.1f}%\n"
                    f"**Threads:** {system_stats['thread_count']}"
                ),
                inline=True
            )

            # Footer
            embed.set_footer(
                text=f"Guild ID: {guild.id} • Shard: {guild.shard_id if hasattr(guild, 'shard_id') else 'N/A'}",
                icon_url=self.bot.user.display_avatar.url
            )

            return embed
            
        except Exception as e:
            logger.error(f"Error creating stats embed: {e}")
            return discord.Embed(
                title="❌ Stats Error",
                description=f"Failed to generate statistics: {str(e)[:100]}",
                color=discord.Color.red()
            )
    # endregion

    # region Tasks
    @tasks.loop(seconds=30)  # Default interval, configurable
    async def update_stats(self):
        """Update the stats message with change detection"""
        if not self.config['enabled'] or not self.initialized:
            return

        try:
            # Ensure we have a channel
            if not self.stats_channel:
                self.stats_channel = await self.get_stats_channel()
                if not self.stats_channel:
                    logger.error("Could not get stats channel, might have been deleted by someone")
                    return

            # Generate new embed
            embed = self.create_stats_embed()
            if not embed:
                return

            # Check if embed has changed (simple hash comparison)
            embed_str = str(embed.to_dict())
            embed_hash = hash(embed_str)

            if embed_hash == self._last_embed_hash:
                return  # No changes, skip update

            self._last_embed_hash = embed_hash

            # Get or create message
            if not self.stats_message:
                if self.config['message_id']:
                    try:
                        self.stats_message = await self.stats_channel.fetch_message(self.config['message_id'])
                    except (discord.NotFound, discord.HTTPException):
                        logger.warning("Configured stats message not found, creating new one")
                        pass

                '''
                if not self.stats_message:  # enable for production servers DISSABLED for testing
                    # Clean up old messages before creating new one
                    try:
                        async for message in self.stats_channel.history(limit=10):
                            if message.author == self.bot.user and message.embeds:
                                await message.delete()
                                await asyncio.sleep(0.5)  # Rate limit protection
                    except discord.HTTPException:
                        pass

                    self.stats_message = await self.stats_channel.send(embed=embed)
                    self.config['message_id'] = self.stats_message.id
                    self.save_config()
                    logger.info("Created new stats message")
                '''
            else:
                await self.stats_message.edit(embed=embed)

        except discord.HTTPException as e:
            logger.error(f"HTTP error updating stats: {e}")
            if e.status == 404:  # Message deleted
                self.stats_message = None
                self.config['message_id'] = None
                self.save_config()
        except Exception as e:
            logger.error(f"Unexpected error updating stats: {e}")
            # Reset on critical errors
            self.stats_message = None
            self.stats_channel = None

    @update_stats.before_loop
    async def before_update_stats(self):
        """Wait for bot to be ready before starting updates"""
        await self.bot.wait_until_ready()

    def _restart_task_with_interval(self):
        """Restart the task with new interval"""
        if self.update_stats.is_running():
            self.update_stats.cancel()

        # Recreate task with new interval
        self.update_stats.change_interval(seconds=self.config.get('update_interval', 30))
        if self.config['enabled'] and self.initialized:
            self.update_stats.start()
    # endregion

    # region Commands
    @commands.group(name="statsboard", invoke_without_command=True, aliases=['stats'])
    @commands.has_permissions(manage_guild=True)
    async def statsboard_group(self, ctx):
        """Manage the stats board system"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="📊 Stats Board Management",
                description="Manage the automatic server statistics display",
                color=discord.Color.blurple()
            )
            embed.add_field(
                name="Commands",
                value=(
                    "`setup` - Initialize the stats system\n"
                    "`toggle` - Enable/disable stats updates\n"
                    "`refresh` - Manually update stats\n"
                    "`config` - View current configuration\n"
                    "`interval <seconds>` - Set update interval"
                ),
                inline=False
            )
            embed.add_field(
                name="Status",
                value=f"**Enabled:** {self.config['enabled']}\n**Initialized:** {self.initialized}",
                inline=True
            )
            await ctx.send(embed=embed)

    @statsboard_group.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    async def setup_stats(self, ctx):
        """Initialize the stats board system"""
        async with self._initialization_lock:
            if self.initialized and self.config['enabled']:
                return await ctx.send("❌ Stats board is already set up and running!")

            try:
                # Set guild ID if not set
                if not self.config.get('guild_id'):
                    self.config['guild_id'] = ctx.guild.id
                    self.save_config()

                # Get or create channel
                self.stats_channel = await self.get_stats_channel()
                if not self.stats_channel:
                    return await ctx.send("❌ Failed to create stats channel. Check bot permissions.")

                # Create initial message
                embed = self.create_stats_embed()
                if not embed:
                    return await ctx.send("❌ Failed to generate stats embed.")

                self.stats_message = await self.stats_channel.send(embed=embed)

                # Update configuration
                self.config['message_id'] = self.stats_message.id
                self.config['enabled'] = True
                self.initialized = True
                self.save_config()

                # Start the update task
                if not self.update_stats.is_running():
                    self.update_stats.start()

                embed_response = discord.Embed(
                    title="✅ Stats Board Initialized",
                    description=f"Stats board is now active in {self.stats_channel.mention}",
                    color=discord.Color.green()
                )
                embed_response.add_field(
                    name="Configuration",
                    value=f"Update interval: {self.config.get('update_interval', 30)}s",
                    inline=False
                )
                await ctx.send(embed=embed_response)

            except Exception as e:
                logger.error(f"Setup failed: {e}")
                await ctx.send(f"❌ Setup failed: {str(e)}")

    @statsboard_group.command(name="toggle")
    @commands.has_permissions(manage_guild=True)
    async def toggle_stats(self, ctx):
        """Toggle the stats display system"""
        self.config['enabled'] = not self.config['enabled']
        self.save_config()

        status = "enabled" if self.config['enabled'] else "disabled"
        color = discord.Color.green() if self.config['enabled'] else discord.Color.orange()

        if self.config['enabled'] and self.initialized and not self.update_stats.is_running():
            self.update_stats.start()
        elif not self.config['enabled'] and self.update_stats.is_running():
            self.update_stats.cancel()

        embed = discord.Embed(
            title=f"📊 Stats Board {status.title()}",
            description=f"Stats display system is now **{status}**",
            color=color
        )
        await ctx.send(embed=embed)

    @statsboard_group.command(name="refresh", aliases=['update'])
    @commands.has_permissions(manage_guild=True)
    async def manual_refresh(self, ctx):
        """Manually refresh the stats embed"""
        if not self.initialized:
            return await ctx.send("❌ Stats board not initialized. Use `statsboard setup` first.")

        try:
            await self.update_stats()
            embed = discord.Embed(
                title="✅ Stats Refreshed",
                description="Statistics have been manually updated",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed, delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ Refresh failed: {str(e)}")

    @statsboard_group.command(name="config", aliases=['settings'])
    @commands.has_permissions(manage_guild=True)
    async def show_config(self, ctx):
        """Display current configuration"""
        embed = discord.Embed(
            title="⚙️ Stats Board Configuration",
            color=discord.Color.blurple()
        )

        guild = self.target_guild
        channel = self.stats_channel or (guild.get_channel(self.config['channel_id']) if self.config['channel_id'] else None)

        embed.add_field(
            name="Status",
            value=(
                f"**Enabled:** {self.config['enabled']}\n"
                f"**Initialized:** {self.initialized}\n"
                f"**Task Running:** {self.update_stats.is_running() if hasattr(self, 'update_stats') else False}"
            ),
            inline=True
        )

        embed.add_field(
            name="Settings",
            value=(
                f"**Update Interval:** {self.config.get('update_interval', 30)}s\n"
                f"**Guild:** {guild.name if guild else 'None'}\n"
                f"**Channel:** {channel.mention if channel else 'None'}"
            ),
            inline=True
        )

        embed.add_field(
            name="Statistics",
            value=(
                f"**Commands Tracked:** {len(self.commands_used)}\n"
                f"**Total Commands:** {sum(self.commands_used.values())}\n"
                f"**Uptime:** {self.format_uptime()}"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @statsboard_group.command(name="interval")
    @commands.has_permissions(manage_guild=True)
    async def set_interval(self, ctx, seconds: int):
        """Set the stats update interval (minimum 10 seconds)"""
        if seconds < 10:
            return await ctx.send("❌ Minimum update interval is 10 seconds.")
        if seconds > 3600:
            return await ctx.send("❌ Maximum update interval is 3600 seconds (1 hour).")

        self.config['update_interval'] = seconds
        self.save_config()

        # Restart task with new interval
        self._restart_task_with_interval()

        embed = discord.Embed(
            title="⏱️ Update Interval Changed",
            description=f"Stats will now update every **{seconds}** seconds",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @statsboard_group.command(name="reset")
    @commands.has_permissions(manage_guild=True)
    async def reset_stats(self, ctx):
        """Reset the stats board system"""
        # Stop task
        if self.update_stats.is_running():
            self.update_stats.cancel()

        # Reset variables
        self.stats_message = None
        self.stats_channel = None
        self.initialized = False

        # Reset config
        self.config.update({
            'channel_id': None,
            'message_id': None,
            'enabled': False
        })
        self.save_config()

        embed = discord.Embed(
            title="🔄 Stats Board Reset",
            description="Stats board has been completely reset. Use `setup` to reinitialize.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @statsboard_group.error
    async def statsboard_error(self, ctx, error):
        """Handle errors in statsboard commands"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="You need `Manage Server` permission to use stats board commands.",
                color=discord.Color.red()
            )
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏳ Command on Cooldown",
                description=f"Please wait {error.retry_after:.1f} seconds before using this command again.",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="❌ Command Error",
                description=f"An error occurred: {str(error)[:200]}",
                color=discord.Color.red()
            )
            logger.error(f"Statsboard command error: {error}")

        await ctx.send(embed=embed, ephemeral=True)
    # endregion

async def setup(bot):
    await bot.add_cog(StatsBoard(bot))
