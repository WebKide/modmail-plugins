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
import json
import datetime
import psutil

from pathlib import Path
from discord.ext import commands, tasks
from collections import defaultdict

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
        self.update_stats.start()

    def load_config(self):
        """Load or create configuration file"""
        defaults = {
            'channel_name': 'bot-stats',
            'channel_id': None,
            'message_id': None,
            'enabled': True
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
        self.update_stats.cancel()

    async def get_stats_channel(self):
        """Get or create the stats channel"""
        # Try to find existing channel first
        if self.config['channel_id']:
            channel = self.bot.get_channel(self.config['channel_id'])
            if channel:
                return channel
        
        # Channel not found, create new one
        guild = self.bot.guilds[0]  # Use first guild the bot is in
        
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
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        
        # Uptime calculation
        delta = datetime.datetime.utcnow() - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        uptime = f"{days}d {hours}h {minutes}m {seconds}s" if days else f"{hours}h {minutes}m {seconds}s"
        
        # System stats
        memory_usage = self.process.memory_full_info().uss / 1024**2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        
        # Guild/member stats
        total_online = len({m.id for m in self.bot.get_all_members() if m.status is not discord.Status.offline})
        total_unique = len(self.bot.users)
        channels = sum(1 for g in self.bot.guilds for _ in g.channels)
        
        # Add fields in 3 columns
        embed.add_field(name="Uptime", value=uptime)
        embed.add_field(name="Latency", value=f"{self.bot.latency*1000:.2f} ms")
        embed.add_field(name="\u200b", value="\u200b")  # Empty column
        
        embed.add_field(name="Guilds", value=len(self.bot.guilds))
        embed.add_field(name="Members", value=f"{total_online}/{total_unique}")
        embed.add_field(name="Channels", value=channels)
        
        embed.add_field(name="RAM Usage", value=f"{memory_usage:.2f} MiB")
        embed.add_field(name="CPU Usage", value=f"{cpu_usage:.2f}%")
        embed.add_field(name="Commands Run", value=sum(self.commands_used.values()))
        
        embed.set_footer(text=f"Last Updated")
        return embed

    @tasks.loop(seconds=16)
    async def update_stats(self):
        """Update the stats message"""
        if not self.config['enabled']:
            return
            
        try:
            if not self.stats_channel:
                self.stats_channel = await self.get_stats_channel()
                if not self.stats_channel:
                    return
                    
            embed = self.create_stats_embed()
            
            if not self.stats_message:
                # Try to find existing message
                if self.config['message_id']:
                    try:
                        self.stats_message = await self.stats_channel.fetch_message(self.config['message_id'])
                    except discord.NotFound:
                        pass
                        
                # Create new message if none exists
                if not self.stats_message:
                    self.stats_message = await self.stats_channel.send(embed=embed)
                    self.config['message_id'] = self.stats_message.id
                    self.save_config()
            else:
                await self.stats_message.edit(embed=embed)
                
        except discord.HTTPException as e:
            print(f"Stats update failed: {e}")
            # Reset message/channel references to attempt fresh start next time
            self.stats_message = None
            self.stats_channel = None

    @update_stats.before_loop
    async def before_update_stats(self):
        """Wait for bot to be ready before starting loop"""
        await self.bot.wait_until_ready()

    @commands.command(name="statsrefresh", hidden=True, no_pm=True)
    @commands.is_owner()
    async def manual_refresh(self, ctx):
        """Manually refresh the stats embed"""
        await self.update_stats()
        await ctx.send("Stats refreshed!", delete_after=23)

    @commands.command(name="togglestats", hidden=True, no_pm=True)
    @commands.is_owner()
    async def toggle_stats(self, ctx):
        """Toggle the stats display system"""
        self.config['enabled'] = not self.config['enabled']
        self.save_config()
        status = "enabled" if self.config['enabled'] else "disabled"
        await ctx.send(f"Stats display system is now {status}.")

def setup(bot):
    bot.add_cog(StatsBoard(bot))
  
