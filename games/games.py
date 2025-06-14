# External imports
import random
import re
import time
import asyncio
from datetime import datetime, date
import discord
import logging
from discord.ext import commands
from discord import ui

# Local imports
from .config import GameConfig, Emoji
# from .tracker import GamesTracker
from .embedmanager import EmbedManager
from .rpsls import RPSLSGame

# Answer file imports
from .answers.cookie import FORTUNE as fortune_cookies
from .answers.eightball import ball_answers
from .answers.futhark import runes_list
from .answers.hangman import hangman_words
from .answers.iching import oracle_answer
from .answers.tarot import card_deck
from .answers.words import scramble_words

logger = logging.getLogger("Modmail")
__version__ = "0.2.16 — ```dsconfig\n{given_choices}```"


class GamesTracker:
    """Handles all game statistics tracking and database operations"""
    
    def __init__(self, bot):
        """Initialize with bot reference and database partition"""
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        
    async def log_command(self, ctx, command_name, **kwargs):
        """Log command usage with flexible fields"""
        try:
            entry = {
                'user_id': ctx.author.id,
                'username': str(ctx.author),
                'channel_id': ctx.channel.id,
                'channel_name': ctx.channel.name,
                'command': command_name,
                'timestamp': datetime.utcnow(),
                **kwargs
            }
            await self.db.find_one_and_update(
                {'_id': 'games-tracking'},
                {'$push': {'commands': entry}},
                upsert=True
            )
        except Exception as e:
            print(f"Error logging command: {e}")

    async def get_user_stats(self, user_id):
        """Get statistics for a specific user"""
        aggr = [
            {'$match': {'_id': 'games-tracking'}},
            {'$unwind': '$commands'},
            {'$match': {'commands.user_id': user_id}},
            {'$group': {
                '_id': '$commands.command',
                'count': {'$sum': 1},
                'last_used': {'$max': '$commands.timestamp'}
            }}
        ]
        
        return {doc['_id']: doc async for doc in self.db.aggregate(aggr)}

    async def get_outcome_stats(self, command_name=None):
        """Get win/lose/draw statistics"""
        match_stage = {'commands.result_int': {'$exists': True}}
        if command_name:
            match_stage['commands.command'] = command_name
            
        aggr = [
            {'$match': {'_id': 'games-tracking'}},
            {'$unwind': '$commands'},
            {'$match': match_stage},
            {'$group': {
                '_id': '$commands.command',
                'total': {'$sum': 1},
                'wins': {'$sum': {'$cond': [{'$eq': ['$commands.result_int', 1]}, 1, 0]}},
                'losses': {'$sum': {'$cond': [{'$eq': ['$commands.result_int', 0]}, 1, 0]}},
                'draws': {'$sum': {'$cond': [{'$eq': ['$commands.result_int', 2]}, 1, 0]}}
            }},
            {'$project': {
                'total': 1,
                'wins': 1,
                'losses': 1,
                'draws': 1,
                'win_rate': {
                    '$multiply': [
                        {'$divide': ['$wins', '$total']},
                        100
                    ]
                }
            }}
        ]
        
        return {doc['_id']: doc async for doc in self.db.aggregate(aggr)}

    async def get_leaderboard(self, limit=10):
        """Get top users by command usage"""
        aggr = [
            {'$match': {'_id': 'games-tracking'}},
            {'$unwind': '$commands'},
            {'$group': {
                '_id': {
                    'user_id': '$commands.user_id',
                    'username': '$commands.username'
                },
                'total': {'$sum': 1},
                'commands': {'$addToSet': '$commands.command'}
            }},
            {'$sort': {'total': -1}},
            {'$limit': limit},
            {'$project': {
                'user': '$_id.username',
                'total': 1,
                'commands': {'$size': '$commands'}
            }}
        ]
        
        return [doc async for doc in self.db.aggregate(aggr)]


class Games(commands.Cog):
    """Text based games and oracle commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_manager = EmbedManager(bot)
        self.tracker = GamesTracker(bot)
        # Verify initialization worked
        if not hasattr(self.tracker, 'db'):
            raise RuntimeError("GamesTracker failed to initialize!")
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

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣     8-BALL       ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['8ball'])
    @commands.guild_only()
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

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣     SETTLE       ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['rpsls', 'rps'])
    @commands.guild_only()
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

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣      GUESS       ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command()
    @commands.guild_only()
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
            result_msg = random.choice([
                "Not even close",
                "Better luck next time", 
                "How could you have known",
                "Right number was"
            ])
            result_str = f'{result_msg}: {answer}'
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

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣      FLIP        ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['toss', 'tossacoin'])
    @commands.guild_only()
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

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣     CHOOSE       ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command()
    @commands.guild_only()
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

        picked = random.choice(choices).title()
        given_choices = '\n'.join(f'• {c.title()}' for c in choices)
        embed = await self.embed_manager.create_command_embed(
            ctx,
            title=f'🙈 Options given by {ctx.author.display_name}:',
            description=f"```dsconfig\n{given_choices}```\n### {Emoji.DIAMOND} I choose:\n# {picked}",
            start_time=start_time
        )
        await ctx.send(embed=embed)

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣      TAROT       ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def tarot(self, ctx):
        """Start a tarot reading session"""
        # Send initial message
        message = await ctx.send(GameConfig.TAROT_MESSAGES[0])
        
        # Edit through the sequence with delays
        for msg, delay in zip(GameConfig.TAROT_MESSAGES[1:], GameConfig.TAROT_DELAYS):
            await asyncio.sleep(delay)
            await message.edit(content=msg)
        
        # Final instruction
        final_msg = (
            f"When you feel ready, type:\n"
            f"**`{ctx.prefix}tarot reading`**\n\n"
            "I will shuffle the cards and pick three for you."
        )
        await message.edit(content=final_msg, delete_after=GameConfig.LONG_DELETE_AFTER)

    @tarot.command()
    async def reading(self, ctx, *, question: str = None):
        """Perform a 3-card tarot reading"""
        u = ctx.author
        
        try:
            # Send initial message and simulate shuffling
            message = await ctx.send(f"Allow me to shuffle my Tarot deck... {u.display_name}")
            await ctx.channel.typing()
            await asyncio.sleep(random.randint(5, 9))
            
            # Draw 3 unique cards
            start_time = time.time()
            cards = random.sample(self.card_deck, 3)
            positions = [
                "1️⃣ **The Past:** — Influences, roots, or unresolved energies. This card reveals events or relationships that shaped your current situation.",
                "2️⃣ **The Present:** — The heart of the matter. Reflects your current mindset or external circumstances affecting you now.",
                "3️⃣ **The Future:** — Probable outcome or advice. Suggests where things may lead and what perspective to embrace."
            ]
            
            # Build the reading embed
            embed = await self.embed_manager.create_command_embed(
                ctx,
                title=f"𝖳𝖺𝗋𝗈𝗍 𝖱𝖾𝖺𝖽𝗂𝗇𝗀 𝖿𝗈𝗋 {u.display_name}",
                description=(
                    "The **Three-Card Spread** reveals your situation across time —\n"
                    "showing past influences, present circumstances, and likely future outcomes."
                ),
                thumbnail=GameConfig.TAROT_DECK_IMAGE,
                start_time=start_time
            )

            # Add each card as a separate field
            for pos, card in zip(positions, cards):
                embed.add_field(
                    name=pos,
                    value=card,
                    inline=False
                )
            
            if question:
                embed.add_field(
                    name="🤔 𝖸𝗈𝗎𝗋 𝗊𝗎𝖾𝗌𝗍𝗂𝗈𝗇:",
                    value=f"> {question}",
                    inline=False
                )

            await message.edit(content=None, embed=embed)
            await self.tracker.log_command(
                ctx,
                'tarot_reading',
                question=question,
                result_str=" | ".join(card.split('\n')[0][:30] for card in cards)  # Truncate long card names
            )
            
        except Exception as e:
            logger.error(f"Tarot error: {e}")
            await ctx.send("The cards refuse to speak... (An error occurred)", delete_after=5)

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣     i-CHING      ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['i-ching', 'oracle'])
    @commands.guild_only()
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

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣   FUTHARK RUNE   ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['futhark'])
    @commands.guild_only()
    async def rune(self, ctx, *, query: str = None):
        """Draw a Viking rune"""
        start_time = time.time()
        rune = random.choice(self.runes_list)
        
        # Get a random draw (Upright or Reversed)
        draw_type, meaning = random.choice(list(rune['rune_draw'].items()))
        
        embed = await self.embed_manager.create_command_embed(
            ctx,
            title=f'{rune["rune_name"]} ({rune["rune_title"]}) - {draw_type}',
            description=meaning,
            color=int(rune['colour'], 16),
            thumbnail=rune['rune_img'],
            start_time=start_time
        )
        
        if query:
            embed.insert_field_at(0, {
                'name': 'Question',
                'value': query,
                'inline': False
            })
            
        await ctx.send(embed=embed)
        await self.tracker.log_command(
            ctx,
            'rune',
            question=query,
            result_str=f"{rune['rune_name']} ({draw_type})"
        )

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣    ROLL DICE     ╠════════════════════╣
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

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣  FORTUNE COOKIE  ╠════════════════════╣
    # ╚════════════════════╩══════════════════╩════════════════════╝
    @commands.command(aliases=['fortune'])
    @commands.guild_only()
    async def cookie(self, ctx):
        """Get a random fortune cookie message"""
        start_time = time.time()
        
        fortune = random.choice(self.fortune_cookies)
        cooky = f'```toml\n[{fortune}]```'
        embed = await self.embed_manager.create_command_embed(
            ctx,
            title=f'🥠 Fortune Cookie for {ctx.author.display_name}:',
            description=cooky,
            thumbnail='https://i.imgur.com/MHkzgHU.png',
            start_time=start_time
        )
        await ctx.send(embed=embed)
        await self.tracker.log_command(
            ctx,
            'fortune_cookie',
            result_str=fortune
        )

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣     HANGMAN      ╠════════════════════╣
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

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣    UNSCRAMBLE    ╠════════════════════╣
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
            title='🔤 𝖶𝗈𝗋𝖽 𝖲𝖼𝗋𝖺𝗆𝖻𝗅𝖾',
            description=(
                f"# 𝖧𝗂𝗇𝗍: {len(word)} 𝗅𝖾𝗍𝗍𝖾𝗋𝗌"
            ),
            thumbnail="https://i.imgur.com/wydPdrN.png",
            fields=[
                {
                    'name': '𝖴𝗇𝗌𝖼𝗋𝖺𝗆𝖻𝗅𝖾 𝗍𝗁𝗂𝗌 𝗐𝗈𝗋𝖽:',
                    'value': f'```ini\n[ {scrambled} ]\n```',
                    'inline': False
                    },
                {
                    'name': '𝖧𝗈𝗐 𝗍𝗈 𝖯𝗅𝖺𝗒:',
                    'value': '𝖳𝗒𝗉𝖾 𝗒𝗈𝗎𝗋 𝖺𝗇𝗌𝗐𝖾𝗋 𝗂𝗇 𝖼𝗁𝖺𝗍.',
                    'inline': False
                    }
                ],
            footer_text="𝖸𝗈𝗎 𝗁𝖺𝗏𝖾 𝗍𝗐𝗈 𝗆𝗂𝗇𝗎𝗍𝖾𝗌! ",
            start_time=start_time
        )
        
        await ctx.send(embed=embed)
        await self.tracker.log_command(
            ctx,
            'scramble_start',
            question=word
        )
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=120)
            if msg.content.upper() == word:
                await ctx.send(f"# ✅ 𝖢𝗈𝗋𝗋𝖾𝖼𝗍, {ctx.author.mention}!\n```ini\n[ 𝖳𝗁𝖾 𝗐𝗈𝗋𝖽 𝗐𝖺𝗌 {word} ]\n```")
            else:
                await ctx.send(f"# ❌ 𝖭𝗈𝗉𝖾! 𝖳𝗁𝖾 𝖼𝗈𝗋𝗋𝖾𝖼𝗍 𝗐𝗈𝗋𝖽 𝗐𝖺𝗌 **{word}**.")
        except asyncio.TimeoutError:
            await ctx.send(f"# ⏰ 𝖳𝗂𝗆𝖾’𝗌 𝗎𝗉, {ctx.author.mention}!\n```ini\n[ 𝖳𝗁𝖾 𝗐𝗈𝗋𝖽 𝗐𝖺𝗌 {word} ]\n```")


    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣   GAMES STATS    ╠════════════════════╣
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

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣     OUTCOMES     ╠════════════════════╣
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

    # ╔════════════════════╦══════════════════╦════════════════════╗
    # ╠════════════════════╣   LEADERBOARD    ╠════════════════════╣
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
                name=f"{i}. {entry['username']}",
                value=(
                    f"Commands: {entry['total']}\n"
                    f"Different games: {entry['commands']}"
                ),
                inline=False
            )
            
        await ctx.send(embed=embed)

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


async def setup(bot):
    await bot.add_cog(Games(bot))
