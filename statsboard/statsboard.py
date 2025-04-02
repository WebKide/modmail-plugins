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
    """Automatic stats display system for bot statistics"""
    
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
        self._uptime = datetime.datetime.utcnow()  # Use internal uptime tracking

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

    def create_stats_embed(self):
        """Generate the stats embed"""
        embed = discord.Embed(title="Bot Statistics", timestamp=datetime.datetime.utcnow())
        
        # Handle avatar URL
        avatar_url = getattr(self.bot.user.display_avatar, 'url', None) or getattr(self.bot.user.avatar, 'url', None)
        if avatar_url:
            embed.set_author(name=self.bot.user.name, icon_url=avatar_url)
        
        # Calculate uptime using our internal property
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
        
        # Guild/member stats
        try:
            total_online = len({m.id for m in self.bot.get_all_members() if m.status is not discord.Status.offline})
            total_unique = len(self.bot.users)
            channels = sum(1 for g in self.bot.guilds for _ in g.channels)
        except:
            total_online = 0
            total_unique = 0
            channels = 0
        
        # Add fields
        embed.add_field(name="Uptime", value=uptime)
        embed.add_field(name="Latency", value=f"{self.bot.latency*1000:.2f} ms")
        embed.add_field(name="\u200b", value="\u200b")
        
        embed.add_field(name="Guilds", value=len(self.bot.guilds))
        embed.add_field(name="Members", value=f"{total_online}/{total_unique}")
        embed.add_field(name="Channels", value=channels)
        
        embed.add_field(name="RAM Usage", value=f"{memory_usage:.2f} MiB")
        embed.add_field(name="CPU Usage", value=f"{cpu_usage:.2f}%")
        embed.add_field(name="Commands Run", value=sum(self.commands_used.values()))
        
        embed.set_footer(text="Bot Statistics")
        return embed

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

def setup(bot):
    bot.add_cog(StatsBoard(bot))
    
