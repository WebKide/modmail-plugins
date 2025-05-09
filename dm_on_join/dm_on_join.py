import discord
import logging
import re
import asyncio
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
    async def setdmmessage(self, ctx):
        """Set a message to DM users when they join"""
        instructions = (
            "Please send your DM message with supported formatting:\n"
            "# H1\n## H2\n### H3\n"
            "**bold**, *italic*, ~~strikethrough~~, ```css\nCode block```, "
            "`monospace`, emojis, and these placeholders:\n"
            "{guild_name}, {user.display_name}, {user.id}, {guild.owner}\n"
            "You have 2 minutes to submit your message."
        )
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
        allowed = {'guild_name', 'user.display_name', 'user.id', 'guild.owner'}
        invalid = [ph for ph in placeholders if ph not in allowed]

        if invalid:
            await ctx.send(f"❌ Invalid placeholders: {', '.join(invalid)}\n"
                           f"Allowed: {', '.join(allowed)}")
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
            formatted = re.sub(r'\{\s*guild_name\s*\}', ctx.guild.name, message)
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
            formatted = re.sub(r'\{\s*guild_name\s*\}', member.guild.name, message)
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
