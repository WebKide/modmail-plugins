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

import asyncio
import datetime
import logging
import random
from typing import Dict, Optional

import aiohttp
import discord
from core import checks
from core.models import PermissionLevel
from discord import Webhook
from discord.ext import commands, tasks

logger = logging.getLogger("Modmail")
__version__ = "0.2"

DEFAULT_DISCLAIMER = """# Welcome to VentSystem
-# Modmail-plugin by **WebKide**

🔰 This is an **anonymous venting space** powered by VentSystem.

By participating you accept the following ToS:
- Your identity will be hidden from other members*
- Moderators can see your identity if needed for safety reasons
- Messages are logged with your identity for moderation purposes
- Abuse of this system will result in sanctions"""

class VentSession:
    def __init__(self, user_id: int, thread: discord.Thread):
        self.user_id = user_id
        self.thread = thread
        self.expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        self.last_activity = datetime.datetime.utcnow()

class VentConfirmationView(discord.ui.View):
    def __init__(self, bot, thread: discord.Thread):
        super().__init__(timeout=300.0)
        self.bot = bot
        self.thread = thread

    async def on_timeout(self):
        """Handle view timeout by cancelling the session"""
        try:
            await self.thread.delete()
            logger.info(f"Vent session timed out for thread {self.thread.id}")
        except discord.NotFound:
            pass
        self.stop()

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✅")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle acceptance of vent terms"""
        try:
            # Update the embed
            embed = interaction.message.embeds[0].copy()
            embed.add_field(
                name=f"Vent Session accepted by {interaction.user.display_name}",
                value="Your messages are posted anonymously, but Moderators can still see the original messages you sent.",
                inline=False
            )

            # Unlock the thread for the user
            await self.thread.edit(
                locked=False,
                reason=f"Vent session accepted by {interaction.user}"
            )

            # Add user to thread if not already added
            await self.thread.add_user(interaction.user)

            # Update the message
            await interaction.response.edit_message(
                embed=embed,
                view=None,
                content=None
            )

            # Log the acceptance
            logger.info(f"Vent session accepted by {interaction.user} in thread {self.thread.id}")

        except Exception as e:
            logger.error(f"Error accepting vent session: {e}")
            await interaction.response.send_message(
                "Failed to start vent session. Please contact moderators.",
                ephemeral=True
            )
            await self.thread.delete()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle cancellation of vent session"""
        try:
            # Delete the thread
            await self.thread.delete()

            # Update the interaction message
            await interaction.response.edit_message(
                content="Vent session cancelled. The thread has been deleted.",
                embed=None,
                view=None
            )

            # Log the cancellation
            logger.info(f"Vent session cancelled by {interaction.user} for thread {self.thread.id}")

        except Exception as e:
            logger.error(f"Error cancelling vent session: {e}")
            await interaction.response.send_message(
                "Failed to cancel vent session properly. Please contact moderators.",
                ephemeral=True
            )

class VentSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.active_sessions: Dict[int, VentSession] = {}
        self.initial_blacklist = ["slur1", "slur2"]
        self.initial_crisis_phrases = ["suicide", "self harm", "kill myself"]
        self.initial_support_phrases = ["depressed", "lonely", "sad"]
        self.session_cleanup.start()

    def cog_unload(self):
        self.session_cleanup.cancel()

    @tasks.loop(minutes=5)
    async def session_cleanup(self):
        """Clean up expired vent sessions"""
        now = datetime.datetime.utcnow()
        to_remove = []

        for user_id, session in self.active_sessions.items():
            if now > session.expires_at:
                try:
                    if not session.thread:
                        continue
                    prefix = (await self.bot.get_prefix(session.thread))[0]
                    await session.thread.send(f"This vent session has expired. Use the `{prefix}vent` command again if you need to continue.")
                    await session.thread.edit(archived=True, locked=True)
                    to_remove.append(user_id)
                except Exception as e:
                    logger.error(f"Failed to clean up vent session for {user_id}: {e}")

        for user_id in to_remove:
            self.active_sessions.pop(user_id, None)

    @tasks.loop(hours=24)
    async def privacy_reminder(self):
        """Send daily privacy reminders"""
        async for config in self.db.find({"is_setup": True}):
            try:
                guild_id = int(config["_id"].split("_")[1])
                channel = self.bot.get_channel(config["vent_channel_id"])
                if channel:
                    await channel.send(
                        "**Reminder:** This is an anonymous venting space. "
                        "Moderators can see original authors if needed for safety reasons."
                    )
            except Exception as e:
                logger.error(f"Failed to send privacy reminder for {config['_id']}: {e}")


    @commands.command(name="setupvent")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def setup_vent(self, ctx):
        """Setup the vent system with required channels"""
        # Create VENTSYSTEM category if not exists
        support_category = discord.utils.get(ctx.guild.categories, name="VENTSYSTEM")
        if not support_category:
            support_category = await ctx.guild.create_category("VENTSYSTEM")

        # Create vent channel with proper permissions
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=False,
                read_message_history=True,
                add_reactions=True
            ),
            ctx.guild.me: discord.PermissionOverwrite(
                manage_messages=True,
                manage_threads=True,
                manage_webhooks=True,
                send_messages=True,
                view_channel=True
            )
        }

        vent_channel = await ctx.guild.create_text_channel(
            "anon-vent",
            category=support_category,
            overwrites=overwrites,
            topic="Anonymous venting space powered by **VentSystem**."
            "Messages here are sent anonymously via webhook."
        )

        # Create webhook for anonymous posting
        webhook = await vent_channel.create_webhook(name="Vent System")

        # Save configuration
        await self.db.update_one(
            {"_id": f"config_{ctx.guild.id}"},
            {"$set": {
                "is_setup": True,
                "vent_channel_id": vent_channel.id,
                "webhook_url": webhook.url,
                "created_at": datetime.datetime.utcnow()
            }},
            upsert=True
        )

        embed = discord.Embed(
            title="VentSystem Setup Complete",
            description=f"""
            **Created:**
            - Channel: {vent_channel.mention}

            **How it works:**
            1. Users use `{ctx.prefix}vent` to start a private thread
            2. They vent in the thread (only visible to them and mods)
            3. Messages are anonymously posted to {vent_channel.mention}
            4. After 30 minutes, the thread auto-closes
            """,
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="vent")
    @checks.has_permissions(PermissionLevel.REGULAR)
    @commands.guild_only()
    async def vent_command(self, ctx):
        """Start an anonymous venting session"""
        config = await self.db.find_one({"_id": f"config_{ctx.guild.id}", "is_setup": True})
        if not config:
            return await ctx.send("This server hasn't set up **VentSystem** yet.")

        if ctx.author.id in self.active_sessions:
            session = self.active_sessions[ctx.author.id]
            if session.thread:
                return await ctx.send(f"You already have an active vent session in {session.thread.mention}")

        try:
            vent_channel = self.bot.get_channel(config["vent_channel_id"])
            
            # Create private thread - threads inherit parent channel permissions by default
            thread = await vent_channel.create_thread(
                name=f"Vent-{ctx.author.display_name}",
                type=discord.ChannelType.private_thread,
                reason="Anonymous vent session"
            )

            # Add user to thread (this grants them access)
            await thread.add_user(ctx.author)

            # Store session
            self.active_sessions[ctx.author.id] = VentSession(ctx.author.id, thread)

            # Create and send the embed with accept/cancel buttons
            embed = discord.Embed(
                title="Private Venting Space",
                description=(
                    f"{ctx.author.mention}, this is your private vent space.\n"
                    f"Messages here will be anonymously posted to {vent_channel.mention}.\n\n"
                    f"{DEFAULT_DISCLAIMER}\n\n"
                    f"⏳ Session will expire in 30 minutes."
                ),
                color=0x7289da
            )
            embed.set_thumbnail(url="https://i.imgur.com/Dym0InE.png")
            embed.set_image(url="https://i.imgur.com/Cr96Hps.png")
            embed.set_footer(text=f"Use {ctx.prefix}vent to start a new session after this one expires")

            # Send the embed with the confirmation view
            view = VentConfirmationView(self.bot, thread)
            await thread.send(embed=embed, view=view)

            await ctx.message.add_reaction("✅")

            # For moderators - we'll need to handle this differently
            # Either:
            # 1. Make sure mods have manage_threads permission in the parent channel, or
            # 2. Add them to each thread manually
            # Here's option #2:
            mod_role = discord.utils.get(ctx.guild.roles, name="Moderator")
            if mod_role:
                for member in mod_role.members:
                    try:
                        await thread.add_user(member)
                    except discord.HTTPException:
                        continue

        except Exception as e:
            logger.error(f"Failed to create vent session: {e}")
            await ctx.send("Failed to create vent session. Please try again.")
            if 'thread' in locals():
                await thread.delete()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle messages in vent threads"""
        if message.author.bot or not isinstance(message.channel, discord.Thread):
            return

        # Check if this is a vent thread
        session = self.active_sessions.get(message.author.id)
        if not session or session.thread.id != message.channel.id:
            return

        # Update last activity
        session.last_activity = datetime.datetime.utcnow()

        config = await self.db.find_one({"_id": f"config_{message.guild.id}", "is_setup": True})
        if not config:
            return await message.channel.send("Vent system is not configured properly.")

        try:
            # Post anonymously to vent channel
            async with aiohttp.ClientSession() as http_session:
                webhook = Webhook.from_url(config["webhook_url"], session=http_session)
                await webhook.send(
                    content=message.content,
                    username=f"Anonymous-{random.randint(1000, 9999)}",
                    avatar_url="https://i.imgur.com/KZPWIkY.png",
                    wait=True
                )

            # Log the message (optional)
            await self.db.insert_one({
                "type": "vent_message",
                "guild_id": message.guild.id,
                "user_id": message.author.id,
                "content": message.content,
                "timestamp": datetime.datetime.utcnow()
            })

            await message.add_reaction("✅")
        except Exception as e:
            logger.error(f"Failed to process vent message: {e}")
            await message.channel.send("Failed to send your vent message. Please try again.")

async def setup(bot):
    await bot.add_cog(VentSystem(bot))
