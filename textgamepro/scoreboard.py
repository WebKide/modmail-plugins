import discord

from discord.ext import commands
from discord import Embed
from .models import GameType, Scoreboard


class ScoreboardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scoreboard = Scoreboard(bot.plugin_db.get_partition(self))
        
    @commands.group(invoke_without_command=True)
    async def scoreboard(self, ctx, game_type: str = None):
        """View scoreboards and player stats"""
        if not game_type:
            embed = Embed(
                title="Available Scoreboards",
                description="Use `!scoreboard <game>` to view specific leaderboards\n"
                            "Available games: rpsls, guess, scramble, coinflip"
            )
            return await ctx.send(embed=embed)
            
        try:
            game = GameType(game_type.lower())
            leaderboard = await self.scoreboard.get_leaderboard(game)
            
            embed = Embed(title=f"🏆 {game.value} Leaderboard")
            for i, entry in enumerate(leaderboard, 1):
                user = self.bot.get_user(entry['player_id'])
                username = user.display_name if user else f"Unknown User ({entry['player_id']})"
                
                embed.add_field(
                    name=f"{i}. {username}",
                    value=f"Wins: {entry['wins']} | Streak: {entry['current_streak']}",
                    inline=False
                )
                
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("Invalid game type. Available: rpsls, guess, scramble, coinflip")
            
    @scoreboard.command()
    async def stats(self, ctx, member: discord.Member = None):
        """View your game statistics"""
        player = member or ctx.author
        stats = await self.scoreboard.get_player_stats(player.id)
        
        embed = Embed(title=f"📊 {player.display_name}'s Game Stats")
        for stat in stats:
            embed.add_field(
                name=stat['game_type'],
                value=f"W: {stat['wins']} / L: {stat['losses']} / D: {stat['draws']}\n"
                      f"Streak: {stat['current_streak']} | High: {stat['highest_score']}",
                inline=True
            )
            
        await ctx.send(embed=embed)
