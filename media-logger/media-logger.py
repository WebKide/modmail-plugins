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
import asyncio
import io
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
__version__ = "0.1.1"
__codename__ = "media-logger"
__copyright__ = "MIT License 2020-2025"
__description__ = "Enhanced Modmail plugin for media logging with smart user tracking"
__installation__ = "!plugin add WebKide/modmail-plugins/media-logger@master"

# Constants
DEFAULT_MEDIA_TYPES = {
    '.png': True, '.gif': True, '.jpg': True, '.jpeg': True, '.webm': True,
    '.pdf': False, '.txt': False, '.py': False, '.html': False, '.js': False,
    '.json': False, '.md': False, '.css': False, '.mp3': False, '.mp4': False,
    '.avi': False, '.mov': False, '.mkv': False, '.webv': False, '.zip': False,
    '.rar': False, '.epub': False,
}

CATEGORY_MAPPING = {
    'Images': {
        'exts': ['.png', '.gif', '.jpg', '.jpeg', '.webm'],
        'thumbnail': 'https://i.imgur.com/l9yCq6n.png'
    },
    'Documents': {
        'exts': ['.pdf', '.txt', '.md', '.zip', '.rar', '.epub'],
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

MAX_TRACKED_USERS = 1000  # To prevent large spikes in memory
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25MB
MAX_DIRECT_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
CACHE_TTL = 300  # 5 minutes
STATS_PRUNE_DAYS = 7  # Prune stats older than 1 week

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
        self.message = None
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
            description="Menu to choose filetypes to log",
            colour=self.cog.bot.main_color
        ).add_field(
            name='✅ **Enabled:**',
            value=' '.join(f'`{e}`' for e in enabled) or 'None',
            inline=False
        ).add_field(
            name='❎ ~~Disabled:~~',
            value=' '.join(f'`{e}`' for e in disabled) or 'None',
            inline=False
        ).set_thumbnail(
            url=CATEGORY_MAPPING[category]['thumbnail']
        ).set_footer(
            text="This menu will timeout in 90 seconds"
        )

        return embed


    async def on_timeout(self):
        category = self.categories[self.current_page]
        enabled = [ext for ext in CATEGORY_MAPPING[category]['exts'] if self.types.get(ext, False)]
        disabled = [ext for ext in CATEGORY_MAPPING[category]['exts'] if not self.types.get(ext, False)]

        embed = discord.Embed(
            title=f"💾 {category} Filetypes",
            description="(Menu Expired)",
            colour=self.cog.bot.light_grey()
        ).add_field(
            name='✅ **Enabled:**',
            value=' '.join(f'`{e}`' for e in enabled) or 'None',
            inline=False
        ).add_field(
            name='❎ ~~Disabled:~~',
            value=' '.join(f'`{e}`' for e in disabled) or 'None',
            inline=False
        ).set_thumbnail(
            url=CATEGORY_MAPPING[category]['thumbnail']
        ).set_footer(
            text=f"Use `{self.ctx.prefix}medialogtypes` to make changes."
        )
        
        try:
            await self.message.edit(embed=embed, view=None)
        except discord.NotFound:
            pass
        except discord.HTTPException:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command invoker can interact with the buttons"""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "❌ This menu is not for you!",
                ephemeral=True
            )
            return False
        return True

class MediaLogger(commands.Cog):
    """Advanced Modmail plugin for media logging with smart user tracking"""

    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.plugin_db.get_partition(self)
        self.config_cache = None
        self._last_config_fetch = 0
        
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

    async def log_channel(self):
        config = await self.get_config()
        channel_id = config.get('log_channel')
        return self.bot.get_channel(int(channel_id)) if channel_id else None

    async def process_attachments(self, message: discord.Message, log_channel: discord.TextChannel):
        """Process and log valid attachments"""
        config = await self.get_config()
        allowed_types = config.get("allowed_types", DEFAULT_MEDIA_TYPES)

        valid_attachments = [
            att for att in message.attachments
            if Path(att.filename).suffix.lower() in allowed_types
            and allowed_types[Path(att.filename).suffix.lower()]
        ]

        if not valid_attachments:
            return

        # Update stats
        if message.guild.member_count < self.stats_threshold or config.get("force_enabled", False):
            await self.update_user_stats(str(message.author.id), message.channel, valid_attachments)
            self.server_stats['total_uploads'] += len(valid_attachments)

        # Log each attachment
        for attachment in valid_attachments:
            try:
                embed = discord.Embed(
                    title="📁 Media Logged",
                    color=self.bot.main_color,
                    timestamp=message.created_at
                )
                embed.add_field(name="Author", value=f"{message.author.mention} (`{message.author.id}`)", inline=False)
                embed.add_field(name="Channel", value=f"{message.channel.mention}", inline=False)
                embed.add_field(name="File", value=f"[{attachment.filename}]({attachment.url})", inline=False)
                embed.set_footer(text=f"Message ID: {message.id}")

                # For images, set the image as embed thumbnail
                if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    embed.set_thumbnail(url=attachment.url)

                await log_channel.send(embed=embed)

            except discord.HTTPException as e:
                print(f"Failed to log media: {e}")

    async def is_ignored(self, channel):
        config = await self.get_config()
        ignored_channels = config.get('ignored_channels', [])
        tracked_channels = config.get('tracked_channels', [])
        
        # If channel tracking is opt-in and this channel isn't tracked
        if config.get('channel_tracking') == 'opt-in' and str(channel.id) not in tracked_channels:
            return True
            
        return str(channel.id) in ignored_channels

    async def validate_attachment(self, attachment: discord.Attachment, allowed_types: Dict[str, bool]) -> bool:
        """Validate attachment with header checks and size limits."""
        if attachment.size > MAX_ATTACHMENT_SIZE:
            return False

        ext = '.' + attachment.filename.lower().split('.')[-1]
        if not allowed_types.get(ext, False):
            return False

        # Skip header checks for small files
        if attachment.size < 1024:  # 1KB
            return True

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        return False
                    
                    # Read first 256 bytes for file signature
                    chunk = await resp.content.read(256)
                    return self.validate_file_signature(ext, chunk)
        except Exception:
            return False

    def validate_file_signature(self, ext: str, header: bytes) -> bool:
        """Validate file headers against known signatures."""
        signatures = {
            '.png': b'\x89PNG',
            '.jpg': b'\xFF\xD8\xFF',
            '.jpeg': b'\xFF\xD8\xFF',
            '.gif': b'GIF',
            '.pdf': b'%PDF',
            '.zip': b'PK\x03\x04',
            '.rar': [b'Rar!\x1A\x07', b'Rar!\x1A\x07\x01\x00']
        }
        return ext not in signatures or header.startswith(signatures[ext])

    async def stream_attachment(self, attachment: discord.Attachment) -> Optional[discord.File]:
        """Stream large attachments >5MB without full download."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        return None
                    return discord.File(
                        fp=resp.content,
                        filename=attachment.filename
                    )
        except Exception:
            return None

    async def handle_attachment(self, attachment: discord.Attachment) -> Optional[discord.File]:
        """Hybrid attachment handler with size-based streaming."""
        if attachment.size <= MAX_DIRECT_UPLOAD_SIZE:
            return await attachment.to_file()
        return await self.stream_attachment(attachment)

    async def update_user_stats(self, user_id: str, channel: discord.TextChannel, attachments: list):
        """Update user stats with memory limits."""
        if len(self.user_stats) >= MAX_TRACKED_USERS:
            # Remove oldest user if bot is at capacity
            oldest_user = min(self.user_stats.items(), key=lambda x: x[1]['last_upload'])
            del self.user_stats[oldest_user[0]]

        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'uploads': 0,
                'deletes': 0,
                'last_upload': datetime.utcnow(),
                'file_types': {}
            }

        user_data = self.user_stats[user_id]
        filetype = Path(attachment.filename).suffix.lower()
        user_data["type_stats"][filetype] += 1
        user_data["channel_stats"][str(channel.id)] += 1
        user_data['uploads'] += len(attachments)
        user_data['last_upload'] = datetime.utcnow()

        for attachment in attachments:
            ext = '.' + attachment.filename.split('.')[-1].lower()
            user_data['file_types'][ext] = user_data['file_types'].get(ext, 0) + 1

    # ┌───────────────────────┬────────────┬───────────────────────┐
    # ├───────────────────────┤ TASKS.LOOP ├───────────────────────┤
    # └───────────────────────┴────────────┴───────────────────────┘
    @tasks.loop(hours=1)
    async def clean_stats(self):
        """Prune old stats and enforce memory limits."""
        cutoff = datetime.utcnow() - timedelta(days=STATS_PRUNE_DAYS)

        # Prune old user stats
        for user_id in list(self.user_stats.keys()):
            if self.user_stats[user_id]['last_upload'] < cutoff:
                del self.user_stats[user_id]

        # Enforce max tracked users
        while len(self.user_stats) > MAX_TRACKED_USERS:
            oldest_user = min(self.user_stats.items(), key=lambda x: x[1]['last_upload'])
            del self.user_stats[oldest_user[0]]

    # ┌───────────────────────┬────────────┬───────────────────────┐
    # ├───────────────────────┤ TASKS.LOOP ├───────────────────────┤
    # └───────────────────────┴────────────┴───────────────────────┘
    @tasks.loop(hours=6)
    async def save_stats_to_db(self):
        """Periodically save stats to database."""
        if not self.user_stats:
            return

        await self.db.find_one_and_update(
            {'_id': 'user_stats'},
            {'$set': {'data': self.user_stats}},
            upsert=True
        )

    async def load_stats_from_db(self):
        """Load stats from database on startup."""
        data = await self.db.find_one({'_id': 'user_stats'})
        if data and 'data' in data:
            self.user_stats = data['data']

            # Prune immediately on load
            cutoff = datetime.utcnow() - timedelta(days=STATS_PRUNE_DAYS)
            self.user_stats = {
                k: v for k, v in self.user_stats.items()
                if v['last_upload'] >= cutoff
            }

    # ┌──────────────────────┬──────────────┬──────────────────────┐
    # ├──────────────────────┤ COG_LISTENER ├──────────────────────┤
    # └──────────────────────┴──────────────┴──────────────────────┘
    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_stats_from_db()

    # ┌──────────────────────┬──────────────┬──────────────────────┐
    # ├──────────────────────┤ COG_LISTENER ├──────────────────────┤
    # └──────────────────────┴──────────────┴──────────────────────┘
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Main event listener that handles media attachment logging
        according to configuration.
        """
        # Ignore messages from the bot itself to prevent loops
        if message.author == self.bot.user:
            return

        # Ignore DMs - only process guild messages
        if not message.guild:
            return

        # Skip messages without attachments
        if not message.attachments:
            return

        # Get current configuration
        config = await self.get_config()

        # Check if logging channel is set up
        log_channel = await self.log_channel()
        if not log_channel:
            return

        # IMPORTANT: Ignore messages in the log channel itself
        if message.channel.id == log_channel.id:
            return

        # Check if we should ignore bots
        if message.author.bot and not config.get("log_bot_media", False):
            return

        # Determine channel tracking mode
        channel_tracking = config.get("channel_tracking", "all")
        ignored_channels = config.get("ignored_channels", [])
        tracked_channels = config.get("tracked_channels", [])

        # Check if this channel should be processed based on tracking mode
        if channel_tracking == "all":
            # In 'all' mode, skip only explicitly ignored channels
            if str(message.channel.id) in ignored_channels:
                return
        else:  # opt-in mode
            # In 'opt-in' mode, process only explicitly tracked channels
            if str(message.channel.id) not in tracked_channels:
                return

        # Get allowed file types
        allowed_types = config.get("allowed_types", DEFAULT_MEDIA_TYPES)

        # Filter attachments by allowed types and size
        valid_attachments = []
        for attachment in message.attachments:
            # Check file extension
            file_ext = Path(attachment.filename).suffix.lower()
            if file_ext not in allowed_types or not allowed_types[file_ext]:
                continue

            # Check file size
            if attachment.size > MAX_ATTACHMENT_SIZE:
                continue

            valid_attachments.append(attachment)

        # If no valid attachments, stop processing
        if not valid_attachments:
            return

        # Update statistics if tracking is enabled
        if message.guild.member_count < self.stats_threshold or config.get("force_enabled", False):
            await self.update_user_stats(str(message.author.id), message.channel, valid_attachments)
            self.server_stats['total_uploads'] += len(valid_attachments)

        # Prepare and send log messages
        try:
            # For multiple attachments, we'll group some types together
            image_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
            document_exts = ('.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx')

            # Group attachments by type
            images = [a for a in valid_attachments if a.filename.lower().endswith(image_exts)]
            documents = [a for a in valid_attachments if a.filename.lower().endswith(document_exts)]
            other_files = [a for a in valid_attachments if a not in images and a not in documents]

            # Create base embed
            embed = discord.Embed(
                color=self.bot.main_color,
                timestamp=message.created_at
            )
            embed.set_author(
                name=f"{message.author.display_name} ({message.author.id})",
                icon_url=message.author.display_avatar.url
            )
            embed.add_field(
                name="📌 Message",
                value=f"[Jump to message]({message.jump_url}) in {message.channel.mention}",
                inline=False
            )

            # Log images in a single embed with thumbnails
            if images:
                image_embed = embed.copy()
                image_embed.title = f"🖼️ {len(images)} Image(s) Logged"
                image_embed.description = "\n".join(
                    f"[{img.filename}]({img.url})" for img in images
                )

                # Use first image as thumbnail if available
                if images[0].filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    image_embed.set_thumbnail(url=images[0].url)

                await log_channel.send(embed=image_embed)

            # Log documents in a single embed
            if documents:
                doc_embed = embed.copy()
                doc_embed.title = f"📄 {len(documents)} Document(s) Logged"
                doc_embed.description = "\n".join(
                    f"[{doc.filename}]({doc.url})" for doc in documents
                )
                await log_channel.send(embed=doc_embed)

            # Log other files individually
            for file in other_files:
                file_embed = embed.copy()
                file_embed.title = f"📁 File Logged: {file.filename}"
                file_embed.description = f"[Download]({file.url})"

                # For video/audio files, show duration if available
                if file.filename.lower().endswith(('.mp4', '.mov', '.mp3', '.wav')):
                    file_embed.add_field(name="Type", value=file.filename.split('.')[-1].upper(), inline=True)

                await log_channel.send(embed=file_embed)

        except discord.HTTPException as e:
            # Fallback to simple text logging if embeds fail
            try:
                file_links = "\n".join(f"- {a.filename}: {a.url}" for a in valid_attachments)
                await log_channel.send(
                    f"📁 Files uploaded by {message.author} in {message.channel.mention}:\n"
                    f"{file_links}\n"
                    f"Original message: {message.jump_url}"
                )
            except discord.HTTPException:
                print(f"Failed to log media from message {message.id}: {e}")
        except Exception as e:
            print(f"Unexpected error logging media: {e}")

    # ╔════════════════════════════════════════════════════════════╗
    # ║░░░░░░░░░░░░░░░░░░░░░SETMEDIALOGCHANNEL░░░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command()
    @commands.guild_only()
    async def setmedialogchannel(self, ctx, channel: discord.TextChannel):
        """Set the media log channel, run this command first"""
        # Check basic permissions first
        required_perms = {
            'view_channel': True,
            'send_messages': True,
            'embed_links': True,
            'attach_files': True,
            'read_message_history': True
        }

        bot_perms = channel.permissions_for(ctx.guild.me)
        missing_perms = [perm for perm, required in required_perms.items() 
                        if required and not getattr(bot_perms, perm)]

        if missing_perms:
            return await ctx.send(
                f"❌ I'm missing required permissions in {channel.mention}:\n"
                f"`{', '.join(missing_perms).replace('_', ' ').title()}`\n"
                "Please fix these permissions and try again."
            )

        # Test actual embed and file sending capability
        test_embed = discord.Embed(
            title="📁 Media Logger Test",
            description="Verifying channel permissions...",
            color=self.bot.main_color
        )
        test_embed.set_thumbnail(url=CATEGORY_MAPPING['Media']['thumbnail'])
        test_embed.set_footer(text="This is a test message, it will be deleted shortly")

        try:
            # Create a small test file in memory
            test_file = discord.File(
                io.BytesIO(b"This is a test file for permission verification"),
                filename="permission_test.txt"
            )

            # Send test message
            test_msg = await channel.send(
                embed=test_embed,
                file=test_file
            )

            # Clean up test message after short delay
            await asyncio.sleep(5)
            await test_msg.delete()

        except discord.Forbidden as e:
            return await ctx.send(
                f"❌ Permission verification failed in {channel.mention}:\n"
                f"`{str(e)}`\n"
                "Please ensure I have all required permissions and try again."
            )
        except discord.HTTPException as e:
            return await ctx.send(
                f"⚠️ Unexpected error while testing {channel.mention}:\n"
                f"`{str(e)}`\n"
                "Please try again or contact support."
            )

        # If we get here, permissions are good - save the channel
        await self.db.find_one_and_update(
            {'_id': 'config'},
            {'$set': {
                'log_channel': str(channel.id), 
                'ignored_channels': [], 
                'allowed_types': DEFAULT_MEDIA_TYPES
            }},
            upsert=True
        )
        await self.update_config_cache()

        await ctx.send(
            f"✅ **Media log channel** successfully set to {channel.mention} by **{ctx.author.display_name}**\n"
            "*All required permissions were succesfully verified.*\n"
            f"Next: `{ctx.prefix}medialogtracking` - to set channel tracking mode"
        )

    # ╔════════════════════════════════════════════════════════════╗
    # ║░░░░░░░░░░░░░░░░░░░░░░░MEDIALOGIGNORE░░░░░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
    # ║░░░░░░░░░░░░░░░░░░░░░░░░░░MEDIALOG░░░░░░░░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
    # ║░░░░░░░░░░░░░░░░░░░░░MEDIALOGTOGGLEBOTS░░░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
    # ║░░░░░░░░░░░░░░░░░░░░░░MEDIALOGTOGTYPES░░░░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
        view.message = await ctx.send(embed=view.create_embed(), view=view)


    # ╔════════════════════════════════════════════════════════════╗
    # ║░░░░░░░░░░░░░░░░░░░░░░░MEDIALOGGONFIG░░░░░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
    # ║░░░░░░░░░░░░░░░░░░░░MEDIALOGCONFIG.ENABLE░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
    # ║░░░░░░░░░░░░░░░░░░░MEDIALOGCONFIG.DISABLE░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @medialogconfig.command()
    async def disable(self, ctx):
        """Disable advanced tracking"""
        await self._update_config(False, False)
        self.user_stats = {}
        self.server_stats = {'total_uploads': 0, 'total_deletes': 0}
        await ctx.send("❎ Advanced tracking disabled by **{ctx.author.display_name}** using normal configuration.")

    # ╔════════════════════════════════════════════════════════════╗
    # ║░░░░░░░░░░░░░░░░MEDIALOGCONFIG.FORCE_ENABLE░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
    # ║░░░░░░░░░░░░░░░░MEDIALOGCONFIG.FORCE_DISABLE░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
    # ║░░░░░░░░░░░░░░░░░░░░░░MEDIALOGGERSTATS░░░░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
    # ║░░░░░░░░░░░░░░░░░░░░░░MEDIALOGTRACKING░░░░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
    # ║░░░░░░░░░░░░░░░░░░░░░MEDIALOGADDCHANNEL░░░░░░░░░░░░░░░░░░░░░║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣░DISCORD░COMMANDS░╠════════════════════╣
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
