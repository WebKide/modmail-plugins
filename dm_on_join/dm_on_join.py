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

import logging
import re
import asyncio
import textwrap

import discord
from discord.ext import commands
from core import checks
from core.models import PermissionLevel

logger = logging.getLogger("Modmail")


class DmOnJoin(commands.Cog):
    """Automatically DM users when they join the server."""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.command(aliases=["sdms"], description='Set DM message')
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def setdmmessage(self, ctx, *, welcome_message: str = None):
        """Set a message to DM users when they join"""
        instructions = textwrap.dedent("""
        # Formatting Guide #

        🔸 Headers:
        # \# H1
        ## \## H2
        ### \### H3
        -# \-# subtitle

        🔸 Text Formatting:
        \``monospace`\` — **\**bold**\** — *\*italic*\* — ~~strikethrough~~

        🔸 Code Blocks:
        ```css
        ```py
        ?plugin add WebKide/modmail-plugins/quote@master```

        🔸 Other:
        Emojis :white_check_mark: :raised_hand:

        🔸 Available Placeholders:
        `{guild.name}` - Server name
        `{user.display_name}` - User's display name
        `{user.id}` - User ID
        `{guild.owner}` - Server owner's name

        You have 2 minutes to submit your message.
        """).strip()
        await ctx.send(instructions)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=120)
        except asyncio.TimeoutError:
            await ctx.send("❌ Timed out. Please try again.")
            return

        # Validate placeholders
        raw_placeholders = re.findall(r'\{([^}]+)\}', msg.content)
        placeholders = [ph.strip() for ph in raw_placeholders]
        allowed = {'guild.name', 'user.display_name', 'user.id', 'guild.owner'}
        invalid = [ph for ph in placeholders if ph not in allowed]

        if invalid:
            await ctx.send(f"❌ **Invalid placeholders:** {', '.join(invalid)}\n"
                           f"✅ **Allowed:** {', '.join(allowed)}")
            return

        # Save valid message
        await self.db.find_one_and_update(
            {"_id": "dm-config"},
            {"$set": {"dm-message": {"message": msg.content, "enabled": True}}},
            upsert=True,
        )
        await ctx.send("✅ DM message updated successfully!")

    @commands.command(description='Toggle DMs')
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def toggledm(self, ctx):
        """Toggle join DMs on/off"""
        config = await self.db.find_one({"_id": "dm-config"}) or {}
        current = config.get("dm-message", {}).get("enabled", True)
        new_status = not current
        
        await self.db.find_one_and_update(
            {"_id": "dm-config"},
            {"$set": {"dm-message.enabled": new_status}},
            upsert=True,
        )
        
        await ctx.send(f"🔰 Join DMs are now {'enabled' if new_status else 'disabled'}.")

    @commands.command(description="Test the DM message")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def testdm(self, ctx):
        """Test the current DM message configuration"""
        config = await self.db.find_one({"_id": "dm-config"})
        if not config or not config.get("dm-message", {}).get("message"):
            await ctx.send("❌ No DM message configured yet!")
            return

        try:
            message = config["dm-message"]["message"]
            # Format with current context
            formatted = re.sub(r'\{\s*guild\.name\s*\}', ctx.guild.name, message)
            formatted = re.sub(r'\{\s*user\.display_name\s*\}', ctx.author.display_name, formatted)
            formatted = re.sub(r'\{\s*user\.id\s*\}', str(ctx.author.id), formatted)
            formatted = re.sub(r'\{\s*guild\.owner\s*\}', ctx.guild.owner.mention, formatted)
            
            await ctx.author.send(formatted)
            await ctx.send("✅ Check your DMs! You should have received the test message.")
        except discord.Forbidden:
            await ctx.send("❌ I can't send you DMs. Please enable DMs and try again.")
        except Exception as e:
            await ctx.send(f"❌ Failed to send test DM: {str(e)}")
            logger.error(f"Test DM error: {str(e)}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        config = await self.db.find_one({"_id": "dm-config"})
        if not config or not config.get("dm-message", {}).get("enabled", True):
            return

        message = config["dm-message"].get("message")
        if not message:
            return

        try:
            # Format message with dynamic replacements
            formatted = re.sub(r'\{\s*guild\.name\s*\}', member.guild.name, message)
            formatted = re.sub(r'\{\s*user\.display_name\s*\}', member.display_name, formatted)
            formatted = re.sub(r'\{\s*user\.id\s*\}', str(member.id), formatted)
            formatted = re.sub(r'\{\s*guild\.owner\s*\}', member.guild.owner.mention, formatted)
            
            await member.send(formatted)
        except discord.Forbidden:
            logger.info(f"Couldn't DM {member} (DMs closed)")
        except Exception as e:
            logger.error(f"Failed to send join DM: {str(e)}")


async def setup(bot):
    await bot.add_cog(DmOnJoin(bot))
