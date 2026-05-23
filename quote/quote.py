"""
MIT License
Copyright (c) 2020-2026 WebKide [d.id @323578534763298816]
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
from typing import Optional, Tuple

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

class Quote(commands.Cog):
    """
    Quote* plugin will search up to 100 messages back in the same channel
    For content searches, it will quote the first matching message found
    The quoted message will appear identical to the original, including:
    ├ Author name and avatar
    ├ Message content
    ├ Attachments (files, images, and media)
    └ Embeds
    A link to the original message is included at the bottom by default
    """
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

    async def resolve_message(self, ctx: commands.Context, query: str) -> Tuple[Optional[discord.Message], bool, Optional[discord.TextChannel], bool]:
        # Track if user explicitly supplied the flags "--clean" OR "--channel"
        has_channel_flag = False
        target_channel = None

        # Check and resolve custom destination target via --channel flag
        channel_match = re.search(r'--channel\s+(?:<#)?([0-9]+)>?', query)
        if channel_match:
            has_channel_flag = True
            chan_id = int(channel_match.group(1))
            target_channel = ctx.guild.get_channel(chan_id)
            # Remove the whole flag pattern from the query parameter
            query = re.sub(r'--channel\s+(?:<#)?[0-9]+>?', '', query).strip()

        # Handle --clean flag (implicitly True if cross-channel)
        has_clean_flag = '--clean' in query
        clean = has_clean_flag or target_channel is not None
        query = query.replace('--clean', '').strip()

        # Message ID lookup
        if query.isdigit():
            try:
                msg = await ctx.channel.fetch_message(int(query))
                return msg, clean, target_channel, has_channel_flag
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
                        return None, clean, target_channel, has_channel_flag
                    # Check if user has access to the guild
                    channel = guild.get_channel(channel_id)
                    if isinstance(channel, discord.TextChannel):
                        msg = await channel.fetch_message(message_id)
                        return msg, clean, target_channel, has_channel_flag
            except (ValueError, discord.NotFound, discord.Forbidden):
                pass

        # Message search by Content (in current channel message history for matching content)
        async for message in ctx.channel.history(limit=100):
            if query.lower() in message.content.lower():
                return message, clean, target_channel, has_channel_flag

        return None, clean, target_channel, has_channel_flag

    # ╔════════════════════╦═════════════════════╦═════════════════╗
    # ╠════════════════════╣QUOTE_MESSAGE COMMAND╠═════════════════╣
    # ╚════════════════════╩═════════════════════╩═════════════════╝

    @commands.command(name="quote", aliases=["q"], description="Quote messages using WebHooks")
    @commands.guild_only()
    async def quote_message(self, ctx: commands.Context, *, query: str):
        """Quote any message by ID, link, or content search
        ```css
        {prefix}quote 1234567890
        {prefix}quote Hello World
        {prefix}q https://discord/123/456/789
        {prefix}q 1234567890 --clean (OWNER only)
        {prefix}q 1234567890 --channel #general (OWNER only)```"""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        message, clean, target_channel, has_channel_flag = await self.resolve_message(ctx, query)
        if not message:
            return await ctx.send("❌ Message not found or inaccessible", delete_after=10)

        is_owner = await checks.has_permissions(PermissionLevel.OWNER).predicate(ctx)

        # Enforce owner restrictions on the --channel flag
        if has_channel_flag and not is_owner:
            return await ctx.send("⚠️ The `--channel` option is restricted to the bot OWNER.", delete_after=10)

        # Setup destination channel
        destination = target_channel if target_channel else ctx.channel

        # Verify clean flag permission ONLY if not explicitly routing to an external channel
        if clean and not target_channel:
            if not is_owner:
                clean = False
                await ctx.send("⚠️ Clean mode is owner-only", delete_after=5)

        webhook = await self.create_webhook(destination)

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

        # Send confirmation message if cross-channel quoting occurred
        if target_channel and target_channel != ctx.channel:
            author_name = ctx.message.author.display_name
            await ctx.send(
                f"✅ Success {author_name}! The quote has been delivered to {target_channel.mention}. "
                f"[**Jump to View Quote here**]({webhook_msg.jump_url})"
            )

        # Add original message’s reactions, if available
        if message.reactions:
            try:
                quoted_msg = await destination.fetch_message(webhook_msg.id)
                for reaction in message.reactions:
                    try:
                        await quoted_msg.add_reaction(reaction.emoji)
                    except:
                        continue
            except discord.Forbidden:
                pass

    # ╔════════════════════╦═══════════════╦═══════════════════════╗
    # ╠════════════════════╣ EMBED TO TEXT ╠═══════════════════════╣
    # ╚════════════════════╩═══════════════╩═══════════════════════╝

    @commands.command(name='deconstruct', aliases=['deembed', 'embedcode'])
    @commands.is_owner()
    @commands.guild_only()
    async def deconstruct_embed(self, ctx, message_link: str):
        """Converts a target message link's embed into copy-pasteable Python code."""
        # 1. Parse out the IDs from the Discord message link structure
        link_pattern = r"channels/(\d+)/(\d+)/(\d+)"
        match = re.search(link_pattern, message_link)
        
        if not match:
            return await ctx.send("❌ **Invalid Link Format!** Please provide a standard Discord message URL.")
        
        guild_id, channel_id, message_id = map(int, match.groups())
        
        # 2. Fetch the target payload across server channels
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            target_msg = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send("❌ **Message Not Found!** Ensure the message exists and the bot can read it.")
        except discord.Forbidden:
            return await ctx.send("❌ **Permission Denied!** I lack the access required to read that channel link.")
        except Exception as e:
            return await ctx.send(f"❌ **Fetch Failure:** `{str(e)}`")

        if not target_msg.embeds:
            return await ctx.send("❓ This target message link does not contain any functional layout embeds.")

        # 3. Process and reverse-engineer the embed metrics
        embed = target_msg.embeds[0]
        code_lines = []
        
        # Base instantiation mapping
        base_args = []
        if embed.title:
            base_args.append(f'title="{embed.title}"')
        if embed.colour:
            base_args.append(f'colour=discord.Colour(0x{embed.colour.value:06x})')
        if embed.url:
            base_args.append(f'url="{embed.url}"')
        if embed.description:
            # Escape inner double line breaks cleanly
            clean_desc = embed.description.replace('\n', '\\n')
            base_args.append(f'description="{clean_desc}"')
        if embed.timestamp:
            # Format cleanly using standard datetime builders
            code_lines.append(f"# Ensure you imported: from datetime import datetime")
            base_args.append(f'timestamp=datetime.fromisoformat("{embed.timestamp.isoformat()}")')
            
        code_lines.append(f"embed = discord.Embed({', '.join(base_args)})")
        code_lines.append("") # Spacing line
        
        # Structural component maps
        if embed.image and embed.image.url:
            code_lines.append(f'embed.set_image(url="{embed.image.url}")')
        if embed.thumbnail and embed.thumbnail.url:
            code_lines.append(f'embed.set_thumbnail(url="{embed.thumbnail.url}")')
            
        if embed.author:
            auth_args = []
            if embed.author.name: auth_args.append(f'name="{embed.author.name}"')
            if embed.author.url: auth_args.append(f'url="{embed.author.url}"')
            if embed.author.icon_url: auth_args.append(f'icon_url="{embed.author.icon_url}"')
            if auth_args:
                code_lines.append(f"embed.set_author({', '.join(auth_args)})")
                
        if embed.footer:
            foot_args = []
            if embed.footer.text: foot_args.append(f'text="{embed.footer.text}"')
            if embed.footer.icon_url: foot_args.append(f'icon_url="{embed.footer.icon_url}"')
            if foot_args:
                code_lines.append(f"embed.set_footer({', '.join(foot_args)})")
                
        if embed.fields:
            code_lines.append("") # Spacing block before field layers
            for field in embed.fields:
                clean_val = field.value.replace('\n', '\\n')
                inline_val = ", inline=True" if field.inline else ", inline=False"
                code_lines.append(f'embed.add_field(name="{field.name}", value="{clean_val}"{inline_val})')

        code_lines.append("") # Space before execution line
        
        # Final broadcast method matching discord.py 2.x formats
        if target_msg.content:
            clean_content = target_msg.content.replace('\n', '\\n')
            code_lines.append(f'await ctx.send(content="{clean_content}", embed=embed)')
        else:
            code_lines.append('await ctx.send(embed=embed)')

        # 4. Bundle output data securely into stream objects for transport
        final_code = '\n'.join(code_lines)
        
        if len(final_code) <= 1980:
            await ctx.send(f"```python\n{final_code}\n```")
        else:
            # Automatically turn it into a downloadable text file if it exceeds the message limit
            file_stream = io.BytesIO(final_code.encode('utf-8'))
            await ctx.send(
                content="⚠️ **Code string exceeded channel limit!** Here is your layout source code package:",
                file=discord.File(file_stream, filename="reconstructed_embed.py")
            )


async def setup(bot):
    await bot.add_cog(Quote(bot))
