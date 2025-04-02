import discord

from discord.ext import commands
from .commands import TextGameCommands
from .scoreboard import ScoreboardCommands
from .admin import ScoreboardAdmin

class TextGames(commands.Cog):
    """Text games with score tracking system"""
    def __init__(self, bot):
        self.bot = bot
        self.games = TextGameCommands(bot)
        self.scoreboard = ScoreboardCommands(bot)
        self.admin = ScoreboardAdmin(bot)

        # Register command groups
        self.scoreboard_command = commands.Group(
            self.scoreboard.scoreboard,
            name="scoreboard",
            invoke_without_command=True
        )
        self.bot.add_command(self.scoreboard_command)

    def cog_unload(self):
        # Clean up commands when cog is unloaded
        self.bot.remove_command("scoreboard")

async def setup(bot):
    await bot.add_cog(TextGames(bot))
    
