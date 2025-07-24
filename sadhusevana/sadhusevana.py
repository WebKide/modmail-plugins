# sadhusevana.py

import asyncio
import json
import logging
import time
from datetime import datetime as t
import sys
import os
sys.path.append(os.path.dirname(__file__))

import discord
from discord.ext import commands, tasks

from core import checks
from core.models import PermissionLevel

from .sadhucore import SadhuUI, DisconnectionWarningView, TimezoneView
from .sadhubase import HardCoded  # dict with static strings of text

log = logging.getLogger("Modmail")
__version__ = "5.06"


class SadhuSevana(commands.Cog):
    """SadhuSevana* is a private Discord.py plugin for managing notifications and announcements for the Gauḍīya Vaiṣṇava podcasts in the **Sādhu Sevā Community** (est. 2016)
    ```
    ╔═╗╔═╗╔╦═╗╦ ╦╦ ╦
    ╚═╗╠═╣ ║░║╠═╣║ ║
    ╚═╝╩ ╩═╩═╝╩ ╩╚═╝
    ╔═╗╔═╗╦ ╦╔═╗╔╗╦╔═╗
    ╚═╗╠═ ╚╗║╠═╣║║║╠═╣
    ╚═╝╚═╝ ╚╝╩ ╩╝╚╝╩ ╩```
    **Usage:**
    - React to any previous Notification with `Heartfelt` emoji
    - Invoke with command: `!radhe` or `!radhe extra [festival]`
    """
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self._config_cache = {}
        self.notification_messages = {}  # Track notification messages for reaction handling
        self.voice_cleanup.start()  # Track voice channel disconnection task
        self.showtimes_messages = {}  # Track showtimes messages for reaction handling

    async def get_guild_config(self, guild_id):
        """Retrieve or create guild configuration with caching"""
        # Check cache first
        if guild_id in self._config_cache:
            return self._config_cache[guild_id]

        # Fetch from database
        config = await self.db.find_one({"_id": str(guild_id)})

        if not config:
            # Create default config if none exists
            default_config = {
                "_id": str(guild_id),
                "target_guild": guild_id,
                "target_channel": None,
                "timezones": HardCoded["DEFAULT_TIMEZONES"],
                "speaker": "and speaker",
                "ping_role": None,
                "voice_channel": None,
                "last_updater": t.now().timestamp()
            }
            await self.db.insert_one(default_config)
            self._config_cache[guild_id] = default_config
            return default_config

        # Ensure all fields exist
        defaults = {
            "timezones": HardCoded["DEFAULT_TIMEZONES"],
            "speaker": "and speaker",
            "ping_role": None,
            "voice_channel": None
        }

        for key, value in defaults.items():
            if key not in config:
                config[key] = value

        # Convert timestamp back to datetime if needed
        if isinstance(config.get("last_updater"), (int, float)):
            config["last_updater"] = t.fromtimestamp(config["last_updater"])

        self._config_cache[guild_id] = config
        return config

    async def clear_config_cache(self, guild_id):
        """Clear cached config for a guild"""
        self._config_cache.pop(guild_id, None)

    async def update_config(self, guild_id, update_data):
        """Update guild configuration using Modmail's plugin_db"""
        # Convert datetime to timestamp for storage
        try:
            if "last_updater" in update_data:  # if "last_updater" in update_data and isinstance(update_data["last_updater"], t):
                update_data["last_updater"] = t.now().timestamp()  # update_data["last_updater"] = update_data["last_updater"].timestamp()

            # Use proper MongoDB update operator syntax
            result = await self.db.update_one(
                {"_id": str(guild_id)},
                {"$set": update_data},
                upsert=True
            )
            if result.matched_count or result.upserted_id:
                await self.clear_config_cache(guild_id)
            return result
        except Exception as e:
            log.error(f"Error updating config for {guild_id}: {str(e)}")
            raise

    async def partial_update(self, guild_id, update_dict):
        """Update only specific fields"""
        if not isinstance(update_dict, dict):
            raise ValueError("update_dict must be a dictionary")

        await self.db.update_one(
            {"_id": str(guild_id)},
            {"$set": update_dict},
            upsert=False  # Don't create if doesn't exist
        )
        await self.clear_config_cache(guild_id)

    async def store_notification(self, message_data):
        await self.db.update_one(
            {"_id": "notifications"},
            {"$set": {str(message_data['message_id']): message_data}},
            upsert=True
        )

    async def get_notification(self, message_id):
        data = await self.db.find_one({"_id": "notifications"})
        return data.get(str(message_id)) if data else None

    async def cleanup_old_notifications(self):
        """Clean up notifications and showtimes messages older than 24 hours"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                # Clean up notifications
                day_ago = t.now().timestamp() - 86400
                notifications_doc = await self.db.find_one({"_id": "notifications"})
                if notifications_doc:
                    old_keys = [k for k, v in notifications_doc.items() 
                               if k != '_id' and isinstance(v, dict) and v.get('timestamp', 0) < day_ago]
                    if old_keys:
                        unset_dict = {k: "" for k in old_keys}
                        await self.db.update_one(
                            {"_id": "notifications"},
                            {"$unset": unset_dict}
                        )

                # Clean up showtimes messages
                old_showtimes = [msg_id for msg_id, data in self.showtimes_messages.items()
                                if t.now().timestamp() - data.get('timestamp', t.now().timestamp()) > 86400]
                for msg_id in old_showtimes:
                    self.showtimes_messages.pop(msg_id, None)

            except Exception as e:
                log.error(f"Error in cleanup iteration: {str(e)}")
            await asyncio.sleep(3600)  # Run hourly

    async def cog_unload(self):
        self.voice_cleanup.cancel()
        self.cleanup_task.cancel()
        try:
            await self.cleanup_task
        except asyncio.CancelledError:
            pass

    # ╔════════════════╦══════════════════════╦════════════════════╗
    # ╠════════════════╣CONFIGURATION COMMANDS╠════════════════════╣
    # ╚════════════════╩══════════════════════╩════════════════════╝
    @commands.command(name="setup_notifications", description="Configure notification settings for this guild")
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def _setup_notifications(self, ctx):
        """Interactive setup for notification configuration"""
        # Step 1: Get target channel
        await ctx.send("Please provide the target channel for notifications (mention, ID, name, or link):", delete_after=60)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', timeout=60, check=check)
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                try:
                    await msg.delete()
                except discord.HTTPException:
                    pass
            target_channel = None

            # Method A) Channel mention
            if msg.channel_mentions:
                target_channel = msg.channel_mentions[0]
            else:
                content = msg.content.strip()

                # Method B) Channel ID (numeric)
                if content.isdigit():
                    target_channel = self.bot.get_channel(int(content))

                # Method C) Channel link (discord.com/channels/guild_id/channel_id)
                elif 'discord.com/channels/' in content:
                    try:
                        # Extract channel ID from URL
                        parts = content.split('/')
                        if len(parts) >= 2:
                            channel_id = parts[-1].split('?')[0]  # Remove any query parameters
                            if channel_id.isdigit():
                                target_channel = self.bot.get_channel(int(channel_id))
                    except (ValueError, IndexError):
                        pass

                # Method D) Channel name (with or without #)
                else:
                    channel_name = content.lstrip('#').lower()
                    # Search through guild channels
                    for channel in ctx.guild.channels:
                        if isinstance(channel, discord.TextChannel) and channel.name.lower() == channel_name:
                            target_channel = channel
                            break

            if not target_channel:
                return await ctx.send("❌ Could not find that channel. Please try again with a valid channel mention, ID, name, or link.", delete_after=15)

            # Verify the channel is in the same guild
            #if target_channel.guild.id != ctx.guild.id:
            #    return await ctx.send("❌ The channel must be in this server. Please try again.", delete_after=15)

        except asyncio.TimeoutError:
            return await ctx.send("Setup timed out. Please try again.", delete_after=9)

        # Step 2: Get speaker name
        await ctx.send("Please enter the speaker/host display name:", delete_after=50)
        try:
            msg = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author)
            speaker = msg.content
        except asyncio.TimeoutError:
            return await ctx.send("Setup timed out. Please try again.", delete_after=9)

        # Step 3: Get ping role
        await ctx.send("Please mention the role to ping (or type 'skip' to skip):", delete_after=50)
        try:
            msg = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author)
            if msg.content.lower() != 'skip' and msg.role_mentions:
                ping_role = msg.role_mentions[0].id
            else:
                ping_role = None
        except asyncio.TimeoutError:
            return await ctx.send("Setup timed out. Please try again.", delete_after=9)

        # Step 4: Set voice channel for disconnection feature
        await ctx.send(
            "Please specify the voice channel for auto-disconnection feature:\n"
            "• Mention: #channel-name\n"
            "• ID: 123456789012345678\n"
            "• Name: channel-name\n"
            "• Link: <https://discord.com/channels/...>\n"
            "• Or type 'skip' to skip:",
            delete_after=60
        )
        try:
            msg = await self.bot.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author)
            voice_channel = None

            if msg.content.lower() != 'skip':
                # Method A) Channel mention
                if msg.channel_mentions:
                    voice_channel = msg.channel_mentions[0].id
                else:
                    content = msg.content.strip()

                    # Method B) Discord link
                    if content.startswith('https://discord.com/channels/'):
                        try:
                            channel_id = int(content.split('/')[-1])
                            channel = ctx.guild.get_channel(channel_id)
                            if channel and isinstance(channel, discord.VoiceChannel):
                                voice_channel = channel.id
                            else:
                                await ctx.send("❌ Invalid voice channel link or channel not found.", delete_after=10)
                                return
                        except (ValueError, IndexError):
                            await ctx.send("❌ Invalid Discord channel link format.", delete_after=10)
                            return

                    # Method C) Channel ID (numeric)
                    elif content.isdigit():
                        channel_id = int(content)
                        channel = ctx.guild.get_channel(channel_id)
                        if channel and isinstance(channel, discord.VoiceChannel):
                            voice_channel = channel.id
                        else:
                            await ctx.send("❌ Channel ID not found or is not a voice channel.", delete_after=10)
                            return

                    # Method D) Channel name (with or without #)
                    else:
                        channel_name = content.lstrip('#').lower()
                        channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name)
                        if channel:
                            voice_channel = channel.id
                        else:
                            # Try partial matching
                            matches = [ch for ch in ctx.guild.voice_channels if channel_name in ch.name.lower()]
                            if len(matches) == 1:
                                voice_channel = matches[0].id
                            elif len(matches) > 1:
                                channel_list = ', '.join([f'#{ch.name}' for ch in matches[:5]])
                                await ctx.send(f"❌ Multiple voice channels found: {channel_list}\nPlease be more specific.", delete_after=15)
                                return
                            else:
                                await ctx.send("❌ Voice channel not found. Please check the name and try again.", delete_after=10)
                                return

                # Confirm the voice channel selection
                if voice_channel:
                    channel_obj = ctx.guild.get_channel(voice_channel)
                    await ctx.send(f"✅ Voice channel set to: **{channel_obj.name}**", delete_after=10)

        except asyncio.TimeoutError:
            return await ctx.send("Setup timed out. Please try again.", delete_after=9)

        # Save configuration
        await self.update_config(ctx.guild.id, {
            "target_channel": target_channel.id,
            "speaker": speaker,
            "ping_role": ping_role,
            "voice_channel": voice_channel,
            "last_updater": t.now().timestamp()
        })

        await ctx.send(f"# ✅ Sādhu Sevā Community configuration saved!\n"
                        f"**Text Channel:** {target_channel.mention}\n"
                        f"**Speaker:** {speaker}\n"
                        f"**Ping Role:** {f'<@&{ping_role}>' if ping_role else 'None'}\n"
                        f"**Voice Channel:** {f'<#{voice_channel}>' if voice_channel else 'None'}")

    @commands.command(name="debug_private_config", description="View your configurations")
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def _debug_private_config(self, ctx):
        """Show the current guild configuration"""
        config = await self.get_guild_config(ctx.guild.id)

        printable_config = {
            "_id": config.get("_id"),
            "target_channel": config.get("target_channel"),
            "speaker": config.get("speaker"),
            "ping_role": config.get("ping_role"),
            "voice_channel": config.get("voice_channel"),
            "timezones": config.get("timezones", {}),
            "last_updater": str(config.get("last_updater"))
        }

        await ctx.send(f"Current `config` for **SadhuSevana** plugin:\n```json\n{json.dumps(printable_config, indent=2, ensure_ascii=False)}\n```")

    @commands.command(name="reset_timezones", description="Reset timezone configurations")
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def reset_timezones(self, ctx):
        """Reset timezones to default"""
        await self.update_config(ctx.guild.id, {
            "timezones": HardCoded["DEFAULT_TIMEZONES"],
            "last_updater": t.now()
        })
        await ctx.send("✅ Timezones reset to defaults!", delete_after=9)

    @commands.command(name="set_timezones", description="Set timezones using interactive buttons")
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def set_timezones(self, ctx):
        """Interactive timezone setup menu using buttons"""
        # Create and send the embed with buttons
        view = TimezoneView(self, ctx)
        embed = discord.Embed(
            title="Timezone Setup",
            description="Click the buttons to select/deselect timezones:\n"
                        "Green = Selected | Grey = Not Selected\n\n"
                        "Click **✅ Done** when finished.",
            color=discord.Color.blue()
        )

        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="showtimes", aliases=['times', 'alltimes'])
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def show_all_times(self, ctx):
        """Show current times for configured timezones"""
        try:
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                try:
                    await ctx.message.delete()
                except discord.Forbidden:
                    pass

            config = await self.get_guild_config(ctx.guild.id)
            timezones = config.get('timezones', HardCoded['DEFAULT_TIMEZONES'])

            if not timezones:
                msg = await ctx.send("⏰ No timezones configured. Use `!set_timezones` to set them up.")
                await msg.delete(delay=30)
                return

            # Get current UTC time
            now_utc = t.now()

            # Format timezone display using SadhuUI method
            time_display = SadhuUI.format_timezones(timezones)

            embed = discord.Embed(
                description=f"## Configured World times:\n{time_display}",
                color=discord.Color.blue(),
                timestamp=now_utc
            )
            embed.set_author(
                name=f"⌚ Current Times requested by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
            )
            embed.set_footer(text="React with ⏰ to refresh | To choose different ones, type !set_timezones")

            # Send the embed and add reaction
            if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
                await ctx.send("❌ Bot lacks permission to send embeds.", delete_after=10)
                return
            if not ctx.channel.permissions_for(ctx.guild.me).add_reactions:
                await ctx.send("❌ Bot lacks permission to add reactions.", delete_after=10)
                return
            message = await ctx.send(embed=embed)
            try:
                await message.add_reaction('⏰')
            except discord.HTTPException:
                log.warning("Failed to add ⏰ reaction to times embed")

            # Store message details
            self.showtimes_messages[message.id] = {
                'channel_id': ctx.channel.id,
                'guild_id': ctx.guild.id,
                'author_id': ctx.author.id,
                'config': config,
                'timestamp': t.now().timestamp()  # Add timestamp for cleanup
            }

        except Exception as e:
            log.error(f"Error in show_all_times: {str(e)}")
            msg = await ctx.send(f"❌ Error: {str(e)[:100]}")
            await msg.delete(delay=30)

    @commands.command(name="disconnect_all", aliases=['disconnect'], description="Disconnect all members from the configured voice channel")
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def disconnect_all(self, ctx):
        """Disconnect all members manually from voice channel"""
        try:
            if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                try:
                    await ctx.message.delete()
                except discord.Forbidden:
                    pass

            config = await self.get_guild_config(ctx.guild.id)
            voice_channel_id = config.get('voice_channel')

            if not voice_channel_id:
                msg = await ctx.send("❌ No voice channel configured for disconnection. Use `!setup_notifications` to set one.")
                await msg.delete(delay=10)
                return

            voice_channel = ctx.guild.get_channel(voice_channel_id)
            if not voice_channel:
                msg = await ctx.send("❌ Configured voice channel not found.")
                await msg.delete(delay=10)
                return

            if not isinstance(voice_channel, discord.VoiceChannel):
                msg = await ctx.send("❌ Configured channel is not a voice channel.")
                await msg.delete(delay=10)
                return

            # Check if there are members to disconnect
            if not voice_channel.members:
                msg = await ctx.send(f"ℹ️ No members in **{voice_channel.name}** to disconnect.")
                await msg.delete(delay=10)
                return

            # Get member count before disconnection
            member_count = len(voice_channel.members)
            member_names = [member.display_name for member in voice_channel.members[:10]]  # Show up to 10 names

            # Disconnect all members
            disconnected = 0
            failed = 0

            for member in voice_channel.members.copy():  # Use copy to avoid issues during iteration
                try:
                    await member.move_to(None)
                    disconnected += 1
                    log.info(f"Disconnected {member.display_name} from {voice_channel.name}")
                except discord.HTTPException as e:
                    failed += 1
                    log.error(f"Failed to disconnect {member.display_name}: {str(e)}")

            # Send confirmation
            if member_count <= 10:
                members_text = ", ".join(member_names)
            else:
                members_text = f"{', '.join(member_names)} and {member_count - 10} others"

            success_msg = f"✅ Disconnected **{disconnected}** member{'s' if disconnected != 1 else ''} from **{voice_channel.name}**"
            if failed > 0:
                success_msg += f"\n⚠️ Failed to disconnect {failed} member{'s' if failed != 1 else ''}"

            success_msg += f"\n**Members:** {members_text}"
            await ctx.send(success_msg)

        except Exception as e:
            log.error(f"Error in disconnect_all command: {str(e)}")
            msg = await ctx.send(f"❌ Error disconnecting members: {str(e)[:100]}")
            await msg.delete(delay=10)

    # ╔════════════════╦═════════════════════╦═════════════════════╗
    # ╠════════════════╣NOTIFICATION COMMANDS╠═════════════════════╣
    # ╚════════════════╩═════════════════════╩═════════════════════╝
    @commands.command(description='Sends notification into same channel', aliases=['poke','rādhe'], no_pm=True)
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def radhe(self, ctx: commands.Context, *, event_today: str = None):
        """Send a push notification in the current channel"""
        config = await self.get_guild_config(ctx.guild.id)
        await self._send_notification(ctx, ctx.channel, event_today, config)

    @commands.command(description='Sends the push notification to the General channel', aliases=['nudge'], no_pm=True)
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def gaura(self, ctx, *, _event_today: str = None):
        """Send a push notification to the configured channel"""
        config = await self.get_guild_config(ctx.guild.id)
        target_channel_id = config.get('target_channel')
        if not target_channel_id:
            return await ctx.send("No target channel configured! Please run `!setup_notifications` first.", delete_after=10)
        target_channel = self.bot.get_channel(target_channel_id)

        if not target_channel:
            return await ctx.send("Couldn't find the target channel! Please configure one first.", delete_after=10)

        await self._send_notification(ctx, target_channel, _event_today, config)

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣NOTIFICATION LOGIC╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    async def _send_notification(self, ctx, channel, _event_today=None, config=None):
        """Notification sending logic"""
        if config is None:
            config = await self.get_guild_config(channel.guild.id)

        # Handle both Context and Member objects for ctx parameter
        is_context = isinstance(ctx, commands.Context)
        author = ctx if isinstance(ctx, discord.Member) else ctx.author

        # Only try to delete if triggered by command
        if is_context and channel.id != ctx.channel.id:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

        start_time = time.time()

        # Get ping role if configured
        ping_role = config.get('ping_role')
        _poke = f'<@&{ping_role}> || ℍ𝕒𝕣𝕚 𝕜𝕒𝕥𝕙𝕒̄ 𝖯𝗎𝗌𝗁-𝗇𝗈𝗍𝗂𝖿𝗂𝖼𝖺𝗍𝗂𝗈𝗇 ||' if ping_role else 'ℍ𝕒𝕣𝕚 𝕜𝕒𝕥𝕙𝕒̄ 𝖯𝗎𝗌𝗁-𝗇𝗈𝗍𝗂𝖿𝗂𝖼𝖺𝗍𝗂𝗈𝗇 @here'

        # Create and send the notification embed
        embed = SadhuUI.create_notification_embed(
            channel.guild,
            author,
            config,
            _event_today,
            self.bot.latency
        )

        try:
            message = await channel.send(content=_poke, embed=embed)
        except discord.Forbidden:
            # Fallback to simple message if embed fails
            simple_msg = f"{_poke}\n{SadhuUI.format_timezones(config.get('timezones', HardCoded['DEFAULT_TIMEZONES']))}\n\n"
            simple_msg += SadhuUI.generate_intro_text(channel.guild.name, config.get('speaker', 'and speaker'))
            message = await channel.send(simple_msg)

        # Store the message for reaction handling
        self.notification_messages[message.id] = {
            'channel_id': channel.id,
            'guild_id': channel.guild.id,
            'config': config,
            'author_id': author.id,
            'content': _event_today,
            'timestamp': t.now().timestamp()
        }

        # Add reactions
        try:
            await asyncio.sleep(1)
            await message.add_reaction('thankful:695101751707303998')
        except discord.HTTPException:
            pass

        # Send confirmation to original text channel
        if is_context and channel.id != ctx.channel.id:
            try:
                confirmation = await ctx.send(
                    f"ℍ𝕒𝕣𝕚 𝕜𝕒𝕥𝕙𝕒̄ Push-Notification sent to **{channel.mention}**! \nSent in {self.bot.latency*1000:.2f}ms'"
                )
                await asyncio.sleep(2)
                await confirmation.add_reaction('✅')
            except discord.HTTPException:
                pass

    # ╔════════════════════╦════════════╦══════════════════════════╗
    # ╠════════════════════╣COG.LISTENER╠══════════════════════════╣
    # ╚════════════════════╩════════════╩══════════════════════════╝
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reaction adds for reminder notifications and showtimes refresh"""
        # Early filter: Only process ⏰ or :Heartfelt: reactions
        if payload.emoji.name != '⏰' and str(payload.emoji) != '<:Heartfelt:525716509830414347>':
            return

        try:
            # Early filter for bot users
            if payload.user_id == self.bot.user.id:
                return

            # Get channel and message objects
            channel = self.bot.get_channel(payload.channel_id)
            if not channel:
                return

            try:
                message = await channel.fetch_message(payload.message_id)
            except discord.NotFound:
                return

            # Handle times refresh (⏰ reaction)
            if payload.emoji.name == '⏰' and message.id in self.showtimes_messages:
                await self._handle_times_refresh(payload, message, member, channel)
                return

            # Get member and check permissions
            member = channel.guild.get_member(payload.user_id)
            if not member:
                return

            # Check if user has mod permissions
            is_mod = any(role.name.lower() in ['admin', 'mod', 'moderator'] for role in member.roles)
            
            if not is_mod:
                # Add "honguito" reaction for non-mods
                try:
                    # Use proper custom emoji
                    await message.add_reaction('<:honguito:760097006005256225>')
                except discord.HTTPException:
                    pass
                return

            # Handle notification reaction (<:Heartfelt:525716509830414347>)
            if str(payload.emoji) == '<:Heartfelt:525716509830414347>' and "𝖯𝗎𝗌𝗁-𝗇𝗈𝗍𝗂𝖿𝗂𝖼𝖺𝗍𝗂𝗈𝗇" in message.content:
                await self._handle_heartfelt_reaction(payload, message, member, channel)
                return
                
        except Exception as e:
            log.error(f"Reaction handler error: {str(e)}", exc_info=True)
            if 'channel' in locals():
                try:
                    await channel.send("⚠️ Failed to process reaction", delete_after=10)
                except discord.HTTPException:
                    pass

    async def _handle_times_refresh(self, payload, message, member, channel):
        """Handle times refresh reaction"""
        try:
            msg_data = self.showtimes_messages[message.id]
            config = msg_data['config']

            # Format updated timezone display
            time_display = SadhuUI.format_timezones(config.get('timezones', HardCoded['DEFAULT_TIMEZONES']))

            # Create updated embed
            embed = discord.Embed(
                description=f"## Selected World times:\n{time_display}",
                color=discord.Color.blue(),
                timestamp=t.now()
            )
            embed.set_author(
                name=f"⌚ Current Times requested by {member.display_name}",
                icon_url=member.avatar.url if member.avatar else member.default_avatar.url
            )
            embed.set_footer(text="Click ⏰ to refresh | To choose different ones, type !set_timezones")

            # Update the message
            try:
                await message.edit(embed=embed)
                # Remove the user's reaction
                if channel.permissions_for(channel.guild.me).manage_messages:
                    await message.remove_reaction(payload.emoji, member)
            except discord.HTTPException as e:
                log.error(f"Failed to update showtimes message: {str(e)}")
                await channel.send("⚠️ Failed to refresh", delete_after=10)

        except Exception as e:
            log.error(f"Times refresh error: {str(e)}", exc_info=True)

    async def _handle_heartfelt_reaction(self, payload, message, member, channel):
        """Handle heartfelt notification reaction"""
        try:
            # Remove the mod's reaction
            try:
                await message.remove_reaction(payload.emoji, member)
            except discord.HTTPException:
                pass

            # Resend notification
            await self._send_notification(
                ctx=member,
                channel=channel,
                _event_today=None,
                config=await self.get_guild_config(channel.guild.id)
            )

        except Exception as e:
            log.error(f"Heartfelt reaction error: {str(e)}", exc_info=True)
            if 'channel' in locals():
                try:
                    await channel.send("⚠️ Failed to process reaction", delete_after=10)
                except discord.HTTPException:
                    pass

    @tasks.loop(minutes=2)
    async def voice_cleanup(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(328341202103435264)
        _bot_logs_channel = discord.utils.get(guild.text_channels, name="bot-logs")
        for guild_id in self._config_cache:
            try:
                return  # early finish

                log.info(f"Checking voice cleanup for guild {guild_id}")
                config = await self.get_guild_config(guild_id)
                voice_channel_id = config.get('voice_channel')
                if not voice_channel_id:
                    await _bot_logs_channel.send(f"No voice channel configured for guild {guild_id}")
                    continue

                voice_channel = self.bot.get_channel(voice_channel_id)
                if not voice_channel or not isinstance(voice_channel, discord.VoiceChannel) or not voice_channel.members:
                    await _bot_logs_channel.send(f"No valid voice channel or no members in {voice_channel_id} for guild {guild_id}")
                    continue

                # Find bot-logs channel by name or ID
                bot_logs_channel = discord.utils.get(voice_channel.guild.text_channels, name="bot-logs")
                if not bot_logs_channel:
                    bot_logs_channel = voice_channel.guild.get_channel(727278644396949585)
                if not bot_logs_channel or not bot_logs_channel.permissions_for(voice_channel.guild.me).send_messages:
                    log.warning(f"No accessible bot-logs channel found for guild {guild_id}")
                    continue

                # Check for a recent notification for this guild
                notification = None
                current_time = t.now().timestamp()
                
                # FIXED: Check if notification is OLD ENOUGH (2 hours = 7200 seconds)
                for msg_id, data in self.notification_messages.items():
                    if data['guild_id'] == guild_id:
                        time_since_notification = current_time - data.get('timestamp', 0)
                        # Only proceed if notification is AT LEAST 2 hours old
                        if time_since_notification >= 7200:
                            notification = data
                            await bot_logs_channel.send(f"Found notification from {time_since_notification/3600:.1f} hours ago for guild {guild_id}")
                            break
                        else:
                            await bot_logs_channel.send(f"Notification too recent ({time_since_notification/3600:.1f} hours ago) for guild {guild_id}")
                
                if not notification:
                    await bot_logs_channel.send(f"No notification old enough (2+ hours) found for guild {guild_id}")
                    continue

                # Check permissions
                target_channel_id = config.get('target_channel')
                target_channel = self.bot.get_channel(target_channel_id)
                if not target_channel or not target_channel.permissions_for(target_channel.guild.me).send_messages:
                    log.warning(f"Cannot send messages to target channel {target_channel_id} for guild {guild_id}")
                    continue
                if not voice_channel.permissions_for(target_channel.guild.me).move_members:
                    await bot_logs_channel.send(f"Missing move_members permission for voice channel {voice_channel_id}")
                    await bot_logs_channel.send("⚠️ Cannot disconnect members: Bot lacks `move_members` permission", delete_after=120)
                    continue

                # Send warning
                await bot_logs_channel.send(f"Sending disconnection warning for {len(voice_channel.members)} members in {voice_channel.name}")
                warning_embed = SadhuUI.create_disconnection_warning_embed(voice_channel.guild, voice_channel.members)
                warning_view = DisconnectionWarningView(voice_channel)
                warning_message = await bot_logs_channel.send(embed=warning_embed, view=warning_view)

                # Wait for 30 seconds or cancellation
                await warning_view.wait()
                if warning_view.cancelled:
                    await bot_logs_channel.send("Voice channel cleanup was cancelled by a moderator")
                    try:
                        await warning_message.delete()
                    except discord.HTTPException:
                        pass
                    continue

                # Disconnect members
                await bot_logs_channel.send(f"Disconnection of members was automatically triggered for **{voice_channel.name}**")
                '''
                disconnected = 0
                for member in voice_channel.members.copy():
                    try:
                        await member.move_to(None)
                        disconnected += 1
                        log.info(f"Disconnected {member.display_name} from {voice_channel.name}")
                    except discord.HTTPException as e:
                        log.error(f"Failed to disconnect {member.display_name}: {str(e)}")'''

                # Clean up the notification after processing
                if notification:
                    # Remove the processed notification so it doesn't trigger again
                    for msg_id, data in list(self.notification_messages.items()):
                        if data == notification:
                            del self.notification_messages[msg_id]
                            await bot_logs_channel.send(f"Removed processed notification {msg_id} from cache")
                            break

                # Clean up warning message
                try:
                    await warning_message.delete()
                    await bot_logs_channel.send(f"Deleted warning message {warning_message.id}")
                except discord.HTTPException as e:
                    await bot_logs_channel.send(f"Failed to delete warning message: {str(e)}")

                if disconnected > 0:
                    await bot_logs_channel.send(f"✅ Disconnected {disconnected} member(s) from {voice_channel.name}")
                else:
                    await bot_logs_channel.send(f"ℹ️ No members were disconnected from {voice_channel.name}")

            except Exception as e:
                log.error(f"Error in voice cleanup for guild {guild_id}: {str(e)}")
                if 'bot_logs_channel' in locals():
                    await bot_logs_channel.send(f"⚠️ Error during voice cleanup: {str(e)[:100]}", delete_after=120)

async def setup(bot):
    await bot.add_cog(SadhuSevana(bot))
