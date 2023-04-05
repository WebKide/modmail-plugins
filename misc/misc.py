"""
MIT License
Copyright (c) 2020 WebKide [d.id @323578534763298816]
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import discord, aiohttp, io, asyncio, random, textwrap, traceback, inspect2

from discord.ext import commands
from discord import File

dev_list = [323578534763298816]


class Misc(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Useful commands to make your life easier """
    def __init__(self, bot):
        self.bot = bot
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange
        self.allowed_file_types = ['.png', '.jpg', '.jpeg', '.pdf', '.doc', '.docx', '.txt', '.gif', '.mp3']

    async def format_mod_embed(self, ctx, user, success, method):
        """ Helper func to format an embed to prevent extra code """
        emb = discord.Embed()
        emb.set_author(name=method.title(), icon_url=user.avatar_url)
        emb.colour = (discord.Colour(0xed791d))
        emb.set_footer(text=f'User ID: {user.id}')
        if success:
            if method == 'ban':
                emb.description = f'{user} was just {method}ned.'
            else:
                emb.description = f'{user} was just {method}ed.'
        else:
            emb.description = f"You do not have the permissions to {method} users."

        return emb

    async def parse_embed_message(self, message):
        ''' Parse the embed message and return it as a dictionary '''
        # Split the command arguments using '|' as the separator
        args = message.content.split('|')

        # Remove whitespace and quotes from the arguments
        args = [arg.strip().strip('"') for arg in args]

        # Create the embed message dictionary
        embed_dict = {}
        for arg in args:
            # Split the argument using the first space as the separator
            split_arg = arg.split(' ', 1)

            # Get the argument name and value
            arg_name = split_arg[0]
            arg_value = split_arg[1]

            # If the value is surrounded by quotes, unwrap it
            if arg_value.startswith('"') and arg_value.endswith('"'):
                arg_value = textwrap.dedent(arg_value.strip('"'))

            # Add the argument to the embed dictionary
            if arg_name == "embed_title":
                embed_dict["title"] = arg_value
            elif arg_name == "embed_description":
                embed_dict["description"] = arg_value
            elif arg_name == "embed_url":
                embed_dict["url"] = arg_value
            elif arg_name == "embed_timestamp":
                embed_dict["timestamp"] = arg_value
            elif arg_name == "embed_color":
                embed_dict["color"] = int(arg_value, 0)
            elif arg_name == "embed_footer":
                footer_split = arg_value.split(',')
                footer_dict = {
                    "text": footer_split[0].strip(),
                    "icon_url": footer_split[1].strip()
                }
                embed_dict["footer"] = footer_dict
            elif arg_name == "embed_image":
                embed_dict["image"] = {"url": arg_value}
            elif arg_name == "embed_thumbnail":
                embed_dict["thumbnail"] = {"url": arg_value}
            elif arg_name == "embed_author":
                author_split = arg_value.split(',')
                author_dict = {
                    "name": author_split[0].strip(),
                    "url": author_split[1].strip(),
                    "icon_url": author_split[2].strip()
                }
                embed_dict["author"] = author_dict
            elif arg_name == "embed_field_name":
                field_dict = {"name": arg_value}
                if "fields" not in embed_dict:
                    embed_dict["fields"] = []
                embed_dict["fields"].append(field_dict)
            elif arg_name == "embed_field_value":
                field_dict = embed_dict["fields"][-1]
                field_dict["value"] = arg_value
            elif arg_name == "embed_field_inline":
                field_dict = embed_dict["fields"][-1]
                field_dict["inline"] = (arg_value.lower() == "true")

        return embed_dict


        # Create the embed message object
        embed = discord.Embed(
            title=embed_dict.get("embed_title", "No title provided"),
            description=embed_dict.get("embed_description", "No description provided"),
            url=embed_dict.get("embed_url", discord.Embed.Empty),
            timestamp=embed_dict.get("embed_timestamp", discord.Embed.Empty),
            color=int(embed_dict.get("embed_color", "0xffffff"), 16)
        )

        # Set the footer
        if "embed_footer" in embed_dict:
            embed.set_footer(text=embed_dict["embed_footer"], icon_url=embed_dict.get("embed_footer_icon", discord.Embed.Empty))

        # Set the image
        if "embed_image" in embed_dict:
            embed.set_image(url=embed_dict["embed_image"])

        # Set the thumbnail
        if "embed_thumbnail" in embed_dict:
            embed.set_thumbnail(url=embed_dict["embed_thumbnail"])

        # Set the author
        if "embed_author" in embed_dict:
            embed.set_author(name=embed_dict["embed_author"], url=embed_dict.get("embed_author_url", discord.Embed.Empty), icon_url=embed_dict.get("embed_author_icon", discord.Embed.Empty))

        # Set the fields
        if "embed_fields" in embed_dict:
            fields = embed_dict["embed_fields"].split(';')
            for field in fields:
                split_field = field.split(',')
                name = split_field[0]
                value = split_field[1]
                inline = True if split_field[2] == "True" else False
                embed.add_field(name=name, value=value, inline=inline)

        return embed_dict


    # +------------------------------------------------------------+
    # |                       GEN EMBED                            |
    # +------------------------------------------------------------+
    @commands.command(description='Send an Embed to another Channel', no_pm=True)
    async def gembed(self, ctx, channel: discord.TextChannel, message: discord.Message = None):
        ma = ctx.message.author.display_name
        if not channel:
            try:
                channel_id = int(channel_name)
                channel = ctx.guild.get_channel(channel_id)
            except ValueError:
                pass
            if not channel:
                return await ctx.send(f'To what channel should I send a message {ma}?')

        if message is None:
            return await ctx.send('To send a message to a channel, tell me which channel first')
        if not channel.permissions_for(ctx.me).send_messages:
            return await ctx.send('I do not have permission to send messages in that channel.')
        if not channel.permissions_for(ctx.me).attach_files:
            return await ctx.send('I do not have permission to attach files in that channel.')

        embed_dict = await self.parse_embed_message(message)
        try:
            embed = discord.Embed(title=embed_dict['title'], description=embed_dict['description'])
            for field in embed_dict['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])
            embed.set_footer(text=embed_dict['footer'])
            embed.set_thumbnail(url=embed_dict['thumbnail'])
            if embed_dict['avatar_url']:
                embed.set_author(name=ma, icon_url=embed_dict['avatar_url'])
            await channel.send(embed=embed)
            await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            return await ctx.send(f'Success {ma}!')
        except Exception as e:
            await ctx.send(f'```py\n{e}```')

    # +------------------------------------------------------------+
    # |                        HACKBAN                             |
    # +------------------------------------------------------------+
    @commands.command(description='Ban using ID if they are no longer in server', no_pm=True)
    async def hackban(self, ctx, userid, *, reason=None):
        """ Ban someone using ID """
        if ctx.author.id not in dev_list:
            return

        try:    userid = int(userid)
        except:    await ctx.send('Invalid ID!', delete_after=3)

        try:    await ctx.guild.ban(discord.Object(userid), reason=reason)
        except:   success = False
        else:    success = True

        if success:
            async for entry in ctx.guild.audit_logs(limit=1, user=ctx.guild.me, action=discord.AuditLogAction.ban):
                emb = await self.format_mod_embed(ctx, entry.target, success, 'hackban')
        else:    emb = await self.format_mod_embed(ctx, userid, success, 'hackban')
        try:    return await ctx.send(embed=emb)
        except discord.HTTPException as e:
            if ctx.author.id == 323578534763298816:    return await ctx.error(f'​`​`​`py\n{e}​`​`​`')
            else:    pass

    '''
    # +------------------------------------------------------------+
    # |                ADD/REMOVE ROLE GROUP                       |
    # +------------------------------------------------------------+
    @commands.group(description='Give or remove roles',  invoke_without_command=True)
    async def role(self, ctx: str = None):
        """ Add or Remove a role for any member """
        msg = f'Command for Mods to give or remove roles for others.\n\nrole add @name RoleName\nrole remove @name RoleName'
        return await ctx.send(msg, delete_after=23)

    # +------------------------------------------------------------+
    # |                        ADD ROLE                            |
    # +------------------------------------------------------------+
    @role.command(no_pm=True)
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    async def add(self, ctx, member: discord.Member, *, rolename: str = None):
        """ Add a role to someone else
        
        Usage:
        {prefix}role add @name Listener
        """
        if not member and rolename is None:
            return await ctx.send('To **whom** do I add **which** role? ╰(⇀ᗣ↼‶)╯', delete_after=23)

        if rolename is not None:
            role = discord.utils.find(lambda m: rolename.lower() in m.name.lower(), ctx.message.guild.roles)
            if not role:
                return await ctx.send(f'That role `{rolename}` does not exist. ╰(⇀ᗣ↼‶)╯', delete_after=23)

            try:
                await member.add_roles(role)
                await ctx.message.delete()
                await ctx.send(f'Added: **`{role.name}`** role to *{member.display_name}*')
            except:
                await ctx.send("I don't have the perms to add that role. ╰(⇀ᗣ↼‶)╯", delete_after=23)

        else:
            return await ctx.send('Please mention the member and role you want me to give them. ╰(⇀ᗣ↼‶)╯', delete_after=23)

    # +------------------------------------------------------------+
    # |                     REMOVE ROLE                            |
    # +------------------------------------------------------------+
    @role.command(no_pm=True)
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    async def remove(self, ctx, member: discord.Member, *, rolename: str):
        """ Remove a role from someone else
        
        Usage:
        {prefix}role remove @name Listener
        """
        role = discord.utils.find(lambda m: rolename.lower() in m.name.lower(), ctx.message.guild.roles)
        if not role:
            return await ctx.send(f'That role `{rolename}` does not exist. ╰(⇀ᗣ↼‶)╯', delete_after=23)

        try:
            await member.remove_roles(role)
            await ctx.message.delete()
            await ctx.send(f'Removed: `{role.name}` role from *{member.display_name}*')
        except:
            await ctx.send("I don't have the perms to remove that role. ╰(⇀ᗣ↼‶)╯", delete_after=23)

    '''
    # +------------------------------------------------------------+
    # |                     NAME                                   |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True, hidden=True)
    async def name(self, ctx, text: str = None):
        """ Change Bot's name """
        if ctx.author.id not in dev_list:    return

        if text is None:    return await ctx.send("What's my new name going to be?")

        if text is not None:
            try:
                await ctx.bot.edit_profile(username=str(text[6:]))
                await ctx.send(f'Thanks for renaming me: {text}')
                await ctx.message.delete()
            except Exception as e:
                await ctx.send(f'Failed to change my name!\n```{e}```')
                pass

    # +------------------------------------------------------------+
    # |                       LOGO                                 |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True, hidden=True)
    async def logo(self, ctx, link: str = None):
        """ Change Bot's avatar img """
        if ctx.author.id not in dev_list:    return

        if link is None:    return await ctx.send('You need to use an image URL as a link.')

        else:
            try:
                # with urllib.request.urlopen(link) as response:
                    #img = response.read()
                    #await ctx.bot.edit_profile(avatar=img)
                async with bot.session.get(link) as r:
                    img = await r.read()
                    await bot.user.edit(avatar=img)
                    return await ctx.send('New logo added successfully!')
                    
            except Exception as e:
                return await ctx.send(f'Failed to update logo image!\n```{e}```')

    # +------------------------------------------------------------+
    # |                     SAUCE                                  |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def sauce(self, ctx, *, command: str = None):
        """ Show source code for any command """
        if ctx.author.id not in dev_list:    return

        if command is not None:
            i = str(inspect2.getsource(self.bot.get_command(command).callback))

            if len(i) < 1980:
                source_full = i.replace('```', '`\u200b`\u200b`')
                await ctx.send('```py\n' + source_full + '```')

            if len(i) > 1981:
                source_trim = i.replace('```', '`\u200b`\u200b`')[:1980]
                await ctx.send('```py\n' + source_trim + '```')

        else:    await ctx.send(f"Tell me what cmd's source code you want to see.")

    # +------------------------------------------------------------+
    # |                          SAY                               |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def say(self, ctx, *, msg=''):
        """ Bot sends message """
        if f'{ctx.prefix}{ctx.invoked_with}' in msg:
            return await ctx.send("Don't ya dare spam. ( ᗒᗣᗕ)", delete_after=23)

        if not msg:    return await ctx.send('Nice try. (｡◝‿◜｡)', delete_after=23)

        else:
            msg = ctx.message.content
            said = ' '.join(msg.split("say ")[1:])
            await ctx.send(said)  # Now it works!

    # +------------------------------------------------------------+
    # |                     SAY DELET                              |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def sayd(self, ctx, *, msg=''):
        """ Sends message and delete original """
        if f'{ctx.prefix}{ctx.invoked_with}' in msg:
            return await ctx.send("Don't ya dare spam. ( ᗒᗣᗕ)", delete_after=23)

        if not msg:
            return await ctx.send('Nice try. (｡◝‿◜｡)')

        else:
            msg = ctx.message.content
            said = ' '.join(msg.split("sayd ")[1:])

            try:    await ctx.message.delete()
            except discord.Forbidden:    pass
            finally:    return await ctx.send(said)  # Now it works!

    # +------------------------------------------------------------+
    # |                      GEN                                   |
    # +------------------------------------------------------------+
    @commands.command(aliases=['general'], no_pm=True)
    async def g(self, ctx, channel: discord.TextChannel, *, message: str = None):
        """ Send a msg to another channel """
        ma = ctx.message.author.display_name
        if not channel:
            return await ctx.send(f'To what channel should I send a message {ma}?')

        if message is None:
            return await ctx.send('To send a message to a channel, tell me which channel first')

        attachments = ctx.message.attachments
        if not attachments:
            await channel.send(content=message)
            await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            return await ctx.channel.send(f'Success {ma}!')

        for attachment in attachments:
            if not any(attachment.filename.lower().endswith(ext) for ext in self.allowed_file_types):
                return await ctx.send(f"Sorry {ma}, I cannot upload files of this type. Allowed file types are: {', '.join(self.allowed_file_types)}")

            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        return await ctx.send(f"Sorry {ma}, I could not download the attachment {attachment.filename}")

                    file_content = await resp.read()

            file = discord.File(io.BytesIO(file_content), filename=attachment.filename)
            await channel.send(content=message, file=file)
            await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            return await ctx.channel.send(f'Success {ma}!')

    # +------------------------------------------------------------+
    # |                       PURGE                                |
    # +------------------------------------------------------------+
    @commands.command(aliases=['del', 'p', 'prune'], bulk=True, no_pm=True)
    async def purge(self, ctx, limit: int):
        """ Delete a number of messages """
        if ctx.author.id not in dev_list:    return

        else:
            try:
                if not limit:
                    return await ctx.send('Enter the number of messages you want me to delete.', delete_after=23)

                if limit < 99:
                    await ctx.message.delete()
                    deleted = await ctx.channel.purge(limit=limit)
                    succ = f'₍₍◝(°꒳°)◜₎₎ Successfully deleted {len(deleted)} message(s)'
                    await ctx.channel.send(succ, delete_after=9)

                else:    await ctx.send(f'Cannot delete `{limit}`, try less than 100.', delete_after=23)
                 
            except discord.Forbidden:    pass


async def setup(bot):
    await bot.add_cog(Misc(bot))
