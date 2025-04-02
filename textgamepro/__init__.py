from discord.ext import commands
from .commands import TextGameCommands
from .scoreboard import ScoreboardCommands
from .admin import ScoreboardAdmin

async def setup(bot):
    await bot.add_cog(TextGameCommands(bot))
    await bot.add_cog(ScoreboardCommands(bot))
    await bot.add_cog(ScoreboardAdmin(bot))
