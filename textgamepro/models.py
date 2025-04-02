from datetime import datetime, timedelta
from enum import Enum
import math

class GameType(Enum):
    RPSLS = "rock-paper-scissors-lizard-spock"
    GUESS = "number-guessing"
    WORD_SCRAMBLE = "word-scramble"
    COIN_FLIP = "coin-flip"

class GameOutcome(Enum):
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"

class Scoreboard:
    def __init__(self, db_partition):
        self.db = db_partition
        
    async def record_game(self, player_id: int, game_type: GameType, outcome: GameOutcome, score: int = 0):
        """Record a game session and update statistics"""
        # Record the session
        await self.db.insert_one({
            'type': 'game_session',
            'player_id': player_id,
            'game_type': game_type.value,
            'outcome': outcome.value,
            'score': score,
            'timestamp': datetime.utcnow()
        })
        
        # Update or create player stats
        stats_key = f"stats:{player_id}:{game_type.value}"
        stats = await self.db.find_one({'_id': stats_key}) or {
            '_id': stats_key,
            'player_id': player_id,
            'game_type': game_type.value,
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'current_streak': 0,
            'highest_score': 0,
            'last_played': None,
            'activity_score': 0
        }
        
        # Update stats
        stats['total_games'] += 1
        stats['last_played'] = datetime.utcnow()
        
        if outcome == GameOutcome.WIN:
            stats['wins'] += 1
            stats['current_streak'] = max(1, stats.get('current_streak', 0) + 1)
        elif outcome == GameOutcome.LOSS:
            stats['losses'] += 1
            stats['current_streak'] = min(-1, stats.get('current_streak', 0) - 1)
        else:
            stats['draws'] += 1
            
        if score > stats['highest_score']:
            stats['highest_score'] = score
            
        # Calculate activity score
        stats['activity_score'] = self.calculate_activity_score(stats)
        
        await self.db.find_one_and_update(
            {'_id': stats_key},
            {'$set': stats},
            upsert=True
        )
        
    def calculate_activity_score(self, stats):
        """Calculate time-decayed activity score"""
        if not stats['last_played']:
            return 0
            
        days_since_active = (datetime.utcnow() - stats['last_played']).days
        win_ratio = (stats['wins'] + (stats['draws'] * 0.5)) / max(1, stats['total_games'])
        activity_modifier = max(0, 1 - (days_since_active / 30))  # 30-day decay period
        
        return win_ratio * activity_modifier * math.log(stats['total_games'] + 1)
        
    async def get_player_stats(self, player_id: int, game_type: GameType = None):
        """Get statistics for a player"""
        query = {'player_id': player_id}
        if game_type:
            query['game_type'] = game_type.value
            
        return await self.db.find(query).to_list(None)
        
    async def get_leaderboard(self, game_type: GameType, limit: int = 10):
        """Get leaderboard for a specific game"""
        return await self.db.find({'game_type': game_type.value})
            .sort('activity_score', -1)
            .limit(limit)
            .to_list(None)
