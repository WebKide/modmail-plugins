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

import discord
from discord.ext import commands, tasks
import datetime
import psutil
from collections import defaultdict
import json
from pathlib import Path

class StatsBoard(commands.Cog):
    """Enhanced automatic stats display system with rich visual presentation"""
    
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
        self._uptime = datetime.datetime.utcnow()
        
        # Status icons mapping
        self.status_icons = {
            'online': 'https://i.imgur.com/wlh1Uwb.png',
            'idle': 'https://i.imgur.com/dCLTaI3.png',
            'dnd': 'https://i.imgur.com/lbMqojO.png',
            'offline': 'https://i.imgur.com/6ZxDPQS.png'
        }
        
        # Track command usage
        bot.add_listener(self.on_command_completion, 'on_command_completion')

    # region Core Functions
    @property
    def uptime(self):
        """Get the uptime, falls back to current time if not set"""
        return getattr(self, '_uptime', datetime.datetime.utcnow())

    def load_config(self):
        """Load or create configuration file"""
        defaults = {
            'channel_name': 'bot-stats',
            'channel_id': None,
            'message_id': None,
            'enabled': False
        }
        
        if not self.config_file.exists():
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(defaults, f, indent=4)
            return defaults
            
        with open(self.config_file) as f:
            return json.load(f)

    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if hasattr(self, 'update_stats') and self.update_stats.is_running():
            self.update_stats.cancel()
        self.bot.remove_listener(self.on_command_completion, 'on_command_completion')

    async def get_stats_channel(self):
        """Get or create the stats channel"""
        if self.config['channel_id']:
            channel = self.bot.get_channel(self.config['channel_id'])
            if channel:
                return channel
        
        if not self.bot.guilds:
            return None
            
        guild = self.bot.guilds[0]
        
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
                embed_links=True
            )
        }
        
        try:
            channel = await guild.create_text_channel(
                name=self.config['channel_name'],
                overwrites=overwrites,
                reason='Automatic stats channel creation'
            )
            self.config['channel_id'] = channel.id
            self.save_config()
            return channel
        except discord.HTTPException:
            return None
    # endregion

    # region Event Listeners
    async def on_command_completion(self, ctx):
        """Track command usage statistics"""
        self.commands_used[ctx.command.qualified_name] += 1
    # endregion

    # region Stats Generation
    def get_guild_creation_date(self, guild):
        """Get server creation date in a readable format"""
        return guild.created_at.strftime('%b %d, %Y')
    
    def get_bot_status_icon(self):
        """Get appropriate status icon based on bot's current status"""
        status = str(self.bot.status)
        return self.status_icons.get(status, self.status_icons['offline'])
    
    def get_voice_stats(self, guild):
        """Get statistics about voice channels"""
        voice_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
        voice_members = sum(len(c.members) for c in voice_channels)
        return {
            'total_voice': len(voice_channels),
            'active_voice': sum(1 for c in voice_channels if len(c.members) > 0),
            'voice_members': voice_members
        }

    def get_role_stats(self, guild):
        """Get statistics about server roles"""
        roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
        return {
            'total_roles': len(roles),
            'highest_role': roles[0].name if roles else 'None',
            'bot_role': guild.get_member(self.bot.user.id).top_role.name
        }

    def get_channel_stats(self, guild):
        """Get statistics about text channels"""
        text_channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
        return {
            'total_text': len(text_channels),
            'public_text': sum(1 for c in text_channels if not c.is_nsfw()),
            'nsfw_text': sum(1 for c in text_channels if c.is_nsfw())
        }

    def get_member_stats(self, guild):
        """Get detailed member statistics"""
        members = guild.members
        bots = sum(1 for m in members if m.bot)
        humans = len(members) - bots
        
        status_counts = {
            'online': sum(1 for m in members if m.status == discord.Status.online),
            'idle': sum(1 for m in members if m.status == discord.Status.idle),
            'dnd': sum(1 for m in members if m.status == discord.Status.dnd),
            'offline': sum(1 for m in members if m.status == discord.Status.offline)
        }
        
        return {
            'total': len(members),
            'bots': bots,
            'humans': humans,
            'status': status_counts
        }

    def create_stats_embed(self):
        """Generate a rich stats embed with comprehensive information"""
        if not self.bot.guilds:
            return discord.Embed(title="No Guild Data Available")
            
        guild = self.bot.guilds[0]
        voice_stats = self.get_voice_stats(guild)
        role_stats = self.get_role_stats(guild)
        channel_stats = self.get_channel_stats(guild)
        member_stats = self.get_member_stats(guild)
        
        # Main embed setup
        d_t = datetime.datetime.utcnow()
        embed = discord.Embed(
            title=f"{guild.name} Statistics",
            description=f"Localtime: {d_t.strftime('%H:%M, %B %d')}\n",
            timestamp=d_t,
            color=guild.me.color if guild.me.color else discord.Color.blurple()
        )
        
        # Set author with status icon
        status_icon = self.get_bot_status_icon()
        embed.set_author(
            name=f"{self.bot.user.name} - Live Stats",
            icon_url=status_icon
        )
        
        # Set guild icon as thumbnail if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Calculate uptime
        delta = datetime.datetime.utcnow() - self.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        uptime = f"{days}d {hours}h {minutes}m {seconds}s" if days else f"{hours}h {minutes}m {seconds}s"
        
        # System stats
        try:
            memory_usage = self.process.memory_full_info().uss / 1024**2
            cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        except:
            memory_usage = 0
            cpu_usage = 0
        
        # Server Information Section
        embed.add_field(
            name="📅 Server Created",
            value=self.get_guild_creation_date(guild),
            inline=True
        )
        embed.add_field(
            name="👑 Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=True
        )
        embed.add_field(
            name="📈 Boost Level",
            value=f"Level {guild.premium_tier} (Boosts: {guild.premium_subscription_count})",
            inline=True
        )
        
        # Member Statistics Section
        embed.add_field(
            name="👥 Members",
            value=(
                f"Total: {member_stats['total']}\n"
                f"Humans: {member_stats['humans']}\n"
                f"Bots: {member_stats['bots']}"
            ),
            inline=True
        )
        embed.add_field(
            name="📶 Status",
            value=(
                f"🟢 {member_stats['status']['online']} "
                f"🟡 {member_stats['status']['idle']}\n"
                f"🔴 {member_stats['status']['dnd']} "
                f"⚫ {member_stats['status']['offline']}"
            ),
            inline=True
        )
        embed.add_field(
            name="🎤 Voice",
            value=(
                f"Active: {voice_stats['active_voice']}/{voice_stats['total_voice']}\n"
                f"Members: {voice_stats['voice_members']}"
            ),
            inline=True
        )
        
        # Channel Statistics Section
        embed.add_field(
            name="💬 Channels",
            value=(
                f"Text: {channel_stats['total_text']}\n"
                f"Public: {channel_stats['public_text']}\n"
                f"NSFW: {channel_stats['nsfw_text']}"
            ),
            inline=True
        )
        embed.add_field(
            name="🎭 Roles",
            value=(
                f"Total: {role_stats['total_roles']}\n"
                f"Highest: {role_stats['highest_role']}\n"
                f"My Role: {role_stats['bot_role']}"
            ),
            inline=True
        )
        embed.add_field(
            name="⚙️ System",
            value=(
                f"RAM: {memory_usage:.2f} MiB\n"
                f"CPU: {cpu_usage:.2f}%\n"
                f"Commands: {sum(self.commands_used.values())}"
            ),
            inline=True
        )
        
        # Bot Information Section
        embed.add_field(
            name="🤖 Bot Info",
            value=(
                f"Uptime: {uptime}\n"
                f"Latency: {self.bot.latency*1000:.2f} ms\n"
                f"Prefix: {self.bot.command_prefix}"
            ),
            inline=True
        )
        
        # Add footer with last update time
        embed.set_footer(text="Last updated")
        
        return embed
    # endregion

    # region Tasks
    @tasks.loop(seconds=16)
    async def update_stats(self):
        """Update the stats message"""
        if not self.config['enabled'] or not self.initialized:
            return
            
        try:
            if not self.stats_channel:
                self.stats_channel = await self.get_stats_channel()
                if not self.stats_channel:
                    return
                    
            embed = self.create_stats_embed()
            
            if not self.stats_message:
                if self.config['message_id']:
                    try:
                        self.stats_message = await self.stats_channel.fetch_message(self.config['message_id'])
                    except discord.NotFound:
                        pass
                        
                if not self.stats_message:
                    self.stats_message = await self.stats_channel.send(embed=embed)
                    self.config['message_id'] = self.stats_message.id
                    self.save_config()
            else:
                await self.stats_message.edit(embed=embed)
                
        except Exception as e:
            print(f"Stats update failed: {e}")
            self.stats_message = None
            self.stats_channel = None

    @update_stats.before_loop
    async def before_update_stats(self):
        await self.bot.wait_until_ready()
    # endregion

    # +------------------------------------------------------------+
    # |                   REGION COMMANDS                          |
    # +------------------------------------------------------------+
    @commands.group(name="statsboard", invoke_without_command=True)
    @commands.is_owner()
    async def statsboard_group(self, ctx):
        """Manage the stats board system"""
        await ctx.send_help(ctx.command)

    @statsboard_group.command(name="setup", no_pm=True)
    @commands.is_owner()
    async def setup_stats(self, ctx):
        """Initialize the stats board system"""
        try:
            self.stats_channel = await self.get_stats_channel()
            if not self.stats_channel:
                return await ctx.send("Failed to create stats channel.")
            
            embed = self.create_stats_embed()
            self.stats_message = await self.stats_channel.send(embed=embed)
            self.config['message_id'] = self.stats_message.id
            self.config['enabled'] = True
            self.initialized = True
            self.save_config()
            
            if not self.update_stats.is_running():
                self.update_stats.start()
            
            await ctx.send(f"Stats board initialized in {self.stats_channel.mention}")
        except Exception as e:
            await ctx.send(f"Setup failed: {str(e)}")

    @statsboard_group.command(name="toggle", no_pm=True)
    @commands.is_owner()
    async def toggle_stats(self, ctx):
        """Toggle the stats display system"""
        self.config['enabled'] = not self.config['enabled']
        self.save_config()
        status = "enabled" if self.config['enabled'] else "disabled"
        
        if self.config['enabled'] and not self.update_stats.is_running():
            self.update_stats.start()
        elif not self.config['enabled'] and self.update_stats.is_running():
            self.update_stats.cancel()
            
        await ctx.send(f"Stats display system is now {status}.")

    @statsboard_group.command(name="refresh", no_pm=True)
    @commands.is_owner()
    async def manual_refresh(self, ctx):
        """Manually refresh the stats embed"""
        if not self.initialized:
            return await ctx.send("Stats board not initialized. Use `statsboard setup` first.")
            
        await self.update_stats()
        await ctx.send("Stats refreshed!", delete_after=3)
    # endregion commands

async def setup(bot):
    await bot.add_cog(StatsBoard(bot))
