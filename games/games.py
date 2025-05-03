# External imports
import random
import re
import time
import asyncio
from datetime import datetime, date
import discord
from discord.ext import commands
from discord import ui

# Local imports
from .config import GameConfig, Emoji
from .embedmanager import EmbedManager
from .rpsls import RPSLSGame

# Answer file imports
from .answers.cookie import fortune_cookies
from .answers.eightball import ball_answers
from .answers.futhark import runes_list
from .answers.hangman import hangman_words
from .answers.iching import oracle_answer
from .answers.tarot import card_deck
from .answers.words import scramble_words


class Games(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Text based games and oracle commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_manager = EmbedManager(bot)
        self.tracker = GamesTracker(bot)
        
        # Initialize answer lists
        self.fortune_cookies = fortune_cookies
        self.ball_answers = ball_answers
        self.runes_list = runes_list
        self.hangman_words = hangman_words
        self.oracle_answer = oracle_answer
        self.card_deck = card_deck
        self.scramble_words = scramble_words
        
        # Game state trackers
        self.hangman_games = {}  # {channel_id: game_state}
        self.scramble_games = {}  # {user_id: game_state}
        self.sessions = set()

    # ╔════════════════════════════════════════════════════════════╗
    # ║                          8-BALL                            ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['8ball'])
    async def eightball(self, ctx, *, question=None):
        """Ask the magic 8-ball a question"""
        start_time = time.time()
        
        if not question:
            embed = await self.embed_manager.create_command_embed(
                ctx,
                description=f'What is your question {ctx.author.mention}?',
                footer_text=f"{date.today()}",
                start_time=start_time
            )
            return await ctx.send(embed=embed, delete_after=GameConfig.SHORT_DELETE_AFTER)

        if not question.endswith("?") or question == "?":
            return await ctx.send(f"*{question}* doesn't look like a yes/no question.", 
                                delete_after=GameConfig.SHORT_DELETE_AFTER)

        response = random.choice(self.ball_answers)
        
        embed = await self.embed_manager.create_command_embed(
            ctx,
            author={'name': f"{ctx.author.display_name}'s question"},
            description=f'```{question}```',
            thumbnail=GameConfig.EIGHTBALL_IMAGE,
            fields=[{
                'name': f'{Emoji.EIGHTBALL} answer:', 
                'value': f'**```css\n{response}```**'
            }],
            start_time=start_time
        )

        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                          SETTLE                            ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['rpsls', 'rps'])
    async def settle(self, ctx, your_choice: str = None):
        """Play Rock-Paper-Scissors-Lizard-Spock"""
        start_time = time.time()
        
        if your_choice is None:
            embed = RPSLSGame.get_help_embed(self.embed_manager, ctx)
            return await ctx.send(embed=embed, delete_after=GameConfig.LONG_DELETE_AFTER)

        try:
            player_choice = RPSLSGame.parse_choice(your_choice)
            bot_choice = RPSLSGame.get_random_choice()
            outcome = RPSLSGame.determine_outcome(player_choice, bot_choice)
            
            embed = await RPSLSGame.create_game_embed(
                self.embed_manager,
                ctx,
                player_choice,
                bot_choice,
                outcome,
                start_time
            )
            await ctx.send(embed=embed)
            
        except ValueError:
            embed = RPSLSGame.get_help_embed(self.embed_manager, ctx)
            await ctx.send(embed=embed, delete_after=GameConfig.LONG_DELETE_AFTER)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                           GUESS                            ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command()
    async def guess(self, ctx, number: int = None):
        """Guess a number between 1-11"""
        start_time = time.time()
        min_num, max_num = GameConfig.GUESS_RANGE
        answer = random.randint(min_num, max_num)

        if number is None:
            embed = await self.embed_manager.create_command_embed(
                ctx,
                description=f'Please guess a number between {min_num} and {max_num}',
                footer_text=f"{date.today()}",
                start_time=start_time
            )
            return await ctx.send(embed=embed, delete_after=GameConfig.DEFAULT_DELETE_AFTER)

        if number == answer:
            result_int = 1
            result_str = random.choice([
                'You guessed correctly!',
                'Everyone knew you could do it!',
                'You got the right answer!'
            ])
            color = self.embed_manager.colors['success']
            icon = Emoji.MEDAL
        else:
            result_int = 0
            result_str = f'{random.choice([
                "Not even close",
                "Better luck next time",
                "How could you have known",
                "Right number was"
            ])}: {answer}'
            color = self.embed_manager.colors['error']
            icon = Emoji.NO_ENTRY

        embed = await self.embed_manager.create_command_embed(
            ctx,
            color=color,
            fields=[{
                'name': f'{icon} {ctx.author.display_name} chose: `{number}`',
                'value': f'```{result_str}```'
            }],
            start_time=start_time
        )
        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                           FLIP                             ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['toss', 'tossacoin'])
    async def flip(self, ctx, *, text: str = None):
        """Flip a coin or some text"""
        start_time = time.time()
        
        if text:
            # Text flipping logic
            flipped = text.translate(str.maketrans(
                'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'ɐqɔpǝɟƃɥᴉɾʞʅɯuodbɹsʇnʌʍxʎz∀ꓭƆᗡƎℲ⅁HIſꓘ⅂WNOԀQᴚSꓕՈΛMX⅄Z'
            ))[::-1]

            embed = await self.embed_manager.create_command_embed(
                ctx,
                fields=[{
                    'name': f'{ctx.author.display_name}',
                    'value': f'(╯°□°）╯︵ **{flipped[:2000]}**'
                }],
                start_time=start_time
            )
            await ctx.send(embed=embed)
            return

        # Coin flip logic
        msg = await ctx.send('Tossing the coin...')
        await asyncio.sleep(1)
        
        result = random.choices(
            ['heads', 'tails', 'edge'],
            weights=[45, 45, 10],
            k=1
        )[0]

        embed_data = {
            'heads': {
                'color': GameConfig.EMBED_COLORS['coin_heads'],
                'thumbnail': GameConfig.COIN_IMAGES['heads'],
                'text': 'Heads'
            },
            'tails': {
                'color': GameConfig.EMBED_COLORS['coin_tails'],
                'thumbnail': GameConfig.COIN_IMAGES['tails'],
                'text': 'Tails'
            },
            'edge': {
                'color': GameConfig.EMBED_COLORS['coin_edge'],
                'thumbnail': GameConfig.COIN_IMAGES['edge'],
                'text': 'Edge!'
            }
        }

        flips = random.randint(GameConfig.COIN_FLIP_MIN, GameConfig.COIN_FLIP_MAX)
        embed = await self.embed_manager.create_command_embed(
            ctx,
            color=discord.Colour(embed_data[result]['color']),
            description=f'After {flips} flips, the coin landed on:',
            thumbnail=embed_data[result]['thumbnail'],
            fields=[{
                'name': 'Result',
                'value': f'**{embed_data[result]["text"]}**'
            }],
            footer_text=GameConfig.COIN_DESCRIPTION,
            start_time=start_time
        )
        await msg.edit(content=None, embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                          CHOOSE                            ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command()
    async def choose(self, ctx, *, options: str = None):
        """Choose between multiple options"""
        start_time = time.time()
        
        if not options:
            embed = await self.embed_manager.create_command_embed(
                ctx,
                description=(
                    'Provide options separated by commas:\n'
                    f'`{ctx.prefix}choose eat, sleep, read`'
                ),
                footer_text=f"{date.today()}",
                start_time=start_time
            )
            return await ctx.send(embed=embed, delete_after=GameConfig.DEFAULT_DELETE_AFTER)

        choices = [opt.strip() for opt in options.replace(' or ', ',').split(',') if opt.strip()]
        
        if len(choices) < 2:
            embed = await self.embed_manager.create_command_embed(
                ctx,
                description='Please provide at least 2 options',
                footer_text=f"{date.today()}",
                start_time=start_time
            )
            return await ctx.send(embed=embed, delete_after=GameConfig.DEFAULT_DELETE_AFTER)

        picked = random.choice(choices)
        embed = await self.embed_manager.create_command_embed(
            ctx,
            fields=[{
                'name': 'Options',
                'value': '\n'.join(f'• {c}' for c in choices)
            }, {
                'name': f'{Emoji.DIAMOND} Selection',
                'value': f'I choose: **{picked}**'
            }],
            start_time=start_time
        )
        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                           TAROT                            ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.group(invoke_without_command=True)
    async def tarot(self, ctx):
        """Start a tarot reading session"""
        await self.embed_manager.show_processing(
            ctx,
            messages=GameConfig.TAROT_MESSAGES,
            delays=GameConfig.TAROT_DELAYS
        )

    @tarot.command()
    async def reading(self, ctx, *, question: str = None):
        """Perform a 3-card tarot reading"""
        start_time = time.time()
        
        cards = [random.choice(self.card_deck) for _ in range(3)]
        positions = [
            "1️⃣ **The Past:** Why you're in this situation",
            "2️⃣ **The Present:** Current challenges",
            "3️⃣ **The Future:** Potential outcomes"
        ]
        
        embed = await self.embed_manager.create_oracle_embed(
            ctx,
            title=f'Tarot Reading for {ctx.author.display_name}',
            description='\n\n'.join(f'{p}\n{c}' for p, c in zip(positions, cards)),
            image_url=GameConfig.TAROT_DECK_IMAGE,
            start_time=start_time
        )
        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                          i-CHING                           ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['i-ching', 'oracle'])
    async def iching(self, ctx, *, question: str = None):
        """Consult the I Ching oracle"""
        start_time = time.time()
        
        if not question or not question.endswith('?'):
            return await ctx.send("Please ask a complete question ending with '?'", 
                               delete_after=GameConfig.SHORT_DELETE_AFTER)

        response = random.choice(self.oracle_answer)
        embed = await self.embed_manager.create_oracle_embed(
            ctx,
            title='I Ching Oracle',
            description=response,
            image_url=GameConfig.ICHING_IMAGE,
            color_name='iching',
            start_time=start_time
        )
        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                        FUTHARK RUNE                        ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['futhark'])
    async def rune(self, ctx, *, query: str = None):
        """Draw a Viking rune"""
        start_time = time.time()
        rune = random.choice(self.runes_list)
        
        embed = await self.embed_manager.create_oracle_embed(
            ctx,
            title=f'{rune["rune_name"]} ({rune["rune_title"]})',
            description=rune["meaning"],
            image_url=rune["image"],
            color_name='mod',
            start_time=start_time
        )
        
        if query:
            embed.insert_field_at(0, {
                'name': 'Question',
                'value': query,
                'inline': False
            })
            
        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                         ROLL DICE                          ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['dice', 'rolldice'])
    @commands.guild_only()
    async def roll(self, ctx, dice: str = "1d6"):
        """Roll dice in NdN format (e.g. 2d20) (Max: 9d99)"""
        start_time = time.time()
        
        try:
            if not re.match(r'^\d+d\d+$', dice):
                raise ValueError("Invalid format")
            
            num_dice, num_faces = map(int, dice.split('d'))
            num_dice = min(max(num_dice, 1), 9)
            num_faces = min(max(num_faces, 2), 99)
            
            rolls = [random.randint(1, num_faces) for _ in range(num_dice)]
            total = sum(rolls)
            
            embed = await self.embed_manager.create_command_embed(
                ctx,
                fields=[{
                    'name': f'🎲 {num_dice}d{num_faces} Results',
                    'value': f'```{" + ".join(map(str, rolls))} = {total}```'
                }],
                thumbnail='https://i.imgur.com/N4d4X3h.png',
                start_time=start_time
            )
            await ctx.send(embed=embed)
            await self.tracker.log_command(
                ctx,
                'dice_roll',
                question=dice,
                result_int=total
            )
            
        except ValueError:
            embed = await self.embed_manager.create_command_embed(
                ctx,
                color=self.embed_manager.colors['error'],
                description='Use `NdN` format (e.g. 2d20)\nMax: 9 dice, 99 faces',
                start_time=start_time
            )
            await ctx.send(embed=embed, delete_after=GameConfig.SHORT_DELETE_AFTER)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                       FORTUNE COOKIE                       ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['fortune'])
    @commands.guild_only()
    async def cookie(self, ctx):
        """Get a random fortune cookie message"""
        start_time = time.time()
        
        fortune = random.choice(self.fortune_cookies)
        embed = await self.embed_manager.create_command_embed(
            ctx,
            title='🥠 Fortune Cookie Says',
            description=f'```{fortune}```',
            thumbnail='https://i.imgur.com/MHkzgHU.png',
            start_time=start_time
        )
        await ctx.send(embed=embed)
        await self.tracker.log_command(
            ctx,
            'fortune_cookie',
            result_str=fortune
        )

    # ╔════════════════════════════════════════════════════════════╗
    # ║                          HANGMAN                           ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command()
    @commands.guild_only()
    async def hangman(self, ctx):
        """Start a game of hangman"""
        start_time = time.time()
        
        word = random.choice(self.hangman_words).upper()
        self.hangman_games[ctx.channel.id] = {
            'word': word,
            'display': ['_' if c.isalpha() else c for c in word],
            'wrong': 0,
            'guessed': set()
        }
        
        embed = await self.embed_manager.create_command_embed(
            ctx,
            title='🎮 Hangman Game Started',
            description=(
                f"Word: {' '.join(self.hangman_games[ctx.channel.id]['display'])}\n"
                f"Wrong guesses left: 6\n"
                "Click a letter to guess!"
            ),
            thumbnail='https://i.imgur.com/EksOlTe.png',
            start_time=start_time
        )
        
        view = HangmanView(timeout=300.0)  # 5 minute timeout
        view.message = await ctx.send(embed=embed, view=view)
        
        await self.tracker.log_command(
            ctx,
            'hangman_start',
            question=word
        )

    # ╔════════════════════════════════════════════════════════════╗
    # ║                         UNSCRAMBLE                         ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['scramble'])
    @commands.guild_only()
    async def unscramble(self, ctx):
        """Unscramble a word challenge"""
        start_time = time.time()
        
        word = random.choice(self.scramble_words).upper()
        scrambled = ''.join(random.sample(word, len(word)))
        self.scramble_games[ctx.author.id] = {
            'answer': word,
            'scrambled': scrambled,
            'start_time': time.time()
        }
        
        embed = await self.embed_manager.create_command_embed(
            ctx,
            title='🔤 Word Scramble',
            description=(
                f"Unscramble this word:\n"
                f"```{scrambled}```\n"
                f"Type your answer in chat!"
            ),
            thumbnail="https://i.imgur.com/wydPdrN.png",
            footer_text=f"Hint: {len(word)} letters | Related to tech",
            start_time=start_time
        )
        
        await ctx.send(embed=embed)
        await self.tracker.log_command(
            ctx,
            'scramble_start',
            question=word
        )

# ╔═════════════════════╦═══════════════╦══════════════════════╗
# ╠═════════════════════╣ DISCORD VIEWS ╠══════════════════════╣
# ╚═════════════════════╩═══════════════╩══════════════════════╝
class HangmanView(discord.ui.View):
    def __init__(self, timeout=60.0):
        super().__init__(timeout=timeout)
        self.create_letter_buttons()
        
    def create_letter_buttons(self):
        """Dynamically generate buttons for A-Z"""
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            button = discord.ui.Button(
                label=letter,
                style=discord.ButtonStyle.secondary,
                custom_id=f"hangman_{letter}"
            )
            button.callback = self.create_callback(letter)
            self.add_item(button)

    def create_callback(self, letter):
        """Generate callback function for each button"""
        async def button_callback(interaction):
            await self.process_guess(interaction, letter)
            # Disable the used button
            for child in self.children:
                if child.custom_id == f"hangman_{letter}":
                    child.disabled = True
            await interaction.response.edit_message(view=self)
        return button_callback

    async def process_guess(self, interaction, letter):
        """Handle guess logic"""
        games_cog = interaction.client.get_cog('Games')
        game = games_cog.hangman_games.get(interaction.channel.id)
        
        if not game or letter in game['guessed']:
            return

        game['guessed'].add(letter)
        word = game['word']
        display = game['display']
        
        # Update display with correct guesses
        correct_guess = False
        for i, char in enumerate(word):
            if char == letter:
                display[i] = letter
                correct_guess = True

        if not correct_guess:
            game['wrong'] += 1

        # Update embed
        embed = interaction.message.embeds[0]
        embed.description = (
            f"Word: `{' '.join(display)}`\n"
            f"Wrong guesses left: {6 - game['wrong']}\n"
            f"Used letters: {', '.join(sorted(game['guessed']))}"
        )

        # Check win/lose conditions
        if '_' not in display:
            embed.color = games_cog.embed_manager.colors['success']
            await games_cog.tracker.log_command(
                interaction,
                'hangman_win',
                result_str=word,
                result_int=6 - game['wrong']
            )
            await interaction.response.edit_message(embed=embed, view=None)
            del games_cog.hangman_games[interaction.channel.id]
            return
        elif game['wrong'] >= 6:
            embed.color = games_cog.embed_manager.colors['error']
            embed.description += f"\n\nGame Over! The word was: **{word}**"
            await games_cog.tracker.log_command(
                interaction,
                'hangman_lose',
                result_str=word
            )
            await interaction.response.edit_message(embed=embed, view=None)
            del games_cog.hangman_games[interaction.channel.id]
            return

        await interaction.response.edit_message(embed=embed)

    async def on_timeout(self):
        """Clean up when view times out"""
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                        GAMES STATS                         ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def gamesstats(self, ctx, user: discord.Member = None):
        """View your game statistics or another user's"""
        start_time = time.time()
        user = user or ctx.author
        stats = await self.tracker.get_user_stats(user.id)
        
        if not stats:
            embed = await self.embed_manager.create_command_embed(
                ctx,
                description=f"No stats found for {user.display_name}",
                start_time=start_time
            )
            return await ctx.send(embed=embed)
            
        embed = await self.embed_manager.create_command_embed(
            ctx,
            title=f"{user.display_name}'s Game Stats",
            description=f"Total commands used: {sum(s['count'] for s in stats.values())}",
            start_time=start_time
        )
        
        for command, data in stats.items():
            embed.add_field(
                name=command.capitalize(),
                value=(
                    f"Used: {data['count']} times\n"
                    f"Last: {data['last_used'].strftime('%Y-%m-%d')}"
                ),
                inline=True
            )
            
        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                          OUTCOMES                          ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @gamesstats.command()
    @commands.guild_only()
    async def outcomes(self, ctx, command_name: str = None):
        """View win/lose/draw statistics for game commands"""
        start_time = time.time()
        stats = await self.tracker.get_outcome_stats(command_name)
        
        if not stats:
            embed = await self.embed_manager.create_command_embed(
                ctx,
                description="No outcome statistics available",
                start_time=start_time
            )
            return await ctx.send(embed=embed)
            
        embed = await self.embed_manager.create_command_embed(
            ctx,
            title="Game Outcome Statistics",
            start_time=start_time
        )
        
        for game, data in stats.items():
            embed.add_field(
                name=game.capitalize(),
                value=(
                    f"Wins: {data['wins']} ({data['win_rate']}%)\n"
                    f"Losses: {data['losses']}\n"
                    f"Draws: {data['draws']}"
                ),
                inline=True
            )
            
        await ctx.send(embed=embed)

    # ╔════════════════════════════════════════════════════════════╗
    # ║                        LEADERBOARD                         ║
    # ╠════════════════════╦══════════════════╦════════════════════╣
    # ╠════════════════════╣ DISCORD COMMANDS ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command()
    @commands.guild_only()
    async def gamesleaderboard(self, ctx, limit: int = 10):
        """View top game command users (default: top 10)"""
        start_time = time.time()
        limit = min(max(limit, 1), 25)  # Clamp between 1-25
        leaderboard = await self.tracker.get_leaderboard(limit)
        
        if not leaderboard:
            embed = await self.embed_manager.create_command_embed(
                ctx,
                description="No leaderboard data available yet",
                start_time=start_time
            )
            return await ctx.send(embed=embed)
            
        embed = await self.embed_manager.create_command_embed(
            ctx,
            title=f"Top {len(leaderboard)} Game Players",
            start_time=start_time
        )
        
        for i, entry in enumerate(leaderboard, 1):
            embed.add_field(
                name=f"{i}. {entry['user']}",
                value=(
                    f"Commands: {entry['total']}\n"
                    f"Different games: {entry['commands']}"
                ),
                inline=False
            )
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Games(bot))
