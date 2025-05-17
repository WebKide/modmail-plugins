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
import discord
from discord.ext import commands
from typing import Optional

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def create_webhook(self, channel: discord.TextChannel) -> discord.Webhook:
        # Check if there's already a webhook we can use
        webhooks = await channel.webhooks()
        if webhooks:
            for webhook in webhooks:
                if webhook.user == self.bot.user:
                    return webhook

        # Create a new webhook if none exist
        avatar = await self.bot.user.avatar.read()
        webhook = await channel.create_webhook(
            name=f"Quote Bot - {self.bot.user.name}",
            avatar=avatar,
            reason="Quote command requires webhook"
        )
        return webhook

    async def find_message(self, ctx: commands.Context, query: str) -> Optional[discord.Message]:
        # Check if query is a message ID
        if query.isdigit():
            try:
                return await ctx.channel.fetch_message(int(query))
            except discord.NotFound:
                pass

        # Check if query is a message link
        if query.startswith(('http://', 'https://')):
            try:
                # Extract message ID from URL
                parts = query.split('/')
                message_id = int(parts[-1])
                return await ctx.channel.fetch_message(message_id)
            except (ValueError, IndexError, discord.NotFound):
                pass

        # Search through message history for matching content
        async for message in ctx.channel.history(limit=100):
            if query.lower() in message.content.lower():
                return message

        return None

    @commands.command(name="quote", aliases=["q"])
    async def quote_message(self, ctx: commands.Context, *, query: str):
        """Quote a message by ID, link, or content search"""
        # Delete the original command message if we have permissions
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        message = await self.find_message(ctx, query)
        if not message:
            return await ctx.send("Could not find a message matching your query.", delete_after=10)

        # Create or get existing webhook
        webhook = await self.create_webhook(ctx.channel)

        # Prepare the webhook payload
        files = []
        embeds = []

        # Add message content
        content = message.content

        # Add message attachments as files
        for attachment in message.attachments:
            try:
                file = await attachment.to_file()
                files.append(file)
            except:
                pass

        # Add message embeds
        if message.embeds:
            embeds = message.embeds

        # Add reference to original message
        reference_text = f"[↑ 𝖮𝗋𝗂𝗀𝗂𝗇𝖺𝗅 𝖬𝖾𝗌𝗌𝖺𝗀𝖾]({message.jump_url})"
        if embeds and len(embeds) < 10:  # Discord allows max 10 embeds
            embed = discord.Embed(description=reference_text, color=message.author.color)
            embeds.append(embed)
        else:
            if content:
                content += f"\n\n{reference_text}"
            else:
                content = reference_text

        # Send the webhook
        await webhook.send(
            content=content,
            username=message.author.display_name,
            avatar_url=message.author.display_avatar.url,
            embeds=embeds,
            files=files,
            allowed_mentions=discord.AllowedMentions.none()
        )

async def setup(bot):
    await bot.add_cog(Quote(bot))
