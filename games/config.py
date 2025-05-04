class GameConfig:
    # Image URLs
    COIN_IMAGES = {
        'heads': 'https://i.imgur.com/ygrKmgh.png',
        'tails': 'https://i.imgur.com/tDfAVCx.png',
        'edge': 'https://i.imgur.com/6Os6BBY.png'
    }
    COIN_DESCRIPTION = '1926 Golden Dollar coin'
    
    EIGHTBALL_IMAGE = 'https://i.imgur.com/GVFY7ry.png'
    TAROT_DECK_IMAGE = 'https://i.imgur.com/rUAjxYx.png'
    ICHING_IMAGE = 'http://i.imgur.com/biEvXBN.png'
    DICE_IMAGE = 'https://i.imgur.com/N4d4X3h.png'
    COOKIE_IMAGE = 'https://i.imgur.com/MHkzgHU.png'
    HANGMAN_IMAGE = 'https://i.imgur.com/EksOlTe.png'
    UNSCRAMBLE_IMAGE = 'https://i.imgur.com/wydPdrN.png'
    
    # Game settings
    GUESS_RANGE = (1, 11)  # min, max
    FLIP_EDGE_CHANCE = 0.09  # 9% chance
    COIN_FLIP_MIN = 3
    COIN_FLIP_MAX = 101
    
    # Processing messages
    TAROT_MESSAGES = [
        "☺️ Please relax and focus on your question...",
        "👃 Inhale deeply through your nose...",
        "👄 Exhale fully through your mouth..."
    ]
    TAROT_DELAYS = [3, 6, 6]  # in seconds
    
    # Text constants
    RPSLS_DESCRIPTION = (
        "```diff\n"
        "“Scissors cut paper, paper covers rock, rock crushes lizard, "
        "lizard poisons Spock, Spock smashes scissors, scissors decapitate lizard, "
        "lizard eats paper, paper disproves Spock, Spock vaporizes rock and, "
        "as it's always been, rock crushes scissors.”``` ~Sheldon Cooper,\n"
        "The Big Bang Theory S02E08 — 'The Lizard-Spock Expansion'"
    )
    
    ADVICE_FOOTER = "𝖮𝗋𝖺𝖼𝗅𝖾"
    
    # Timing
    DEFAULT_DELETE_AFTER = 23  # seconds
    SHORT_DELETE_AFTER = 6
    LONG_DELETE_AFTER = 69
    
    # Input validation
    ALLOWED_CHARS = r'[^a-zA-Z0-9!&@#\-_\"\',.:;()|\s\?]'
    MAX_INPUT_LENGTH = 1080
    
    # Colors
    EMBED_COLORS = {
        'mod': 0x7289da,    # Blurple
        'user': 0xed791d,   # Orange
        'success': 0x2ecc71, # Green
        'error': 0xe74c3c,   # Red
        'warning': 0xf39c12, # Yellow
        'coin_heads': 0xa84300,
        'coin_tails': 0x1f8b4c,
        'coin_edge': 0x23272a,
        'iching': 0xc5b358
    }

class Emoji:
    EIGHTBALL = '\N{BILLIARDS}'
    MEDAL = '\N{SPORTS MEDAL}'
    WARNING = '\N{OCTAGONAL SIGN}'
    DIAMOND = '\N{SMALL ORANGE DIAMOND}'
    NO_ENTRY = '\N{NO ENTRY SIGN}'
    BEGINNER = '\N{JAPANESE SYMBOL FOR BEGINNER}'
    CRYSTAL_BALL = '\N{CRYSTAL BALL}'
    
    # Keycap numbers
    KEYCAP_1 = '1\N{COMBINING ENCLOSING KEYCAP}'
    KEYCAP_2 = '2\N{COMBINING ENCLOSING KEYCAP}'
    KEYCAP_3 = '3\N{COMBINING ENCLOSING KEYCAP}'
