import discord, datetime
from discord.ext import commands
from discord.embeds import EmptyEmbed


class CustomEmbeds:
    @classmethod
    def starboard(cls, message, **kwargs):
        title = kwargs.get('title', EmptyEmbed)
        description = kwargs.get('description', f'{message.content}\n [Jump To](https://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id})')
        url = kwargs.get('url', EmptyEmbed)
        color = kwargs.get('color', 13103696)
        author = kwargs.get('author', ':star: Starboard :star:')

        embed = discord.Embed(color=color,
                              description=description)
        embed.set_footer(text=f"Author: {message.author}", icon_url=message.author.avatar_url)
        return embed


class Starboard:
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Starboard2 hopefully a working one"""
    def __init__(self, index, channel, emotes, threshold, activated=True):
        self.id = index
        self.channel = channel
        self.emotes = emotes
        self.threshold = threshold
        self.time = datetime.datetime.utcnow()
        self.activated = activated

    def serialize(self):
        return {
            "_id": self.id,
            "channel": self.channel.id,
            "emotes": self.emotes,
            "threshold": self.threshold,
            "created": self.time,
            "activated": self.activated
        }


class StarboardCog(commands.Cog, name="Starboard"):
    """Cog for creating advanced starboards"""
    def __init__(self, bot):
        self.bot = bot
        self.starboards_collection = bot.db["starboard"]
        self.starboard_sent_collection = bot.db["starboard_sent"]

    @commands.group(name='starboard')
    async def starboard(self, ctx):
        """A Group of Commands useful for interacting with starboards"""
        pass

    @starboard.command(name='add', aliases=["new", "create"])
    @commands.has_permissions(manage_channels=True)
    async def add_starboard(self, ctx):
        """Runs interactive prompt for creating a new starboard"""
        channel = await ctx.get_text_channel(embed=CustomEmbeds.add(author="Channel",
                                                                    description="Send a channel to add it to the starboard!"))
        emotes = await ctx.get_emotes(embed=CustomEmbeds.add(author="Emotes",
                                                             description="React with emotes and then click ✅ to add them to the starboard."))
        threshold = await ctx.get_int(embed=CustomEmbeds.add(author="Add a Threshold",
                                                             description="Send message with the minimum number of reactions for it to be added to the starboard."))

        guild_starboards = await self.starboards_collection.find_one({"_id": ctx.guild.id})
        if guild_starboards is None:
            starboard_len = 0
        else:
            starboard_len = len(guild_starboards.get("starboards"))

        starboard = Starboard(index=starboard_len,
                              channel=channel,
                              emotes=emotes,
                              threshold=threshold)

        await self.db_add_starboard(ctx.guild, starboard.serialize())
        await ctx.send(embed=CustomEmbeds.confirm(author="Starboard Added", description=f"ID: {starboard_len}\n"
                                                                                        f"Channel: {channel.mention}\n"
                                                                                        f"Emotes: {' '.join(emotes)}\n"
                                                                                        f"Threshold: {threshold}"))

    @starboard.command(name='del', aliases=["delete", "remove"])
    @commands.has_permissions(manage_channels=True)
    async def delete_starboard(self, ctx, index: int = None):
        """Deletes a starboard. Specify a number to delete a specific starboard or no number to delete all"""
        if index is None and await ctx.confirm(prompt="Delete all starboards?"):
            self.starboards_collection.update_one({"_id": ctx.guild.id}, {"$set": {"starboards": []}})

        self.starboards_collection.update_one({"_id": ctx.guild.id}, {"$pull": {"starboards": {"_id": index}}})
        starboards = (await self.starboards_collection.find_one({"_id": ctx.guild.id})).get("starboards")
        for starboard in starboards:
            if starboard.get("_id") > index:
                starboard["_id"] -= 1

        await self.starboards_collection.update_one({"_id": ctx.guild.id}, {"$set": {"starboards": starboards}})
        await ctx.send(embed=CustomEmbeds.remove(author="Removed Starboard"))

    @starboard.command(name='list', aliases=["show"])
    async def list_starboard(self, ctx):
        """Lists all guild starboards"""
        entries = []
        guild_starboards = await self.starboards_collection.find_one({"_id": ctx.guild.id})

        if guild_starboards is None or guild_starboards.get("starboards") is None:
            entries.append(("No Starboards", "This guild has no starboards setup"))
            return await StarboardPages(ctx, entries=entries).paginate()
        starboards = guild_starboards.get("starboards")

        entries.append(("Guild Starboard Status", f"Activated: `{guild_starboards.get('activated')}`"))

        for starboard in starboards:
            entries.append((f"Starboard #{starboard.get('_id')}", f"Channel: <#{starboard.get('channel')}>\n"
                            f"Emotes: {' '.join(starboard.get('emotes'))}\n"
                            f"Threshold: `{starboard.get('threshold')}`\n"
                            f"Created: `{starboard.get('created').strftime('%b %d %Y %H:%M:%S')}`\n"
                            f"Activated: `{starboard.get('activated')}`"))

        pages = StarboardPages(ctx, entries=entries)
        await pages.paginate()

    @starboard.command(name='activate', aliases=['on'])
    @commands.has_permissions(manage_channels=True)
    async def starboard_activate(self, ctx, s_id: int = None):
        """Activate a specific starboard by number or activate guild starboards"""
        if s_id is None:
            await self.starboards_collection.update_one({"_id": ctx.guild.id}, {"$set": {"activated": True}},
                                                        upsert=True)
        else:
            await self.starboards_collection.update_one({"_id": ctx.guild.id, "starboards._id": s_id},
                                                        {"$set": {"starboards.$.activated": True}}, upsert=True)

        await ctx.send(embed=CustomEmbeds.confirm(author="Activated!"))

    @starboard.command(name='deactivate', aliases=['off'])
    @commands.has_permissions(manage_channels=True)
    async def starboard_deactivate(self, ctx, s_id: int = None):
        """Deactivate a specific starboard by number or deactivate guild starboards"""
        if s_id is None:
            await self.starboards_collection.update_one({"_id": ctx.guild.id}, {"$set": {"activated": False}},
                                                        upsert=True)
        else:
            await self.starboards_collection.update_one({"_id": ctx.guild.id, "starboards._id": s_id},
                                                        {"$set": {"starboards.$.activated": False}}, upsert=True)

        await ctx.send(embed=CustomEmbeds.confirm(author="Deactivated!"))

    async def db_add_starboard(self, guild, starboard):
        await self.starboards_collection.update_one({"_id": guild.id},
                                                    {"$setOnInsert": {"starboards": [], "activated": True}},
                                                    upsert=True)
        await self.starboards_collection.update_one({"_id": guild.id}, {"$push": {"starboards": starboard}})

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild_starboard_db = await self.starboards_collection.find_one({"_id": payload.guild_id})

        if guild_starboard_db is None or "starboards" not in guild_starboard_db:
            return

        guild_starboards = guild_starboard_db.get("starboards")

        if not guild_starboard_db.get("activated", False):
            return

        if await self.starboard_sent_collection.find_one({"_id": payload.message_id}) is not None:
            return

        reaction_emoji = payload.emoji
        reaction_guild = self.bot.get_guild(payload.guild_id)
        reaction_channel = reaction_guild.get_channel(payload.channel_id)
        reaction_message = await reaction_channel.fetch_message(payload.message_id)

        for starboard in guild_starboards:
            if not starboard.get("activated", False):
                continue

            if str(reaction_emoji) in starboard.get("emotes"):
                for r in reaction_message.reactions:
                    if r.count >= starboard.get("threshold"):
                        starboard_channel = reaction_guild.get_channel(starboard.get("channel"))
                        sent = await starboard_channel.send(embed=CustomEmbeds.starboard(reaction_message))
                        await self.starboard_sent_collection.update_one({"_id": payload.message_id}, {
                            "$setOnInsert": {"guild": payload.guild_id,
                                             "reaction_channel": payload.channel_id,
                                             "reaction_message": payload.message_id,
                                             "starboard_channel": starboard.get("channel"),
                                             "starboard_message": sent.id,
                                             "content": reaction_message.content,
                                             "created": datetime.datetime.utcnow()}}, upsert=True)


def setup(bot):
    bot.add_cog(StarboardCog(bot))
