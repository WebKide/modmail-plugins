from .games import Games

def __init__(self, bot):
    self.bot = bot
    self.tracker = GamesTracker(bot)
    # ... other initializations ...
