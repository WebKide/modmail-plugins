from discord.ext import commands
from discord import Embed
from .models import Scoreboard

class ScoreboardAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scoreboard = Scoreboard(bot.plugin_db.get_partition(self))
        
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def clean_user(self, ctx, member: discord.Member):
        """Remove all stats for a user"""
        await self.scoreboard.db.delete_many({'player_id': member.id})
        await ctx.send(f"🧹 Cleared all stats for {member.display_name}")
        
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def adjust_score(self, ctx, member: discord.Member, game_type: str, wins: int = 0, losses: int = 0):
        """Adjust a player's win/loss stats"""
        stats_key = f"stats:{member.id}:{game_type.lower()}"
        
        await self.scoreboard.db.find_one_and_update(
            {'_id': stats_key},
            {'$inc': {
                'wins': wins,
                'losses': losses,
                'total_games': wins + losses
            }},
            upsert=True
        )
        
        await ctx.send(f"✅ Updated {member.display_name}'s {game_type} stats")
