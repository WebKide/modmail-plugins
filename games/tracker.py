from discord.ext import commands
from datetime import datetime

class GamesTracker:
    def __init__(self, bot):
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
        
        return {doc['_id']: doc for doc in await self.db.aggregate(aggr)}

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
        
        return {doc['_id']: doc for doc in await self.db.aggregate(aggr)}

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
