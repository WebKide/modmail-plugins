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
import re
from typing import Optional

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    # ╔════════════════════╦══════════════╦════════════════════════╗
    # ╠════════════════════╣CREATE_WEBHOOK╠════════════════════════╣
    # ╚════════════════════╩══════════════╩════════════════════════╝
    async def create_webhook(self, channel: discord.TextChannel) -> discord.Webhook:
        webhooks = await channel.webhooks()
        if webhooks:
            for webhook in webhooks:
                if webhook.user == self.bot.user:
                    return webhook
        
        avatar = await self.bot.user.avatar.read()
        return await channel.create_webhook(
            name=f"Quote Plugin - {self.bot.user.name}",
            avatar=avatar,
            reason="Quote command requires webhook"
        )

    # ╔════════════════════╦═════════════════════╦═════════════════╗
    # ╠════════════════════╣RESOLVE_MESSAGE LOGIC╠═════════════════╣
    # ╚════════════════════╩═════════════════════╩═════════════════╝
    async def resolve_message(self, ctx: commands.Context, query: str) -> Optional[discord.Message]:
        # Handle --clean flag
        clean = '--clean' in query
        query = query.replace('--clean', '').strip()

        # Message ID lookup
        if query.isdigit():
            try:
                return await ctx.channel.fetch_message(int(query)), clean
            except discord.NotFound:
                pass

        # Message URL parsing
        if query.startswith(('http://', 'https://')):
            try:
                pattern = r'https?://(?:ptb\.|canary\.)?discord\.com/channels/(?P<guild_id>[0-9]+)/(?P<channel_id>[0-9]+)/(?P<message_id>[0-9]+)'
                match = re.match(pattern, query)
                if match:
                    guild_id = int(match.group('guild_id'))
                    channel_id = int(match.group('channel_id'))
                    message_id = int(match.group('message_id'))
                    # Check if guild is accessible
                    guild = self.bot.get_guild(guild_id)
                    if not guild or guild not in ctx.author.mutual_guilds:
                        return None, clean
                    # Check if user has access to the guild
                    channel = guild.get_channel(channel_id)
                    if isinstance(channel, discord.TextChannel):
                        return await channel.fetch_message(message_id), clean
            except (ValueError, discord.NotFound, discord.Forbidden):
                pass

        # Message searc by Content (in current channel message history for matching content)
        async for message in ctx.channel.history(limit=100):
            if query.lower() in message.content.lower():
                return message, clean

        return None, clean

    # ╔════════════════════╦═════════════════════╦═════════════════╗
    # ╠════════════════════╣QUOTE_MESSAGE COMMAND╠═════════════════╣
    # ╚════════════════════╩═════════════════════╩═════════════════╝
    @commands.command(name="quote", aliases=["q"])
    @commands.guild_only()
    async def quote_message(self, ctx: commands.Context, *, query: str):
        """Quote any message by ID, link, or content search
        ```css
        {prefix}quote 1234567890
        {prefix}quote Hello World
        {prefix}q https://discord/123/456/789
        {prefix}q 1234567890 --clean (OWNER only)```"""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        message, clean = await self.resolve_message(ctx, query)
        if not message:
            return await ctx.send("❌ Message not found or inaccessible", delete_after=10)

        # Verify clean flag permission
        if clean:
            if not await checks.has_permissions(PermissionLevel.OWNER).predicate(ctx):
                clean = False
                await ctx.send("⚠️ Clean mode is owner-only", delete_after=5)

        webhook = await self.create_webhook(ctx.channel)
        
        # Build components
        content = message.content
        files = []
        embeds = message.embeds.copy() if message.embeds else []
        
        # Handle attachments
        for attachment in message.attachments:
            try:
                files.append(await attachment.to_file())
            except:
                continue

        # Add reference (unless --clean mode)
        if not clean:
            reference = f"[↑ 𝖮𝗋𝗂𝗀𝗂𝗇𝖺𝗅 𝖬𝖾𝗌𝗌𝖺𝗀𝖾]({message.jump_url}) | `𝖨𝖣: {message.id}`"
            if len(embeds) < 10:
                embeds.append(discord.Embed(
                    description=reference,
                    color=message.author.color
                ))
            else:
                content = f"{content}\n\n{reference}" if content else reference

        # Send message
        webhook_msg = await webhook.send(
            content=content,
            username=message.author.display_name,
            avatar_url=message.author.display_avatar.url,
            embeds=embeds,
            files=files,
            allowed_mentions=discord.AllowedMentions.none(),
            wait=True
        )

        # Add original message’s reactions, if available
        if message.reactions:
            try:
                quoted_msg = await ctx.channel.fetch_message(webhook_msg.id)
                for reaction in message.reactions:
                    try:
                        await quoted_msg.add_reaction(reaction.emoji)
                    except:
                        continue
            except discord.Forbidden:
                pass

async def setup(bot):
    await bot.add_cog(Quote(bot))
