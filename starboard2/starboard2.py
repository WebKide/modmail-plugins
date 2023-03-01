import discord

from discord.ext import commands

class Starboard(commands.Cog):
    """─=≡Σ(つಠ益ಠ)つ private cog for my personal discord guild, it won't work on yours! """
    def __init__(self, bot):
        self.bot = bot
        self.star_emoji = '⭐'
        self.star_count = 1
        self.guild_id = 328341202103435264 # ID of my Guild
        self.starboard_channel_id = 729093473487028254 # ID of my Starboard channel
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.channel_id == self.starboard_channel_id and payload.emoji.name == self.star_emoji:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)

        guild = bot.get_guild(self.guild_id)
        if guild is None:
            # handle the error here, e.g. log a warning and return
            return
        member = guild.get_member(payload.user_id)
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return

        message = await channel.fetch_message(payload.message_id)
        if message is None:
            return

        if payload.user_id == self.bot.user.id:
            return

        channel = await self.bot.fetch_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        
        message = await channel.fetch_message(payload.message_id)
        if not message:
            return
        
        starboard_channel = await self.bot.fetch_channel(self.starboard_channel_id)
        if not isinstance(starboard_channel, discord.TextChannel):
            return
        
        reactions = message.reactions
        star_reaction = None
        for reaction in reactions:
            if reaction.emoji == self.star_emoji:
                star_reaction = reaction
                break
        
        if star_reaction.count < self.star_count:
            return
        
        embed = discord.Embed(description=message.content)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
        embed.add_field(name='Original', value=f'[Jump!]({message.jump_url})')
        embed.add_field(name='Stars', value=star_reaction.count)
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        
        await starboard_channel.send(embed=embed)
        
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name != self.star_emoji:
            return
        
        channel = await self.bot.fetch_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        
        message = await channel.fetch_message(payload.message_id)
        if not message:
            return
        
        starboard_channel = await self.bot.fetch_channel(self.starboard_channel_id)
        if not isinstance(starboard_channel, discord.TextChannel):
            return
        
        reactions = message.reactions
        star_reaction = None
        for reaction in reactions:
            if reaction.emoji == self.star_emoji:
                star_reaction = reaction
                break
        
        if not star_reaction:
            return
        
        if star_reaction.count < self.star_count:
            starboard_message = await starboard_channel.fetch_message(star_reaction.message_id)
            if starboard_message:
                await starboard_message.delete()
                
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        starboard_channel = await self.bot.fetch_channel(self.starboard_channel_id)
        if not isinstance(starboard_channel, discord.TextChannel):
            return
        
        try:
            starboard_message = await starboard_channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
        
        original_message_id = starboard_message.embeds[0].fields[0].value.split('/')[-1]
        channel = await self.bot.fetch_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        
        message = await channel.fetch_message(original_message_id)
        if not message:
            return
        
        reactions = message.reactions
        star_reaction = None
        for reaction in reactions:
            if reaction.emoji == self.star_emoji:
                star_reaction = reaction
                break
        
        if not star_reaction:
            await starboard_message.delete()
            return
        
        if star_reaction.count < self.star_count:
            await starboard_message.delete()
            return
        
        if star_reaction.count < self.star_count:
            await starboard_message.delete()
            return

        # Check if there is already a message on the starboard for this message
        existing_message = None
        for m in await starboard_channel.history(limit=100).flatten():
            if m.embeds and m.embeds[0].footer.text == f"Starboard ID: {message.id}":
                existing_message = m
                break

        # If there's an existing message, update its star count and return
        if existing_message:
            embed = existing_message.embeds[0]
            embed.set_field_at(0, name="Stars", value=f"{star_reaction.count}")
            await existing_message.edit(embed=embed)
            return

        # Otherwise, create a new starboard message
        embed = discord.Embed(
            title=message.content,
            color=discord.Color.gold(),
            timestamp=message.created_at,
            url=message.jump_url,
        )
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
        embed.set_footer(text=f"Starboard ID: {message.id}")
        embed.add_field(name="Channel", value=message.channel.mention)
        embed.add_field(name="Stars", value=f"{star_reaction.count}")
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        await starboard_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Starboard(bot))
