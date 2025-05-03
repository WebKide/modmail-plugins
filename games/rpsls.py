from enum import Enum
import random
import discord
from .config import GameConfig, Emoji

class RPSLSChoice(Enum):
    """Represents the possible choices in RPSLS with their display values"""
    ROCK = "\N{RAISED FIST} **Rock!**"
    PAPER = "\N{PAGE FACING UP} **Paper!**"
    SCISSORS = "\N{BLACK SCISSORS} **Scissors!**"
    LIZARD = "\N{LIZARD} **Lizard!**"
    SPOCK = "\N{RAISED HAND WITH PART BETWEEN MIDDLE AND RING FINGERS} **Spock!**"

class RPSLSGame:
    """
    Handles all Rock-Paper-Scissors-Lizard-Spock game logic including:
    - Choice validation
    - Outcome determination
    - Embed generation
    """
    RULES = {
        RPSLSChoice.ROCK: [RPSLSChoice.SCISSORS, RPSLSChoice.LIZARD],
        RPSLSChoice.PAPER: [RPSLSChoice.ROCK, RPSLSChoice.SPOCK],
        RPSLSChoice.SCISSORS: [RPSLSChoice.PAPER, RPSLSChoice.LIZARD],
        RPSLSChoice.LIZARD: [RPSLSChoice.PAPER, RPSLSChoice.SPOCK],
        RPSLSChoice.SPOCK: [RPSLSChoice.ROCK, RPSLSChoice.SCISSORS]
    }

    @classmethod
    def parse_choice(cls, argument: str) -> RPSLSChoice:
        """Convert string input to RPSLSChoice enum"""
        argument = argument.lower()
        for choice in RPSLSChoice:
            if choice.name.lower() == argument:
                return choice
        raise ValueError(f"Invalid choice: {argument}")

    @classmethod
    def get_random_choice(cls) -> RPSLSChoice:
        """Get a random valid choice"""
        return random.choice(list(RPSLSChoice))

    @classmethod
    def determine_outcome(cls, player_choice: RPSLSChoice, bot_choice: RPSLSChoice) -> int:
        """
        Determine game outcome
        Returns: 1 for win, 0 for lose, 2 for draw
        """
        if player_choice == bot_choice:
            return 2
        return 1 if bot_choice in cls.RULES[player_choice] else 0

    @classmethod
    async def create_game_embed(
        cls,
        embed_manager,
        ctx,
        player_choice: RPSLSChoice,
        bot_choice: RPSLSChoice,
        outcome: int,
        start_time: float = None
    ) -> discord.Embed:
        """Generate a standardized embed for RPSLS results"""
        if outcome == 1:  # Win
            color = embed_manager.colors['success']
            result_text = "You win!"
            icon = Emoji.DIAMOND
        elif outcome == 0:  # Lose
            color = embed_manager.colors['error']
            result_text = "You lose..."
            icon = Emoji.NO_ENTRY
        else:  # Draw (2)
            color = embed_manager.colors['mod']
            result_text = "We're square"
            icon = Emoji.BEGINNER

        return await embed_manager.create_command_embed(
            ctx,
            color=color,
            fields=[
                {
                    'name': f'{ctx.bot.user.display_name} chose:',
                    'value': bot_choice.value,
                    'inline': True
                },
                {
                    'name': f'{ctx.author.display_name} chose:',
                    'value': player_choice.value,
                    'inline': True
                }
            ],
            footer_text=f"{icon} {result_text}",
            start_time=start_time
        )

    @classmethod
    def get_help_embed(cls, embed_manager, ctx) -> discord.Embed:
        """Generate the help embed explaining RPSLS rules"""
        return embed_manager.create_base_embed(
            ctx,
            color=embed_manager.colors['warning'],
            description=GameConfig.RPSLS_DESCRIPTION
        )
