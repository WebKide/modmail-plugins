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

    def cog_unload(self):
        # Cleanup if needed
        pass

async def setup(bot):
    # Initialize all components
    cog = TextGames(bot)
    await bot.add_cog(cog)
    
    # Manually add command groups
    bot.add_command(cog.games.settle)
    bot.add_command(cog.games.guess)
    bot.add_command(cog.scoreboard.scoreboard)
    bot.add_command(cog.admin.clean_user)
    # Add all other commands...
    
