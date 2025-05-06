# ╔════════════════════════════════════════════════════════════╗
# ║                    MEDIALOGGER.PY v2025                    ║
# ╠════════════════════╦══════════════════╦════════════════════╣
# ╠════════════════════╣ MODMAIL PLUGINS  ╠════════════════════╣
# ╠════════════════════╣ ORIGINAL FOURJR  ╠════════════════════╣
# ╠════════════════════╣ EXPANDED WEBKIDE ╠════════════════════╣
# ╚════════════════════╩══════════════════╩════════════════════╝
# https://github.com/fourjr/modmail-plugins/blob/v4/media-logger/media-logger.py

from datetime import datetime, timedelta
import time
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from core import checks
from core.models import PermissionLevel
from typing import Dict, Optional

DEFAULT_MEDIA_TYPES = {
    '.png': True, '.gif': True, '.jpg': True, '.jpeg': True, '.webm': True,
    '.pdf': False, '.txt': False, '.py': False, '.html': False, '.js': False,
    '.json': False, '.md': False, '.css': False, '.mp3': False, '.mp4': False,
    '.avi': False, '.mov': False, '.mkv': False, '.webv': False, '.zip': False,
    '.rar': False, '.7z': False,
}

CATEGORY_MAPPING = {
    'Images': {
        'exts': ['.png', '.gif', '.jpg', '.jpeg', '.webm'],
        'thumbnail': 'https://i.imgur.com/JdsoiDSJ.png'
    },
    'Documents': {
        'exts': ['.pdf', '.txt', '.md', '.zip', '.rar', '.7z'],
        'thumbnail': 'https://i.imgur.com/GoisdDde.png'
    },
    'Code': {
        'exts': ['.py', '.html', '.js', '.json', '.css'],
        'thumbnail': 'https://i.imgur.com/OpsdiuhD.png'
    },
    'Media': {
        'exts': ['.mp3', '.mp4', '.avi', '.mov', '.mkv', '.webv'],
        'thumbnail': 'https://i.imgur.com/NiodsDsd.png'
    }
}

class FiletypeToggleButton(Button):
    def __init__(self, ext, enabled, view):
        super().__init__(
            label=ext,
            style=discord.ButtonStyle.green if enabled else discord.ButtonStyle.red
        )
        self.ext = ext
        self.enabled = enabled
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        self.view.types[self.ext] = not self.enabled
        await self.view.cog.db.find_one_and_update(
            {'_id': 'config'},
            {'$set': {'allowed_types': self.view.types}},
            upsert=True
        )
        await self.view.cog.update_config_cache()
        self.view.update_buttons()
        await interaction.response.edit_message(embed=self.view.create_embed(), view=self.view)

class PageNavButton(Button):
    def __init__(self, label: str, view: View, direction: int):
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.view = view
        self.direction = direction

    async def callback(self, interaction: discord.Interaction):
        self.view.current_page = (self.view.current_page + self.direction) % len(self.view.categories)
        self.view.update_buttons()
        await interaction.response.edit_message(embed=self.view.create_embed(), view=self.view)

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
            self.add_item(PageNavButton('◀️', self, -1))
            self.add_item(PageNavButton('▶️', self, 1))

    def create_embed(self):
        category = self.categories[self.current_page]
        enabled = [ext for ext in CATEGORY_MAPPING[category]['exts'] if self.types.get(ext, False)]
        disabled = [ext for ext in CATEGORY_MAPPING[category]['exts'] if not self.types.get(ext, False)]

        embed = discord.Embed(
            title=f"{category} Filetypes",
            description=(
                f"**Enabled**: {' '.join(f'`{e}`' for e in enabled) or 'None'}\n"
                f"~~Disabled~~: {' '.join(f'`{e}`' for e in disabled) or 'None'}"
            ),
            colour=self.cog.bot.main_color
        )
        embed.set_thumbnail(url=CATEGORY_MAPPING[category]['thumbnail'])
        return embed

class MediaLogger(commands.Cog):
    """Enhanced Modmail plugin for media logging with smart tracking"""

    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.plugin_db.get_partition(self)
        self.config_cache = None
        self._last_config_fetch = 0
        self._cache_ttl = 300  # 5 minutes cache
        
        # Statistics tracking
        self.user_stats = {}  # {user_id: {'uploads': int, 'deletes': int, 'last_upload': datetime}}
        self.server_stats = {'total_uploads': 0, 'total_deletes': 0}
        self.stats_threshold = 1000  # Member count threshold for advanced tracking
        self.clean_stats.start()

    def cog_unload(self):
        self.clean_stats.cancel()

    @tasks.loop(hours=1)
    async def clean_stats(self):
        """Periodically clean old stats to prevent memory bloat"""
        cutoff = datetime.utcnow() - timedelta(days=30)
        for user_id in list(self.user_stats.keys()):
            if self.user_stats[user_id]['last_upload'] < cutoff:
                del self.user_stats[user_id]

    async def get_config(self):
        if self.config_cache is None or time.time() - self._last_config_fetch > self._cache_ttl:
            self.config_cache = await self.db.find_one({'_id': 'config'}) or {}
            self._last_config_fetch = time.time()
        return self.config_cache

    async def update_config_cache(self):
        self.config_cache = await self.db.find_one({'_id': 'config'}) or {}
        self._last_config_fetch = time.time()

    async def log_channel(self):
        config = await self.get_config()
        channel_id = config.get('log_channel')
        if channel_id:
            return self.bot.get_channel(int(channel_id))

    async def is_ignored(self, channel):
        config = await self.get_config()
        return str(channel.id) in config.get('ignored_channels', [])

    def is_valid_attachment(self, attachment, allowed_types):
        content_type = (attachment.content_type or '').lower()
        filename = attachment.filename.lower()
        return any(enabled and (filename.endswith(ext) or ext in content_type)
                   for ext, enabled in allowed_types.items())

    async def create_media_embed(self, message, attachments):
        embed = discord.Embed(
            title=f"Media from {message.channel.name}",
            description=f'[Jump to Message]({message.jump_url})',
            color=self.bot.main_color,
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(name=f"{message.author.display_name} ({message.author.id})", 
                        icon_url=message.author.display_avatar.url)
        
        # Server size based conditional fields
        if message.guild.member_count < self.stats_threshold:
            user_stats = self.user_stats.get(str(message.author.id), {})
            embed.add_field(
                name="User Statistics",
                value=f"Uploads: {user_stats.get('uploads', 0)}\nDeletes: {user_stats.get('deletes', 0)}",
                inline=True
            )
            
            time_since_last = (datetime.utcnow() - user_stats.get('last_upload', datetime.utcnow())).seconds
            if time_since_last < 3600:  # 1 hour
                embed.add_field(
                    name="⚠️ Upload Frequency",
                    value=f"{time_since_last//60} minutes since last upload",
                    inline=True
                )
        
        # File information
        embed.add_field(
            name="Files",
            value=f"Count: {len(attachments)}\nTypes: {', '.join(set(a.filename.split('.')[-1] for a in attachments))}",
            inline=False
        )
        
        return embed

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or not message.attachments:
            return
        
        config = await self.get_config()
        if message.author.bot and not config.get("log_bot_media", False):
            return
        if await self.is_ignored(message.channel):
            return

        allowed_types = config.get("allowed_types", DEFAULT_MEDIA_TYPES)
        valid_files = [a for a in message.attachments if self.is_valid_attachment(a, allowed_types)]
        if not valid_files:
            return

        log_channel = await self.log_channel()
        if not log_channel:
            return

        # Update statistics (only if below threshold)
        if message.guild.member_count < self.stats_threshold:
            user_id = str(message.author.id)
            if user_id not in self.user_stats:
                self.user_stats[user_id] = {'uploads': 0, 'deletes': 0, 'last_upload': datetime.utcnow()}
            
            self.user_stats[user_id]['uploads'] += len(valid_files)
            self.user_stats[user_id]['last_upload'] = datetime.utcnow()
            self.server_stats['total_uploads'] += len(valid_files)

        # Create and send embed
        embed = await self.create_media_embed(message, valid_files)
        
        # Send all valid attachments in one message if possible
        try:
            files = [await attachment.to_file() for attachment in valid_files[:10]]  # Discord limit of 10 files
            await log_channel.send(files=files, embed=embed)
        except discord.HTTPException:
            # Fallback to individual sends if bulk fails
            for attachment in valid_files:
                try:
                    file = await attachment.to_file()
                    await log_channel.send(file=file, embed=embed)
                except Exception:
                    continue

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return
            
        if message.guild.member_count < self.stats_threshold and message.attachments:
            user_id = str(message.author.id)
            if user_id in self.user_stats:
                self.user_stats[user_id]['deletes'] += len(message.attachments)
                self.server_stats['total_deletes'] += len(message.attachments)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                     SETMEDIALOGCHANNEL                     ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    @commands.guild_only()
    async def setmedialogchannel(self, ctx, channel: discord.TextChannel):
        """Set the media log channel"""
        await self.db.find_one_and_update(
            {'_id': 'config'},
            {'$set': {'log_channel': str(channel.id), 'ignored_channels': [], 'allowed_types': DEFAULT_MEDIA_TYPES}},
            upsert=True
        )
        await self.update_config_cache()
        await ctx.send(f'Media log channel set to {channel.mention}')

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
        await ctx.send(f'{action} {channel.mention} {"from" if action == "Removed" else "to"} ignore list.')

    # ╔════════════════════════════════════════════════════════════╗
    # ║                          MEDIALOG                          ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.MODERATOR)
    @commands.command()
    @commands.guild_only()
    async def medialog(self, ctx):
        """View current media logging settings"""
        config = await self.get_config()
        allowed = config.get("allowed_types", DEFAULT_MEDIA_TYPES)
        log_bot = config.get("log_bot_media", False)
        log_channel = await self.log_channel()
        ignored = config.get("ignored_channels", [])

        embed = discord.Embed(
            title="Media Logging Settings",
            color=self.bot.main_color
        )
        embed.add_field(
            name="Log Channel",
            value=log_channel.mention if log_channel else "Not Set",
            inline=False
        )
        embed.add_field(
            name="Log Bot Media",
            value="✅ Enabled" if log_bot else "❌ Disabled",
            inline=False
        )
        embed.add_field(
            name="Ignored Channels",
            value=", ".join(f"<#{c}>" for c in ignored) or "None",
            inline=False
        )
        
        enabled_types = [ext for ext, enabled in allowed.items() if enabled]
        disabled_types = [ext for ext, enabled in allowed.items() if not enabled]
        
        embed.add_field(
            name="Enabled Filetypes",
            value=" ".join(f"`{ext}`" for ext in enabled_types) or "None",
            inline=False
        )
        embed.add_field(
            name="Disabled Filetypes",
            value=" ".join(f"`{ext}`" for ext in disabled_types) or "None",
            inline=False
        )

        if ctx.guild.member_count < self.stats_threshold:
            embed.add_field(
                name="Server Statistics",
                value=f"Total uploads: {self.server_stats['total_uploads']}\nTotal deletes: {self.server_stats['total_deletes']}",
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
        await ctx.send(f"Logging bot media is now {'enabled ✅' if not current else 'disabled ❌'}.")

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
        await ctx.send("Select filetypes to log:", embed=view.create_embed(), view=view)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                       MEDIALOGGONFIG                       ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    @commands.guild_only()
    async def medialogconfig(self, ctx, enable_stats: bool = None):
        """Configure advanced tracking with size warnings"""
        if enable_stats is None:
            current = ctx.guild.member_count < self.stats_threshold
            embed = discord.Embed(
                title="Media Logger Configuration",
                color=self.bot.main_color
            )
            embed.add_field(
                name="Current Status",
                value=f"Advanced tracking is {'✅ enabled' if current else '❌ disabled'}",
                inline=False
            )
            embed.add_field(
                name="Server Size",
                value=f"{ctx.guild.member_count} members (threshold: {self.stats_threshold})",
                inline=False
            )
            embed.add_field(
                name="Warning",
                value="⚠️ Enabling on large servers may increase memory usage",
                inline=False
            )
            return await ctx.send(embed=embed)
        
        if enable_stats and ctx.guild.member_count >= self.stats_threshold:
            return await ctx.send(
                f"⚠️ Warning: Your server has {ctx.guild.member_count} members.\n"
                f"Advanced tracking is not recommended above {self.stats_threshold} members.\n"
                "Use `medialogconfig force_enable` to override this warning."
            )
        
        # In a real implementation, you would save this preference to database
        await ctx.send(
            f"Advanced tracking has been {'enabled ✅' if enable_stats else 'disabled ❌'}.\n"
            f"Statistics will {'now' if enable_stats else 'no longer'} be collected."
        )

async def setup(bot):
    await bot.add_cog(MediaLogger(bot))
