from discord.ext import commands
from .models import GameType, GameOutcome, Scoreboard

class TextGameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scoreboard = Scoreboard(bot.plugin_db.get_partition(self))
        
    async def record_outcome(self, ctx, game_type, outcome, score=0):
        """Helper to record game outcomes"""
        await self.scoreboard.record_game(
            ctx.author.id,
            game_type,
            outcome,
            score
        )
        
    # +------------------------------------------------------------+
    # |                                                            |
    # |         Rock, paper, scissors, lizard, Spock               |
    # |                                                            |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def settle(self, ctx, your_choice: str = None):
        """ Play: rock paper scissors lizard spock
        
        Usage:
        {prefix}settle rock
        
        Note: game variation inspired in TheBigBangTheory
        """
        await ctx.typing()
        author = ctx.message.author.display_name
        mod_bot = self.bot.user.display_name
        errored = f"{self.d}\n\n**Usage:**\n{ctx.prefix}{ctx.invoked_with} [rock, paper, scissors, lizard, or spock]"

        if your_choice is None:
            return await ctx.send(errored, delete_after=69)

        elif your_choice is not None:
            try:
                player_choice = your_choice.choice
                available = RPSLS.rock, RPSLS.paper, RPSLS.scissors, RPSLS.lizard, RPSLS.spock
                bot_choice = random.choice(available)
                cond = {
                    (RPSLS.rock, RPSLS.paper): False,
                    (RPSLS.rock, RPSLS.scissors): True,
                    (RPSLS.rock, RPSLS.lizard): True,
                    (RPSLS.rock, RPSLS.spock): False,
                    (RPSLS.paper, RPSLS.rock): True,
                    (RPSLS.paper, RPSLS.scissors): False,
                    (RPSLS.paper, RPSLS.lizard): False,
                    (RPSLS.paper, RPSLS.spock): True,
                    (RPSLS.scissors, RPSLS.rock): False,
                    (RPSLS.scissors, RPSLS.paper): True,
                    (RPSLS.scissors, RPSLS.lizard): True,
                    (RPSLS.scissors, RPSLS.spock): False,
                    (RPSLS.lizard, RPSLS.rock): False,
                    (RPSLS.lizard, RPSLS.paper): True,
                    (RPSLS.lizard, RPSLS.scissors): False,
                    (RPSLS.lizard, RPSLS.spock): True,
                    (RPSLS.spock, RPSLS.rock): True,
                    (RPSLS.spock, RPSLS.paper): False,
                    (RPSLS.spock, RPSLS.scissors): True,
                    (RPSLS.spock, RPSLS.lizard): False
                }
                e = discord.Embed()
                e.add_field(name=f'{mod_bot} chose:', value=f'{bot_choice.value}', inline=True)
                e.add_field(name=f'{author} chose:', value=f'{player_choice.value}', inline=True)

                if bot_choice == player_choice:
                    outcome = None

                else:
                    outcome = cond[(player_choice, bot_choice)]

                if outcome is True:
                    e.color = (discord.Colour(0xed791d))
                    e.set_footer(text="\N{SMALL ORANGE DIAMOND} You win!")
                    await ctx.channel.send(embed=e)

                elif outcome is False:
                    e.color = (discord.Colour(0xe000ff))
                    e.set_footer(text="\N{NO ENTRY SIGN} You lose...")
                    await ctx.channel.send(embed=e)

                else:
                    e.color = (discord.Colour(0x7289da))
                    e.set_footer(text="\N{JAPANESE SYMBOL FOR BEGINNER} We're square")
                    await ctx.channel.send(embed=e)

            except AttributeError:
                return await ctx.send(errored, delete_after=69)
        
        if outcome is True:
            await self.record_outcome(ctx, GameType.RPSLS, GameOutcome.WIN)
        elif outcome is False:
            await self.record_outcome(ctx, GameType.RPSLS, GameOutcome.LOSS)
        else:
            await self.record_outcome(ctx, GameType.RPSLS, GameOutcome.DRAW)
            
    # +------------------------------------------------------------+
    # |                                                            |
    # |                        GUESS                               |
    # |                                                            |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def guess(self, ctx, number: int = None):
        """ Write number between 1 and 11
        
        Usage:
        {prefix}guess 7
        """
        answer = random.randint(1, 11)
        guessed_wrong = [
            'Not even close, the right number was:',
            'Better luck next time, the number was:',
            'How could you have known that the number was:',
            'Hmm, well, the right number was:',
            'Not getting any better, the number was:',
            'Right number was:'
        ]
        wrong = f'```{random.choice(guessed_wrong)} {answer}```'
        guessed_right = [
            'You guessed correctly!',
            'Everyone knew you could do it!',
            'You got the right answer!',
            'History will remember you...'
        ]
        right = f'```{random.choice(guessed_right)}```'
        u = ctx.message.author.display_name
        e = discord.Embed(color=self.user_color)

        if number is None:
            return await ctx.send('please write any number between 1 and 11', delete_after=23)

        if number is not None:
            if number < answer or number > answer:
                q_mark = '\N{OCTAGONAL SIGN}'
                e.add_field(name=f'{q_mark} {u} chose: `{number}`',
                            value=wrong, inline=True)
                try:
                    await ctx.send(embed=e)
                except discord.HTTPException:
                    await ctx.send(wrong)

            if number == answer:
                q_mark = '\N{SPORTS MEDAL}'
                e.add_field(name=f'{q_mark} {u} chose: `{answer}`',
                            value=right, inline=True)
                try:
                    await ctx.send(embed=e)
                except discord.HTTPException:
                    await ctx.send(right)

            else:
                pass
        
        if number == answer:
            await self.record_outcome(ctx, GameType.GUESS, GameOutcome.WIN, score=10)
        else:
            await self.record_outcome(ctx, GameType.GUESS, GameOutcome.LOSS)
            
    # ... other game commands ...

async def setup(bot):
    await bot.add_cog(TextGames(bot))
