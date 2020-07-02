import discord, unicodedata, inspect, urllib.request

from discord.ext import commands


class Misc:
    """Useful commands to make your life easier"""
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange

    @commands.command(no_pm=True)
    async def name(self, ctx, text: str = None):
        """ Change Bot's name """
        if text is None:
            return await ctx.send("What's my new name going to be?")

        if text is not None:
            try:
                await ctx.bot.edit_profile(username=str(text[6:]))
                await ctx.send(f'Thanks for renaming me: {text}')
                await ctx.message.delete()
            except Exception as e:
                await ctx.send(f'Failed to change my name!\n```{e}```')
                pass

    @commands.command(no_pm=True)
    async def logo(self, ctx, link: str = None):
        """ Change Bot's avatar img """
        if link is None:
            return await ctx.send('You need to use an image URL as a link.')

        if link is not None:
            try:
                with urllib.request.urlopen(link) as response:
                    img = response.read()
                    await ctx.bot.edit_profile(avatar=img)
                    await ctx.send('New logo added successfully!', delete_after=5)
                    await ctx.message.delete()
            except Exception as e:
                await ctx.send(f'Failed to update logo image!\n```{e}```')
                pass

    @commands.command(no_pm=True)
    async def sauce(self, ctx, *, command: str = None):
        """ See the source code for any command """
        if command is not None:
            i = str(inspect.getsource(self.bot.get_command(command).callback))

            if len(i) < 1980:
                source_full = i.replace('```', '`\u200b`\u200b`')
                await ctx.send('```py\n' + source_full + '```')

            if len(i) > 1981:
                source_trim = i.replace('```', '`\u200b`\u200b`')[:1980]
                await ctx.send('```py\n' + source_trim + '```')

        else:
            await ctx.send(f"Tell me what cmd's source code you want to see.")

    @commands.command()
    async def charinfo(self, ctx, *, characters: str):
        """
        Return UNICODE characters
        Usage:
        charinfo ā
        """
        if len(characters) > 15:
            return await ctx.send('Too many characters ({}/15)'.format(len(characters)))

        else:
            fmt = '​`{2}​` — `\\U{0:>08}​`\n​```tex\n\\N{{{1}}}​```'

            def to_string(c):
                digit = format(ord(c), 'x')
                name = unicodedata.name(c, 'Name not found.')
                return fmt.format(digit, name, c)

            e = discord.Embed(color=self.user_color)
            e.description = '\n'.join(map(to_string, characters))
            # e.add_field(name='', value=f"```tex\n\\N{{{1}}}​```")
            await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Misc(bot))
