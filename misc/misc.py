import discord
from discord.ext import commands
import unicodedata
import inspect
import io
import urllib.request


dev_list = [323578534763298816]


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    @commands.command()
    @commands.has_role('Journalist')
    async def botname(self, ctx, text: str):
        """Change Bot's name"""
        if ctx.author.id in dev_list:
            try:
                #await self.edit_profile(username=str(text[6:]))
                await ctx.bot.user.edit_profile(username=text)
                await ctx.send('Thanks for renaming me!', delete_after=5)
                await ctx.message.delete()
            except Exception as e:
                await ctx.send(f'Failed to change my name!\n```{e}```')
                pass

    @commands.command()
    @commands.has_role('Journalist')
    async def botlogo(self, ctx, link: str):
        """Change the logo of the bot"""
        if link != None:
            link = 'https://i.imgur.com/TGj0HJD.jpg'
            async with ctx.session.get(link) as response:
                img = await response.read()
                with io.BytesIO(img) as file:
                    await bot.user.edit(avatar=file)
        if ctx.author.id in dev_list:
            try:
                async with ctx.session.get(link) as response:
                    img = await response.read()
                    with io.BytesIO(img) as file:
                        await bot.user.edit(avatar=file)
                    await ctx.send('New logo added successfully!', delete_after=5)
                    await ctx.message.delete()
            except Exception as e:
                await ctx.send(f'Failed to update logo image!\n```{e}```')
                pass

    @commands.command(hidden=True)
    @commands.has_any_role('Admin', 'Mod', 'Journalist', 'Owner')
    async def sauce(self, ctx, *, command):
        """See the source code for any command."""
        source = str(inspect.getsource(self.bot.get_command(command).callback))
        try:
            await ctx.send('```py\n' + source + '```')
        except:
            await ctx.send('The command source is too long to send.')

    @commands.command(aliases=['ch'], no_pm=True)
    async def channels(self, ctx):
        """Return all channels"""
        text = []
        #voice = []
        #for TextChannel in sorted(ctx.message.guild.text_channels, key=lambda c: c.position):
        #    TextChannel.append('#' + TextChannel.name)

        for i in ctx.message.guild.text_channels:
            text.append('#' + i)
        em1 = discord.Embed(title='Text Channels')
        em1.description = '\n'.join(text)
        em1.colour = (discord.Colour(0xed791d))

        '''for VoiceChannel in sorted(ctx.message.guild.voice_channels, key=lambda c: c.position):
            VoiceChannel.append('#' + VoiceChannel.name)
        em2 = discord.Embed(title='Voice Channels')
        em2.description = '\n'.join(VoiceChannel)
        em2.colour = (discord.Colour(0xFFFFFF))'''
        await ctx.send(embed=em1)
        #await ctx.send(embed=em2)

    @commands.command()
    async def charinfo(self, ctx, *, characters: str):
        """Shows you UNICODE characters for emotes"""
        if len(characters) > 15:
            return await ctx.send('Too many characters ({}/15)'.format(len(characters)))

        fmt = '​`{2}​` — `\\U{0:>08}​`: ​\n`\\N{{{1}}}​`'

        def to_string(c):
            digit = format(ord(c), 'x')
            name = unicodedata.name(c, 'Name not found.')
            return fmt.format(digit, name, c)

        await ctx.send('\n'.join(map(to_string, characters)))


def setup(bot):
    bot.add_cog(Misc(bot))
