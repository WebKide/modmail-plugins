"""
MIT License
Copyright (c) 2020-2026 WebKide [d.id @323578534763298816]
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

import asyncio
import inspect2
import io
import random
import textwrap
import traceback

import aiohttp
import discord
from aiohttp import ClientSession, ClientResponseError
from discord import File
from discord.ext import commands

dev_list = [1094090021914554510, 323578534763298816, 1437031434723397662, 354780332081414154]


class Misc(commands.Cog):
    """Useful commands to make your life easier v2.0
    - Only works with Admin perms, and a few commands require dev_list to be modified if you wish to use
    - This cog was made to keep a few commands that are no longer common, but are useful to run a server
    """
    def __init__(self, bot):
        self.bot = bot
        self.mod_color = discord.Colour(0x7289da)  # Blurple
        self.user_color = discord.Colour(0xed791d)  # Orange
        self.IMGUR_THUMBNAIL_KICK = "https://i.imgur.com/BjhBoyc.png"
        self.IMGUR_THUMBNAIL_BAN = "https://i.imgur.com/1tqFp0N.png"
        self.IMGUR_THUMBNAIL_HACKBAN = "https://i.imgur.com/85qlkKU.png"
        self.allowed_file_types = ['.png', '.jpg', '.jpeg', '.pdf', '.doc', '.docx', '.txt', '.gif', '.mp3']
        self._internal_session = None

    async def cog_unload(self):
        """Cleanup session on cog unload if internal session was created"""
        if self._internal_session:
            await self._internal_session.close()

    async def _get_session(self):
        """Safely fetch bot HTTP session or provision an internal fallback"""
        if hasattr(self.bot, 'session') and isinstance(self.bot.session, aiohttp.ClientSession):
            return self.bot.session
        if not self._internal_session or self._internal_session.closed:
            self._internal_session = aiohttp.ClientSession()
        return self._internal_session

    async def format_mod_embed(self, ctx, user, success, method):
        """ Helper func to format an embed to prevent extra code """
        emb = discord.Embed()
        emb.colour = self.mod_color

        # Handle both Member objects and raw user IDs
        user_id = getattr(user, "id", user)
        emb.set_footer(text=f'User ID: {user_id}')

        if isinstance(user, int):
            emb.set_author(name=method.title())
            user_display = f"User with ID `{user}`"
        else:
            emb.set_author(name=method.title(), icon_url=user.display_avatar.url)
            user_display = f"**{user}**"

        # Handle past tense properly
        past_tense = {
            'kick': 'kicked',
            'ban': 'banned',
            'hackban': 'hackbanned'
        }

        if success:
            emb.description = f'{user_display} was successfully {past_tense.get(method, method+"ed")}.'
        else:
            # Dynamically state why the action failed rather than guessing it was permission-based
            reason = error_msg or "Internal API Exception or missing Bot Permissions."
            emb.description = f"❌ Failed to {method} {user_display}.\n**Reason:** {reason}"
            emb.colour = discord.Colour.red() # Shift to red on failure states

        return emb


    # +------------------------------------------------------------+
    # |                     CLEAR BOT DMs                          |
    # +------------------------------------------------------------+
    @commands.command(description='WARNING! advanced command', name='clear_bot_dms')
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
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
            await ctx.channel.typing()
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
    # |             MANAGE GUILD COMMANDS GROUP                    |
    # +------------------------------------------------------------+
    @commands.group(description='Kick, Ban or Hackban', invoke_without_command=True)
    @commands.guild_only()
    async def manageguild(self, ctx):
        """ Kick, Ban or Hackban users with command + Reason """
        msg = f'Command for Admins and Mods to Kick, Ban or Hackban user with ID or @nametag + Reason.'
        await ctx.send(msg, delete_after=23)

    # +------------------------------------------------------------+
    # |                        KICK                                |
    # +------------------------------------------------------------+
    @manageguild.command()
    @commands.guild_only()
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """ Kick a member from the server """
        reason = reason or "No reason provided"
        error_msg = None

        try:
            await member.kick(reason=reason)
            success = True
        except discord.Forbidden:
            success = False
            error_msg = "The bot lacks permissions or the user holds a higher role hierarchy."
        except discord.HTTPException:
            success = False
            error_msg = "Network connection issues with Discord API."

        # Format embed using the helper function
        emb = await self.format_mod_embed(ctx, member, success, 'kick', error_msg)
        emb.set_thumbnail(url=self.IMGUR_THUMBNAIL_KICK)

        try:
            await ctx.send(embed=emb)
        except discord.HTTPException as e:
            if ctx.author.id in DEV_LIST:
                await ctx.send(f'```py\n{e}```', delete_after=120)

    # +------------------------------------------------------------+
    # |                        BAN                                 |
    # +------------------------------------------------------------+
    @manageguild.command()
    @commands.guild_only()
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """ Ban a member from the server """
        reason = reason or "No reason provided"
        error_msg = None

        try:
            await member.ban(reason=reason)
            success = True
        except discord.Forbidden:
            success = False
            error_msg = "The bot lacks permissions or the user holds a higher role hierarchy."
        except discord.HTTPException:
            success = False
            error_msg = "Network connection issues with Discord API."

        emb = await self.format_mod_embed(ctx, member, success, 'ban', error_msg)
        emb.set_thumbnail(url=self.IMGUR_THUMBNAIL_BAN)

        try:
            await ctx.send(embed=emb)
        except discord.HTTPException as e:
            if ctx.author.id in DEV_LIST:
                await ctx.send(f'```py\n{e}```', delete_after=120)

    # +------------------------------------------------------------+
    # |                        HACKBAN                             |
    # +------------------------------------------------------------+
    @manageguild.command(description='Ban using ID if they are no longer in server')
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def hackban(self, ctx, userid: int, *, reason: str = None):
        """ Ban someone using ID """
        if ctx.author.id not in dev_list:
            return

        reason = reason or "No reason provided"
        error_msg = None

        try:
            await ctx.guild.ban(user=discord.Object(id=userid), reason=reason)
            success = True
        except discord.Forbidden:
            success = False
            error_msg = "The bot does not have Ban permissions."
        except discord.HTTPException:
            success = False
            error_msg = "Invalid User ID or API network failure."

        emb = None
        if success:
            try:
                async for entry in ctx.guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                    if entry.target and entry.target.id == userid:
                        emb = await self.format_mod_embed(ctx, entry.target, success, 'hackban')
                        break

            except discord.Forbidden:
                # Bot can ban, but might lack separate view_audit_log permissions
                pass

            if not emb:
                emb = await self.format_mod_embed(ctx, userid, success, 'hackban')
        else:
            emb = await self.format_mod_embed(ctx, userid, success, 'hackban')

        emb.set_thumbnail(url=self.IMGUR_THUMBNAIL_HACKBAN)

        try:
            await ctx.send(embed=emb)
        except discord.HTTPException as e:
            if ctx.author.id == 1094090021914554510:
                await ctx.send(f'```py\n{e}```', delete_after=120)

    # +------------------------------------------------------------+
    # |                ADD/REMOVE ROLE GROUP                       |
    # +------------------------------------------------------------+
    @commands.group(description='Give or remove roles', invoke_without_command=True)
    @commands.guild_only()
    async def guildrole(self, ctx): # FIX: Removed string type hint
        """ Add or Remove a role for any member """
        msg = (
            'Command for Mods to give or remove roles for others.\n\n'
            '`guildrole add @name RoleName`\n'
            '`guildrole remove @name RoleName`'
        )
        await ctx.send(msg, delete_after=23)

    # +------------------------------------------------------------+
    # |                        ADD ROLE                            |
    # +------------------------------------------------------------+
    @guildrole.command(name="add")
    @commands.guild_only()
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.bot_has_permissions(manage_roles=True) # FIX: Proactively checks bot perms
    async def add_role(self, ctx, member: discord.Member, *, rolename: str = None):
        """ Add a role to someone else """
        if not rolename: # FIX: Clean handling of missing role name string
            return await ctx.send('Please specify the role you want me to give them. ╰(⇀ᗣ↼‶)╯', delete_after=23)

        # Optimization: case-insensitive search through guild roles
        role = discord.utils.find(lambda r: rolename.lower() in r.name.lower(), ctx.guild.roles)

        if not role:
            return await ctx.send(f'That role `{rolename}` does not exist. ╰(⇀ᗣ↼‶)╯', delete_after=23)

        try:
            await member.add_roles(role)

            # Clean up the invoking message if possible
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass # Fail silently if bot lacks 'Manage Messages' permission

            await ctx.send(f'Added: **`{role.name}`** role to *{member.display_name}*')

        except discord.Forbidden: # FIX: Target role hierarchy check
            await ctx.send("I don’t have the perms to add that role (it might be higher than my own role hierarchy). ╰(⇀ᗣ↼‶)╯", delete_after=23)
        except discord.HTTPException:
            await ctx.send("Failed to update roles due to a Discord API error.", delete_after=23)

    # +------------------------------------------------------------+
    # |                     REMOVE ROLE                            |
    # +------------------------------------------------------------+
    @guildrole.command(name="remove")
    @commands.guild_only()
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.bot_has_permissions(manage_roles=True) # FIX: Proactively checks bot perms
    async def remove_role(self, ctx, member: discord.Member, *, rolename: str):
        """ Remove a role from someone else """
        role = discord.utils.find(lambda r: rolename.lower() in r.name.lower(), ctx.guild.roles)

        if not role:
            return await ctx.send(f'That role `{rolename}` does not exist. ╰(⇀ᗣ↼‶)╯', delete_after=23)

        try:
            await member.remove_roles(role)

            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            await ctx.send(f'Removed: `{role.name}` role from *{member.display_name}*')

        except discord.Forbidden: # FIX: Target role hierarchy check
            await ctx.send("I don’t have the perms to remove that role (it might be higher than my own role hierarchy). ╰(⇀ᗣ↼‶)╯", delete_after=23)
        except discord.HTTPException:
            await ctx.send("Failed to update roles due to a Discord API error.", delete_after=23)

    # +------------------------------------------------------------+
    # |                     NAME                                   |
    # +------------------------------------------------------------+
    @commands.command(description='Use only to rename the bot from a text-channel')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def botname(self, ctx, *, text: str = None):
        """ Change Bot’s name """
        if ctx.author.id not in dev_list:
            return

        if text is None:
            return await ctx.send("What’s my new name going to be?", delete_after=35)

        try:
            async with ctx.channel.typing():
                await asyncio.sleep(6) 
                await self.bot.user.edit(username=text)
                await ctx.send(f'✅ Thanks for renaming me: **{text}**')
                try:
                    await ctx.message.delete()
                except discord.Forbidden:
                    pass
        except discord.HTTPException as e:
            # Catching explicit Discord rate limits (Max 2 name changes per hour)
            if e.status == 429:
                await ctx.send("❌ Failed! Discord is rate-limiting username changes. Try again in an hour.", delete_after=23)
            else:
                await ctx.send(f'❌ Failed to change my name!\n```py\n{e}```', delete_after=23)

    # +------------------------------------------------------------+
    # |                       LOGO                                 |
    # +------------------------------------------------------------+
    @commands.command(description='Change the bot’s avatar')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def botlogo(self, ctx, link: str = None):
        """ Change the Bot’s avatar (admins only) """
        if ctx.author.id not in dev_list:
            return await ctx.send("❌ You don't have permission to use this command.", delete_after=23)

        if not link:
            return await ctx.send("❌ Please provide a direct image URL (e.g., `https://i.imgur.com/abc123.png`)", delete_after=23)

        # Ensure it's a direct image URL (not an Imgur page)
        if "imgur.com" in link and not link.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            link = f"https://i.imgur.com/{link.split('/')[-1]}.png"  # Convert to direct URL

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            async with ctx.channel.typing():
                session = await self._get_session()

                for attempt in range(3):
                    try:
                        async with session.get(link, headers=headers) as response:
                            if response.status == 429:
                                retry_after = int(response.headers.get('Retry-After', 5))
                                await ctx.send(f"⚠️ External host rate-limited. Retrying in {retry_after}s...", delete_after=10)
                                await asyncio.sleep(retry_after)
                                continue

                            if response.status != 200:
                                return await ctx.send(f"❌ Failed to download image (HTTP {response.status})", delete_after=23)

                            content_type = response.headers.get('Content-Type', '').lower()
                            if not content_type.startswith('image/'):
                                return await ctx.send(f"❌ URL does not point to a valid image profile.", delete_after=23)

                            image_data = await response.read()

                            if len(image_data) > 10 * 1024 * 1024:
                                return await ctx.send("❌ Image size exceeds maximum limit of 10MB.", delete_after=23)

                            # Push update to Discord
                            await self.bot.user.edit(avatar=image_data)
                            return await ctx.send("✅ Avatar updated successfully!")

                    except aiohttp.ClientResponseError:
                        if attempt < 2:
                            await asyncio.sleep(3)
                            continue
                        raise

        except discord.HTTPException as e:
            if e.status == 429:
                await ctx.send("❌ Discord API rate-limit hit. You are changing avatars too fast!", delete_after=23)
            else:
                await ctx.send(f"❌ Discord API error: `{e.text}`", delete_after=23)
        except Exception as e:
            await ctx.send(f"❌ Failed to update avatar: `{str(e)}`", delete_after=23)
            traceback.print_exc()

    # +------------------------------------------------------------+
    # |                     SAUCE                                  |
    # +------------------------------------------------------------+
    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def sauce(self, ctx, *, command: str = None):
        """ Show source code for any command """
        try:
            await ctx.message.delete()
            await ctx.channel.typing()
        except discord.Forbidden:
            pass

        if command is not None:
            i = str(inspect2.getsource(self.bot.get_command(command).callback))

            if len(i) < 1980:
                source_full = i.replace('```', '`\u200b`\u200b`')
                await ctx.send('```py\n' + source_full + '```', delete_after=64)

            if len(i) > 1981:
                source_trim = i.replace('```', '`\u200b`\u200b`')[:1980]
                await ctx.send('```py\n' + source_trim + '```', delete_after=64)

        else:
            await ctx.send(f"Tell me what cmd's source code you want to see.", delete_after=23)

    # +------------------------------------------------------------+
    # |                          SAY                               |
    # +------------------------------------------------------------+
    @commands.command()
    @commands.guild_only()
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
    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def sayd(self, ctx, *, msg=''):
        """ Bot sends message and deletes original """
        if f'{ctx.prefix}{ctx.invoked_with}' in msg:
            return await ctx.send("Don’t ya dare spam. ( ᗒᗣᗕ)", delete_after=23)

        if not msg:
            return await ctx.send('Nice try. (｡◝‿◜｡)')

        else:
            await ctx.channel.typing()
            await asyncio.sleep(random.randint(3, 11))
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
    @commands.command(aliases=['general'])
    @commands.guild_only()
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
    @commands.command(aliases=['del', 'p', 'prune'], bulk=True)
    @commands.guild_only()
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
