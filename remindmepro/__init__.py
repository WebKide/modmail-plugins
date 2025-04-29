# modmail-plugins/RemindMePro/__init__.py
from .remindmepro import RemindMePro

async def setup(bot):
    """Setup function for the plugin"""
    await bot.add_cog(RemindMePro(bot))

'''
async def setup(bot):
    """Setup function for the plugin"""
    plugin = RemindMePro(bot)
    await bot.add_cog(plugin)
'''
