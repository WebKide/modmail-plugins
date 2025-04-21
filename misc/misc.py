"""
MIT License
Copyright (c) 2020-2025 WebKide [d.id @323578534763298816]
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

import asyncio, io, random, textwrap, traceback, inspect2

import aiohttp, discord
from discord import File
from discord.ext import commands

dev_list = [1094090021914554510, 323578534763298816]


class Misc(commands.Cog):
    """Useful commands to make your life easier
    - Only works with Admin perms, and a few commands require dev_list to be modified if you wish to use
    - This cog was made to keep a few commands that are no longer common but are useful to run a server
    """
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


    # +------------------------------------------------------------+
    # |                     CLEAR BOT DMs                          |
    # +------------------------------------------------------------+
    @commands.command(description='WARNING! advanced command', name='clear_bot_dms', no_pm=True)
    async def _clear_bot_dms(self, ctx, limit: int):
        """WARNING!! Deletes the bot’s own messages in your DMs
        - Can be invoked from any text-channel. Limit applies to checked messages.
        """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if limit <= 0:
            return await ctx.send('Please provide a positive number of messages to check: between 1 and 99.', delete_after=6)

        # Add a reasonable upper limit to prevent excessive API calls/time
        if limit > 100:
             await ctx.send('Checking up to 100 messages in DMs.', delete_after=15)
             limit = 100

        # Get the DM channel with the user who invoked the command
        try:
            # Use existing DM channel or create one if it doesn’t exist
            dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
        except discord.Forbidden:
             # This can happen if the user has DMs disabled for non-friends/server members
             return await ctx.send("I can’t create or access a DM channel with you. Please check your privacy settings.", delete_after=23)
        except discord.HTTPException as e:
             return await ctx.send(f"Failed to get DM channel due to an API error:\n{e}", delete_after=40)

        feedback_msg = await ctx.send(f"Attempting to delete my last {limit} applicable messages in my DM with you...", delete_after=10)

        deleted_count = 0
        checked_count = 0
        try:
            # Fetch message history from the DM channel
            async for message in dm_channel.history(limit=limit):
                checked_count += 1
                # Check if the message was sent by the bot
                if message.author.id == self.bot.user.id:
                    try:
                        await message.delete()
                        deleted_count += 1
                        # Avoid hitting rate limits
                        await asyncio.sleep(random.randint(2, 11))
                    except discord.Forbidden:
                        print(f"Permission error deleting message {message.id} in DM with {ctx.author.id}")
                        # Stop if permission is denied for one, likely denied for all in the DM
                        await dm_channel.send("Stopped deleting: I lack permissions to delete my messages in this DM.", delete_after=15)
                        break
                    except discord.NotFound:
                        # Message was already deleted somehow, ignore
                        pass
                    except discord.HTTPException as e:
                        print(f"HTTP error deleting message {message.id}: {e}")
                        # Handle potential rate limits (status code 429)
                        if e.status == 429:
                            await dm_channel.send("Rate limited. Please wait before trying again.", delete_after=15)
                            await asyncio.sleep(random.randint(5, 11))
                        # Stop on other HTTP errors
                        else:
                             await dm_channel.send(f"An API error occurred while deleting:\n{e}", delete_after=15)
                             break

            # Send confirmation to the DM channel
            await dm_channel.send(f'Successfully deleted {deleted_count} of my messages in your DMs (checked last {checked_count} messages).', delete_after=60)

            # Optionally try to delete the initial feedback message
            try:
                await feedback_msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        except discord.Forbidden:
            # This might happen if the bot cannot read history in the DM (unlikely but possible)
             await ctx.send("I don’t have permission to read message history in our DM.", delete_after=23)
        except discord.HTTPException as e:
             await ctx.send(f"An API error occurred while fetching history:\n{e}", delete_after=23)

    # +------------------------------------------------------------+
    # |                        HACKBAN                             |
    # +------------------------------------------------------------+
    @commands.command(description='Ban using ID if they are no longer in server', no_pm=True)
    @commands.has_permissions(administrator=True)
    async def hackban(self, ctx, userid, *, reason=None):
        """ Ban someone using ID """
        if ctx.author.id not in dev_list:
            return

        try:
            userid = int(userid)
        except:
            await ctx.send('Invalid ID!', delete_after=3)

        try:
            await ctx.guild.ban(discord.Object(userid), reason=reason)
        except:
            success = False
        else:
            success = True

        if success:
            async for entry in ctx.guild.audit_logs(limit=1, user=ctx.guild.me, action=discord.AuditLogAction.ban):
                emb = await self.format_mod_embed(ctx, entry.target, success, 'hackban')
        else:
            emb = await self.format_mod_embed(ctx, userid, success, 'hackban')
        try:
            return await ctx.send(embed=emb)
        except discord.HTTPException as e:
            if ctx.author.id == 323578534763298816:    return await ctx.error(f'​`​`​`py\n{e}​`​`​`')
            else:
                pass

    # +------------------------------------------------------------+
    # |                ADD/REMOVE ROLE GROUP                       |
    # +------------------------------------------------------------+
    @commands.group(description='Give or remove roles',  invoke_without_command=True)
    async def guildrole(self, ctx: str = None):
        """ Add or Remove a role for any member """
        msg = f'Command for Mods to give or remove roles for others.\n\nguildrole add @name RoleName\nguildrole remove @name RoleName'
        return await ctx.send(msg, delete_after=23)

    # +------------------------------------------------------------+
    # |                        ADD ROLE                            |
    # +------------------------------------------------------------+
    @guildrole.command(no_pm=True)
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    async def add(self, ctx, member: discord.Member, *, rolename: str = None):
        """ Add a role to someone else
        
        Usage:
        {prefix}guildrole add @name Listener
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
                await ctx.send("I don’t have the perms to add that role. ╰(⇀ᗣ↼‶)╯", delete_after=23)

        else:
            return await ctx.send('Please mention the member and role you want me to give them. ╰(⇀ᗣ↼‶)╯', delete_after=23)

    # +------------------------------------------------------------+
    # |                     REMOVE ROLE                            |
    # +------------------------------------------------------------+
    @guildrole.command(no_pm=True)
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    async def remove(self, ctx, member: discord.Member, *, rolename: str):
        """ Remove a role from someone else
        
        Usage:
        {prefix}guildrole remove @name Listener
        """
        role = discord.utils.find(lambda m: rolename.lower() in m.name.lower(), ctx.message.guild.roles)
        if not role:
            return await ctx.send(f'That role `{rolename}` does not exist. ╰(⇀ᗣ↼‶)╯', delete_after=23)

        try:
            await member.remove_roles(role)
            await ctx.message.delete()
            await ctx.send(f'Removed: `{role.name}` role from *{member.display_name}*')
        except:
            await ctx.send("I don’t have the perms to remove that role. ╰(⇀ᗣ↼‶)╯", delete_after=23)

    # +------------------------------------------------------------+
    # |                     NAME                                   |
    # +------------------------------------------------------------+
    @commands.command(description='Use only to rename the bot from a text-channel', no_pm=True)
    @commands.has_permissions(administrator=True)
    async def name(self, ctx, text: str = None):
        """ Change Bot’s name """
        if ctx.author.id not in dev_list:
            return

        if text is None:
            return await ctx.send("What’s my new name going to be?")

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
    @commands.command(description='Use to replace the AVY for the bot', no_pm=True)
    @commands.has_permissions(administrator=True)
    async def logo(self, ctx, link: str = None):
        """ Change Bot’s avatar img """
        if ctx.author.id not in dev_list:
            return await ctx.send("You don't have permission to use this command.", delete_after=23)
            
        if not link:
            return await ctx.send('Please provide an image URL.', delete_after=23)

        try:
            async with self.bot.session.get(link) as response:
                # Check if request was successful
                if response.status != 200:
                    return await ctx.send(f'Failed to download image (HTTP {response.status})', delete_after=23)

                # Check content type to ensure it's an image
                content_type = response.headers.get('Content-Type', '').lower()
                if not content_type.startswith('image/'):
                    return await ctx.send(f'URL does not point to an image (Content-Type: {content_type})', delete_after=23)

                # Read image data
                image_data = await response.read()

                # Check image size (Discord limit is 10MB for avatars)
                if len(image_data) > 10 * 1024 * 1024:
                    return await ctx.send('Image is too large (max 10MB)', delete_after=23)

                # Update avatar
                await self.bot.user.edit(avatar=image_data)
                await ctx.send('✅ Avatar updated successfully!')

        except aiohttp.ClientError as e:
            await ctx.send(f'Failed to download image: {str(e)}', delete_after=23)
        except discord.HTTPException as e:
            await ctx.send(f'Discord rejected the avatar change: {str(e)}', delete_after=23)
        except Exception as e:
            await ctx.send(f'An unexpected error occurred: {str(e)}', delete_after=23)
            traceback.print_exc()  # Print full traceback to console for debugging

    # +------------------------------------------------------------+
    # |                     SAUCE                                  |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    @commands.has_permissions(administrator=True)
    async def sauce(self, ctx, *, command: str = None):
        """ Show source code for any command """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if command is not None:
            i = str(inspect2.getsource(self.bot.get_command(command).callback))

            if len(i) < 1980:
                source_full = i.replace('```', '`\u200b`\u200b`')
                await ctx.send('```py\n' + source_full + '```')

            if len(i) > 1981:
                source_trim = i.replace('```', '`\u200b`\u200b`')[:1980]
                await ctx.send('```py\n' + source_trim + '```')

        else:
            await ctx.send(f"Tell me what cmd's source code you want to see.")

    # +------------------------------------------------------------+
    # |                          SAY                               |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    @commands.has_permissions(administrator=True)
    async def say(self, ctx, *, msg=''):
        """ Bot repeats message """
        if f'{ctx.prefix}{ctx.invoked_with}' in msg:
            return await ctx.send("Don’t ya dare spam. ( ᗒᗣᗕ)", delete_after=23)

        if not msg:
            return await ctx.send('Nice try. (｡◝‿◜｡)', delete_after=23)

        else:
            msg = ctx.message.content
            said = ' '.join(msg.split("say ")[1:])
            await ctx.send(said)  # Now it works!

    # +------------------------------------------------------------+
    # |                     SAY DELET                              |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    @commands.has_permissions(administrator=True)
    async def sayd(self, ctx, *, msg=''):
        """ Bot sends message and deletes original """
        if f'{ctx.prefix}{ctx.invoked_with}' in msg:
            return await ctx.send("Don’t ya dare spam. ( ᗒᗣᗕ)", delete_after=23)

        if not msg:
            return await ctx.send('Nice try. (｡◝‿◜｡)')

        else:
            msg = ctx.message.content
            said = ' '.join(msg.split("sayd ")[1:])

            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            finally:
                return await ctx.send(said)  # Now it works!

    # +------------------------------------------------------------+
    # |                      GEN                                   |
    # +------------------------------------------------------------+
    @commands.command(aliases=['general'], no_pm=True)
    @commands.has_permissions(administrator=True)
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
    @commands.has_permissions(administrator=True)
    async def purge(self, ctx, limit: int):
        """ Delete x number of messages in text-channel """
        try:
            if not limit:
                return await ctx.send('Enter the number of messages you want me to delete.', delete_after=23)

            if limit < 99:
                await ctx.message.delete()
                deleted = await ctx.channel.purge(limit=limit)
                succ = f'₍₍◝(°꒳°)◜₎₎ Successfully deleted {len(deleted)} message(s)'
                await ctx.channel.send(succ, delete_after=9)

            else:
                await ctx.send(f'Cannot delete `{limit}`, try less than 100.', delete_after=23)
                 
        except discord.Forbidden:
            pass


async def setup(bot):
    await bot.add_cog(Misc(bot))
