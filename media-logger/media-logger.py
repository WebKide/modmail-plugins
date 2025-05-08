"""
MIT License
Copyright (c) 2020-2025 WebKide [d.id @323578534763298816]
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

import aiohttp
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Set

import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from core import checks
from core.models import PermissionLevel

__original__ = "code inspired by @fourjr media-logger"
__source__ = "https://github.com/fourjr/modmail-plugins/blob/v4/media-logger/media-logger.py"
__author__ = "WebKide"
__version__ = "0.0.8"
__codename__ = "media-logger"
__copyright__ = "MIT License 2020-2025"
__description__ = "Enhanced Modmail plugin for media logging with smart user tracking"
__installation__ = "!plugin add WebKide/modmail-plugins/media-logger@master"

# Constants
DEFAULT_MEDIA_TYPES = {
    '.png': True, '.gif': True, '.jpg': True, '.jpeg': True, '.webm': True,
    '.pdf': False, '.txt': False, '.py': False, '.html': False, '.js': False,
    '.json': False, '.doc': False, '.css': False, '.mp3': False, '.mp4': False,
    '.avi': False, '.mov': False, '.mkv': False, '.webv': False, '.zip': False,
    '.rar': False, '.epub': False,
}

CATEGORY_MAPPING = {
    'Images': {
        'exts': ['.png', '.gif', '.jpg', '.jpeg', '.webm'],
        'thumbnail': 'https://i.imgur.com/l9yCq6n.png'
    },
    'Documents': {
        'exts': ['.pdf', '.txt', '.doc', '.zip', '.rar', '.epub'],
        'thumbnail': 'https://i.imgur.com/qiOFtgt.png'
    },
    'Code': {
        'exts': ['.py', '.html', '.js', '.json', '.css'],
        'thumbnail': 'https://i.imgur.com/QWtGa8Q.png'
    },
    'Media': {
        'exts': ['.mp3', '.mp4', '.avi', '.mov', '.mkv', '.webv'],
        'thumbnail': 'https://i.imgur.com/l2xJzbh.png'
    }
}

MAX_TRACKED_USERS = 1000
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25MB
MAX_DIRECT_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
CACHE_TTL = 300  # 5 minutes
STATS_PRUNE_DAYS = 7

# ┌───────────────────────┬───────────────────────┬───────────────────────┐
# ├───────────────────────┤     HELPER CLASSES    ├───────────────────────┤
# └───────────────────────┴───────────────────────┴───────────────────────┘
class FiletypeToggleButton(Button):
    def __init__(self, ext: str, enabled: bool, parent_view: View):
        super().__init__(
            label=ext,
            style=discord.ButtonStyle.green if enabled else discord.ButtonStyle.red
        )
        self.ext = ext
        self.enabled = enabled
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.types[self.ext] = not self.enabled
        await self.parent_view.cog.db.find_one_and_update(
            {'_id': 'config'},
            {'$set': {'allowed_types': self.parent_view.types}},
            upsert=True
        )
        await self.parent_view.cog.invalidate_config_cache()
        self.parent_view.update_buttons()
        try:
            await interaction.response.edit_message(
                embed=self.parent_view.create_embed(),
                view=self.parent_view
            )
        except discord.NotFound:
            pass

class PageNavButton(Button):
    def __init__(self, label: str, direction: int):
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.direction = direction

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        view.current_page = (view.current_page + self.direction) % len(view.categories)
        view.update_buttons()
        try:
            await interaction.response.edit_message(embed=view.create_embed(), view=view)
        except discord.NotFound:
            pass

class FiletypePaginator(View):
    def __init__(self, cog, ctx, types: dict):
        super().__init__(timeout=90)
        self.ctx = ctx
        self.cog = cog
        self.types = types
        self.categories = list(CATEGORY_MAPPING.keys())
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        category = self.categories[self.current_page]
        for ext in CATEGORY_MAPPING[category]['exts']:
            enabled = self.types.get(ext, False)
            self.add_item(FiletypeToggleButton(ext, enabled, self))
        if len(self.categories) > 1:
            self.add_item(PageNavButton('❰ 𝗉𝗋𝖾𝗏', -1))
            self.add_item(PageNavButton('𝗇𝖾𝗑𝗍 ❱', 1))

    def create_embed(self):
        category = self.categories[self.current_page]
        enabled = [ext for ext in CATEGORY_MAPPING[category]['exts'] if self.types.get(ext, False)]
        disabled = [ext for ext in CATEGORY_MAPPING[category]['exts'] if not self.types.get(ext, False)]

        embed = discord.Embed(
            title=f"💾 {category} Filetypes",
            description=(
                f"**Enabled**: {' '.join(f'`{e}`' for e in enabled) or 'None'}\n"
                f"~~Disabled~~: {' '.join(f'`{e}`' for e in disabled) or 'None'}"
            ),
            colour=self.cog.bot.main_color
        )
        embed.set_thumbnail(url=CATEGORY_MAPPING[category]['thumbnail'])
        return embed

    async def on_timeout(self):
        self.clear_items()
        if hasattr(self, 'message'):
            try:
                await self.message.edit(view=None)
            except discord.NotFound:
                pass

# ┌───────────────────────┬───────────────────────┬───────────────────────┐
# ├───────────────────────┤    MAIN COG CLASS     ├───────────────────────┤
# └───────────────────────┴───────────────────────┴───────────────────────┘
class MediaLogger(commands.Cog):
    """Advanced Modmail plugin for media logging with smart user tracking"""

    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.plugin_db.get_partition(self)
        self.config_cache = None
        self._last_config_fetch = 0
        self.session = aiohttp.ClientSession()
        
        # Memory-optimized user stats
        self.user_stats = {}  # {user_id: {uploads, deletes, last_upload, file_types}}
        self.server_stats = {'total_uploads': 0, 'total_deletes': 0}
        self.stats_threshold = 1000  # Member count threshold for tracking
        
        # Start background tasks
        self.clean_stats.start()
        self.save_stats_to_db.start()

    def cog_unload(self):
        self.clean_stats.cancel()
        self.save_stats_to_db.cancel()
        if hasattr(self, 'session'):
            self.bot.loop.create_task(self.session.close())

    # ┌───────────────────────┬────────────┬───────────────────────┐
    # ├───────────────────────┤ CORE UTILS ├───────────────────────┤
    # └───────────────────────┴────────────┴───────────────────────┘
    async def invalidate_config_cache(self):
        """Force refresh config cache on next access"""
        self.config_cache = None
        self._last_config_fetch = 0

    async def get_config(self):
        """Get config with caching"""
        if not self.config_cache or time.time() - self._last_config_fetch > CACHE_TTL:
            self.config_cache = await self.db.find_one({'_id': 'config'}) or {}
            self._last_config_fetch = time.time()
        return self.config_cache

    async def update_config_cache(self):
        """Force update and return config"""
        await self.invalidate_config_cache()
        return await self.get_config()

    async def log_channel(self):
        """Safely get log channel with permission checks"""
        config = await self.get_config()
        channel_id = config.get('log_channel')
        if not channel_id:
            return None
        
        channel = self.bot.get_channel(int(channel_id))
        if channel and channel.permissions_for(channel.guild.me).send_messages:
            return channel
        return None

    # ┌───────────────────────┬────────────┬───────────────────────┐
    # ├───────────────────────┤ TASKS.LOOP ├───────────────────────┤
    # └───────────────────────┴────────────┴───────────────────────┘
    @tasks.loop(hours=1)
    async def clean_stats(self):
        """Prune old stats and enforce memory limits"""
        cutoff = datetime.utcnow() - timedelta(days=STATS_PRUNE_DAYS)
        
        # Prune old user stats
        for user_id in list(self.user_stats.keys()):
            if self.user_stats[user_id]['last_upload'] < cutoff:
                del self.user_stats[user_id]
        
        # Enforce max tracked users
        while len(self.user_stats) > MAX_TRACKED_USERS:
            oldest_user = min(self.user_stats.items(), key=lambda x: x[1]['last_upload'])
            del self.user_stats[oldest_user[0]]

    @tasks.loop(hours=6)
    async def save_stats_to_db(self):
        """Periodically save stats to database"""
        if not self.user_stats:
            return
            
        # Convert datetime objects to ISO format for storage
        stats_to_save = {}
        for user_id, data in self.user_stats.items():
            stats_to_save[user_id] = data.copy()
            if isinstance(data['last_upload'], datetime):
                stats_to_save[user_id]['last_upload'] = data['last_upload'].isoformat()
        
        await self.db.find_one_and_update(
            {'_id': 'user_stats'},
            {'$set': {'data': stats_to_save}},
            upsert=True
        )

    # ┌──────────────────────┬──────────────┬──────────────────────┐
    # ├──────────────────────┤ COG_LISTENER ├──────────────────────┤
    # └──────────────────────┴──────────────┴──────────────────────┘
    @commands.Cog.listener()
    async def on_ready(self):
        """Load stats on startup"""
        await self.load_stats_from_db()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Log command errors to media log channel"""
        log_channel = await self.log_channel()
        if log_channel:
            embed = discord.Embed(
                title="⚠️ Command Error",
                description=(
                    f"**Command:** `{ctx.command}`\n"
                    f"**User:** {ctx.author.mention}\n"
                    f"**Error:** ```{str(error)}```"
                ),
                color=discord.Color.red()
            )
            await log_channel.send(embed=embed)

    # ┌───────────────────────┬────────────┬───────────────────────┐
    # ├───────────────────────┤ STATS UTIL ├───────────────────────┤
    # └───────────────────────┴────────────┴───────────────────────┘
    async def load_stats_from_db(self):
        """Load stats from database on startup"""
        data = await self.db.find_one({'_id': 'user_stats'})
        if data and 'data' in data:
            for user_id, stats in data['data'].items():
                if 'last_upload' in stats and isinstance(stats['last_upload'], str):
                    stats['last_upload'] = datetime.fromisoformat(stats['last_upload'])
            self.user_stats = data['data']
            
            # Prune immediately on load
            cutoff = datetime.utcnow() - timedelta(days=STATS_PRUNE_DAYS)
            self.user_stats = {
                k: v for k, v in self.user_stats.items()
                if v['last_upload'] >= cutoff
            }

    async def update_user_stats(self, user_id: str, channel: discord.TextChannel, attachments: list):
        """Update user stats with memory limits"""
        if len(self.user_stats) >= MAX_TRACKED_USERS:
            # Remove oldest user if bot is at capacity
            oldest_user = min(self.user_stats.items(), key=lambda x: x[1]['last_upload'])
            del self.user_stats[oldest_user[0]]

        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'uploads': 0,
                'deletes': 0,
                'last_upload': datetime.utcnow(),
                'type_stats': defaultdict(int),
                'channel_stats': defaultdict(int)
            }

        user_data = self.user_stats[user_id]
        for attachment in attachments:
            filetype = Path(attachment.filename).suffix.lower()
            user_data["type_stats"][filetype] += 1
            user_data["channel_stats"][str(channel.id)] += 1

        user_data['uploads'] += len(attachments)
        user_data['last_upload'] = datetime.utcnow()
        await self.save_stats_to_db()  # Persist changes immediately

    # ╔════════════════════════════════════════════════════════════╗
    # ║                     SETMEDIALOGCHANNEL                     ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    @commands.guild_only()
    async def setmedialogchannel(self, ctx, channel: discord.TextChannel):
        """Set the media log channel, run this command first"""
        u = ctx.author
        await self.db.find_one_and_update(
            {'_id': 'config'},
            {'$set': {'log_channel': str(channel.id), 'ignored_channels': [], 'allowed_types': DEFAULT_MEDIA_TYPES}},
            upsert=True
        )
        await self.update_config_cache()
        await ctx.send(f'🗃️ Media log channel set to {channel.mention} by **{u.display_name}**')

    # ╔════════════════════════════════════════════════════════════╗
    # ║                       MEDIALOGIGNORE                       ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    @commands.guild_only()
    async def medialogignore(self, ctx, channel: discord.TextChannel):
        """Toggle ignore status for a channel"""
        config = await self.get_config()
        ignored = config.get("ignored_channels", [])
        action = "Removed" if str(channel.id) in ignored else "Added"
        update = {'$pull': {'ignored_channels': str(channel.id)}} if action == "Removed" \
            else {'$addToSet': {'ignored_channels': str(channel.id)}}
        await self.db.find_one_and_update({'_id': 'config'}, update, upsert=True)
        await self.update_config_cache()
        await ctx.send(f'📦 {action} {channel.mention} {"from" if action == "Removed" else "to"} ignore list.')

    # ╔════════════════════════════════════════════════════════════╗
    # ║                          MEDIALOG                          ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.MODERATOR)
    @commands.command()
    @commands.guild_only()
    async def medialog(self, ctx):
        """View current media logging settings
        - `setmedialogchannel` - Set the media log channel
        - `medialogtracking` - Set channel tracking mode
        - `medialogtypes` - Toggle which filetypes to log
        - `medialogtogglebots` - Log media from bots too?
        - `medialogconfig` - Media logger configuration
          ├─ `enable` - Enable advanced tracking
          ├─ `disable` - Disable advanced tracking
          ├─ `force_enable` - Bypass server-size check
          └─ `force_disable` - Disable bypass
        - `medialogaddchannel` - Opt-in a channel
        - `medialogignore` - Ignore status for channel
        - `medialog` - View current media logging settings
        - `medialoggerstats` - View detailed statistics
        """

        config = await self.get_config()
        allowed = config.get("allowed_types", DEFAULT_MEDIA_TYPES)
        log_bot = config.get("log_bot_media", False)
        log_channel = await self.log_channel()
        ignored = config.get("ignored_channels", [])

        embed = discord.Embed(
            title="🎛️ Media Logging Settings",
            color=self.bot.main_color
        )
        embed.add_field(
            name="📮 Log Channel",
            value=log_channel.mention if log_channel else "Not Set",
            inline=False
        )
        embed.add_field(
            name="🤖 Log Bot Media",
            value="✅ Enabled" if log_bot else "❎ Disabled",
            inline=False
        )
        embed.add_field(
            name="📵 Ignored Channels",
            value=", ".join(f"<#{c}>" for c in ignored) or "None",
            inline=False
        )
        
        enabled_types = [ext for ext, enabled in allowed.items() if enabled]
        disabled_types = [ext for ext, enabled in allowed.items() if not enabled]
        
        embed.add_field(
            name="💾 Enabled Filetypes",
            value=" ".join(f"`{ext}`" for ext in enabled_types) or "None",
            inline=False
        )
        embed.add_field(
            name="🗳️ Disabled Filetypes",
            value=" ".join(f"`{ext}`" for ext in disabled_types) or "None",
            inline=False
        )

        if ctx.guild.member_count < self.stats_threshold:
            embed.add_field(
                name="📊 Server Statistics",
                value=f"🗄️ **Total uploads:** {self.server_stats['total_uploads']}\n🗑️ **Total deletes:** {self.server_stats['total_deletes']}",
                inline=False
            )

        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                     MEDIALOGTOGGLEBOTS                     ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    @commands.guild_only()
    async def medialogtogglebots(self, ctx):
        """Toggle logging media from bots"""
        config = await self.get_config()
        current = config.get("log_bot_media", False)
        await self.db.find_one_and_update(
            {'_id': 'config'},
            {'$set': {'log_bot_media': not current}},
            upsert=True
        )
        await self.update_config_cache()
        await ctx.send(f"🤖 Logging bot media is now {'enabled ✅' if not current else 'disabled ❎'}.")

    # ╔════════════════════════════════════════════════════════════╗
    # ║                      MEDIALOGTOGTYPES                      ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    @commands.guild_only()
    async def medialogtypes(self, ctx):
        """Toggle which filetypes to log using paginator"""
        await self.update_config_cache()
        config = self.config_cache
        types = config.get("allowed_types", DEFAULT_MEDIA_TYPES.copy())

        view = FiletypePaginator(self, ctx, types)
        await ctx.send("💾 Select filetypes to log:", embed=view.create_embed(), view=view)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                       MEDIALOGGONFIG                       ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def medialogconfig(self, ctx):
        """Media logger configuration panel"""
        config = await self.get_config()
        current = config.get("advanced_tracking", ctx.guild.member_count < self.stats_threshold)
        force_enabled = config.get("force_enabled", False)
        
        embed = discord.Embed(
            title="🎛️ Media Logger Configuration",
            color=self.bot.main_color
        )
        
        status = "✅ Enabled" if current else "❎ Disabled"
        if force_enabled:
            status += " (⚠️ Force-enabled)"
        
        embed.add_field(
            name="🚥 Current Status",
            value=status,
            inline=False
        )
        embed.add_field(
            name="👥 Server Size",
            value=f"{ctx.guild.member_count} members (threshold: {self.stats_threshold})",
            inline=False
        )
        embed.add_field(
            name="📊 Statistics",
            value=f"Total uploads: {self.server_stats.get('total_uploads', 0)}\n"
                  f"Total deletes: {self.server_stats.get('total_deletes', 0)}",
            inline=False
        )
        embed.set_footer(text=f"Use {ctx.prefix}help medialogconfig for commands")
        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                    MEDIALOGCONFIG.ENABLE                   ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @medialogconfig.command()
    async def enable(self, ctx):
        """Enable advanced tracking"""
        if ctx.guild.member_count >= self.stats_threshold:
            return await ctx.send(
                f"⚠️ **Warning: Your server has {ctx.guild.member_count} members.**\n"
                f"Advanced tracking is not recommended above {self.stats_threshold} members.\n\n"
                f"Use `{ctx.prefix}medialogconfig force_enable` to override."
            )
        
        await self._update_config(True, False)
        await ctx.send(f"✅ Advanced tracking enabled by **{ctx.author.display_name}** using normal configuration.")

    # ╔════════════════════════════════════════════════════════════╗
    # ║                   MEDIALOGCONFIG.DISABLE                   ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @medialogconfig.command()
    async def disable(self, ctx):
        """Disable advanced tracking"""
        await self._update_config(False, False)
        self.user_stats = {}
        self.server_stats = {'total_uploads': 0, 'total_deletes': 0}
        await ctx.send("❎ Advanced tracking disabled by **{ctx.author.display_name}** using normal configuration.")

    # ╔════════════════════════════════════════════════════════════╗
    # ║                MEDIALOGCONFIG.FORCE_ENABLE                 ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @medialogconfig.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    async def force_enable(self, ctx):
        """Force-enable advanced tracking (bypass size check)"""
        await self._update_config(True, True)
        await ctx.send(
            "⚠️ Advanced tracking FORCE-ENABLED despite size warning!\n"
            "Statistics collection may impact performance on large servers.\n"
            "Settings enabled by **{ctx.author.display_name}**"
        )

    # ╔════════════════════════════════════════════════════════════╗
    # ║                MEDIALOGCONFIG.FORCE_DISABLE                ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @medialogconfig.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    async def force_disable(self, ctx):
        """Force-disable advanced tracking"""
        await self._update_config(False, False)
        self.user_stats = {}
        self.server_stats = {'total_uploads': 0, 'total_deletes': 0}
        await ctx.send("🛑 Advanced tracking force-disabled by **{ctx.author.display_name}**.")

    async def _update_config(self, enabled: bool, force: bool):
        """Internal method to update configuration"""
        await self.db.find_one_and_update(
            {'_id': 'config'},
            {'$set': {
                'advanced_tracking': enabled,
                'force_enabled': force
            }},
            upsert=True
        )
        await self.update_config_cache()

    # ╔════════════════════════════════════════════════════════════╗
    # ║                      MEDIALOGGERSTATS                      ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.MODERATOR)
    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.guild_only()
    async def medialoggerstats(self, ctx, user: Optional[discord.User] = None):
        """View detailed media statistics for a user (or yourself)"""
        target_user = user or ctx.author
        config = await self.get_config()
        
        # Only show stats if advanced tracking is enabled for this server
        if ctx.guild.member_count >= self.stats_threshold:
            return await ctx.send("ℹ️ Advanced statistics tracking is disabled for large servers.")
        
        user_data = self.user_stats.get(str(target_user.id))
        if not user_data:
            return await ctx.send(f"📊 No media statistics found for {target_user.display_name}.")
        
        # Calculate top file types
        top_types = sorted(
            user_data['type_stats'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Calculate top channels
        top_channels = sorted(
            user_data['channel_stats'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Create the embed
        embed = discord.Embed(
            title=f"📊 Media Statistics for {target_user.display_name}",
            description=f"🛒 Total attachments sent: **{user_data.get('uploads', 0)}**",
            color=self.bot.main_color
        )
        
        # Add file type distribution
        type_field = "\n".join(f"{ext}: {count}" for ext, count in top_types)
        embed.add_field(
            name="📄 Top File Types",
            value=type_field or "🚧 No file type data",
            inline=True
        )
        
        # Add channel distribution
        channel_field = "\n".join(f"<#{cid}>: {count}" for cid, count in top_channels)
        embed.add_field(
            name="📂 Top Channels",
            value=channel_field or "🚧 No channel data",
            inline=True
        )
        
        # Add activity info
        embed.add_field(
            name="⏱️ Last Activity",
            value=f"<t:{int(user_data['last_upload'].timestamp())}:R>",
            inline=False
        )
        
        embed.set_footer(text=f"👤 User ID: {target_user.id}")
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                      MEDIALOGTRACKING                      ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    async def medialogtracking(self, ctx, mode: str):
        """Set channel tracking mode (opt-in or all).
        
        Options:
        - `all`: Track all channels except ignored ones
        - `opt-in`: Only track explicitly listed channels
        """
        if mode.lower() not in ('all', 'opt-in'):
            return await ctx.send("Invalid mode. Use `all` or `opt-in`.")
        
        await self.db.find_one_and_update(
            {'_id': 'config'},
            {'$set': {'channel_tracking': mode.lower()}},
            upsert=True
        )
        await self.invalidate_config_cache()
        await ctx.send(f"Channel tracking set to `{mode.lower()}` mode.")

    # ╔════════════════════════════════════════════════════════════╗
    # ║                     MEDIALOGADDCHANNEL                     ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    async def medialogaddchannel(self, ctx, channel: discord.TextChannel):
        """Add a channel to the tracked list (opt-in mode only)."""
        config = await self.get_config()
        if config.get('channel_tracking', 'all') != 'opt-in':
            return await ctx.send("Channel tracking is not in opt-in mode.")
        
        await self.db.find_one_and_update(
            {'_id': 'config'},
            {'$addToSet': {'tracked_channels': str(channel.id)}},
            upsert=True
        )
        await self.invalidate_config_cache()
        await ctx.send(f"Added {channel.mention} to tracked channels.")

async def setup(bot):
    await bot.add_cog(MediaLogger(bot))
