import discord
import logging
from discord.ext import commands
from core import checks
from core.models import PermissionLevel

logger = logging.getLogger("Modmail")


class DmOnJoin(commands.Cog):
    """Automatically DM users when they join the server."""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.command(aliases=["sdms"], description='Change options', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def setdmmessage(self, ctx, *, message):
        """Set a message to DM users when they join.
        
        You can use {user} to mention the user and {guild} for server name.
        Alternatively, provide a hastebin URL with the message content.
        """
        if message.startswith(("https://", "http://")):
            if "hasteb.in" in message:
                if not message.startswith("https://hasteb.in/raw/"):
                    message = "https://hasteb.in/raw/" + message.split("/")[-1]

            try:
                async with self.bot.session.get(message) as resp:
                    if resp.status == 200:
                        message = await resp.text()
                    else:
                        await ctx.send("Failed to fetch message from URL.")
                        return
            except Exception as e:
                await ctx.send(f"Error fetching URL: {e}")
                return

        await self.db.find_one_and_update(
            {"_id": "dm-config"},
            {"$set": {"dm-message": {"message": message, "enabled": True}}},
            upsert=True,
        )

        await ctx.send("Successfully set the DM message.")

    @commands.command(description='Change options', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def toggledm(self, ctx):
        """Toggle whether join DMs are enabled."""
        config = await self.db.find_one({"_id": "dm-config"}) or {}
        current = config.get("dm-message", {}).get("enabled", True)
        
        await self.db.find_one_and_update(
            {"_id": "dm-config"},
            {"$set": {"dm-message.enabled": not current}},
            upsert=True,
        )
        
        status = "enabled" if not current else "disabled"
        await ctx.send(f"Join DMs are now {status}.")

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
            formatted = message.replace("{user}", str(member)).replace("{guild}", member.guild.name)
            await member.send(formatted)
        except discord.Forbidden:
            logger.info(f"Could not DM {member} (DMs disabled).")
        except discord.HTTPException as e:
            logger.error(f"Failed to send DM to {member}: \n{e}")


async def setup(bot):
    await bot.add_cog(DmOnJoin(bot))
    
