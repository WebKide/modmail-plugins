import os
import logging
import discord
from discord.ext import commands
from core import checks
from core.models import PermissionLevel
from .core.servers import KeepAliveServer

logger = logging.getLogger("Modmail")

class KeepAlive(commands.Cog):
    """Keeps bot from sleeping on Koyeb's free tier"""
    
    def __init__(self, bot):
        self.bot = bot
        self.server = KeepAliveServer()

    async def cog_load(self):
        self.server.start()

    @commands.group(name="keepalive", invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.OWNER)
    async def keepalive_group(self, ctx):
        """Keep the bot awake on Koyeb"""
        await ctx.send_help(ctx.command)

    @keepalive_group.command(name="start")
    async def start_server(self, ctx):
        """Start the keepalive server"""
        if self.server.is_running():
            await ctx.send("🟢 Server already running!")
        else:
            self.server.start()
            await ctx.send(f"✅ Server started at: {self.server.url}")

    @keepalive_group.command(name="test")
    async def test_server(self, ctx):
        """Test if the server is accessible"""
        if not self.server.is_running():
            return await ctx.send("🔴 Server not running! Use `!keepalive start`")
            
        await ctx.send(f"🔍 Testing {self.server.url}...")
        try:
            async with self.bot.session.get(self.server.url) as resp:
                if resp.status == 200:
                    await ctx.send("🟢 Server is responding!")
                else:
                    await ctx.send(f"🟠 Unexpected status: {resp.status}")
        except Exception as e:
            await ctx.send(f"🔴 Connection failed: {str(e)}")

    @keepalive_group.command(name="info")
    async def server_info(self, ctx):
        """Show keepalive status"""
        embed = discord.Embed(title="🚦 KeepAlive Status", color=0x00ff00)
        embed.set_footer(text="Persistent HTTP server powered by Flask", icon_url="https://i.imgur.com/Rxhy1W5.png")
        embed.add_field(
            name="Server", 
            value=f"Status: {'🟢 Running' if self.server.is_running() else '🔴 Stopped'}\n"
                  f"URL: {self.server.url or 'Not set'}"
        )
        embed.add_field(
            name="Koyeb Setup",
            value="Required ENV vars:\n"
                  "`PORT=8000`\n"
                  "`KOYEB_APP_URL=https://your-app.koyeb.app`",
            inline=False
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(KeepAlive(bot))
