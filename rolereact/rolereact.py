"""
MIT License
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
from typing import Optional, Union, Dict, Set

import discord
from discord.ext import commands
from core import checks
from core.models import PermissionLevel

restricted_emojis = {'⭐', '🌟', '✨'}  # Emojis used by Starboard plugin

class RoleReact(commands.Cog):
    """This RoleReact plugin allows server administrators to set up reaction roles — a system where users can self-assign roles by clicking on reactions.
    It's perfect for:

    - Creating opt-in role systems
    - Letting users choose notification preferences
    - Organizing community interests
    - Managing game/server access roles
    
    **reaction role Sub Commands**
        ├─ `add` - Add a reaction role
        ├─ `blacklist` - Add/remove a user from reaction role blacklis
        ├─ `blacklist_list` - View blacklisted users with pagination
        ├─ `cleanup` - Remove all reactions from a message
        ├─ `ignore_role` - Add/remove a role that will be ignored by reaction roles
        ├─ `ignored_roles` - View ignored roles
        ├─ `list` - List all configured reaction roles
        ├─ `pause` - Pause or resume all reaction role functionality
        ├─ `react` - Add reactions to a message for reaction roles
        ├─ `remove` - Remove a reaction role
        ├─ `set_audit_channel` - Set the channel for audit logs
        └─ `set_channel` - Set the channel for reaction role messages
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.roles: Dict[str, int] = {}
        self.paused: bool = False
        self.blacklist: Set[int] = set()
        self.ignored_roles: Set[int] = set()
        self.audit_channel_id: Optional[int] = None
        self._config_ready = asyncio.Event()
        asyncio.create_task(self._set_config())

    async def _set_config(self) -> None:
        """Load configuration from database."""
        try:
            config = await self.db.find_one({"_id": "config"})
            audit_config = await self.db.find_one({"_id": "audit_channel"})
            
            if config:
                self.roles = config.get("roles", {})
                self.paused = config.get("paused", False)
                self.blacklist = set(config.get("blacklist", []))
                self.ignored_roles = set(config.get("ignored_roles", []))
            
            if audit_config:
                self.audit_channel_id = int(audit_config.get("channel_id", 0)) or None
        except Exception as e:
            print(f"Error loading config: {e}")
        finally:
            self._config_ready.set()

    async def _update_config(self) -> None:
        """Update the configuration in the database."""
        try:
            await self.db.find_one_and_update(
                {"_id": "config"},
                {"$set": {
                    "roles": self.roles,
                    "paused": self.paused,
                    "blacklist": list(self.blacklist),
                    "ignored_roles": list(self.ignored_roles)
                }},
                upsert=True
            )
        except Exception as e:
            print(f"Error updating config: {e}")

    async def wait_until_ready(self) -> None:
        """Wait until the config is loaded."""
        await self._config_ready.wait()

    @commands.group(aliases=["rr"], description="Manage reaction roles with 12 sub-commands", invoke_without_command=True)
    async def rolereaction(self, ctx: commands.Context):
        """ Manage reaction roles """
        await ctx.send_help(ctx.command)

    @rolereaction.command(description='Add reaction to a message using ID', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def add(self, ctx: commands.Context, emoji: Union[discord.Emoji, str], role: discord.Role):
        """Add a reaction role
        
        Parameters
        ----------
        emoji : Union[discord.Emoji, str]
            The emoji to use for the reaction role
        role : discord.Role
            The role to assign when the emoji is clicked
        """
        await self.wait_until_ready()

        # Check for restricted emojis
        emoji_str = str(emoji)
        if emoji_str in restricted_emojis:
            return await ctx.send(
                f"You cannot use {emoji_str} as it's reserved for other plugins.", 
                delete_after=9
            )

        # Check role hierarchy
        if role >= ctx.guild.me.top_role:
            return await ctx.send(
                "I can't assign roles higher than my highest role!", 
                delete_after=9
            )
        
        if role.managed:
            return await ctx.send(
                "This role is managed by an integration and cannot be assigned.", 
                delete_after=9
            )

        emote = emoji.name if hasattr(emoji, 'id') else str(emoji)
        
        updated = emote in self.roles
        self.roles[emote] = role.id

        await self._update_config()

        try:
            await ctx.send(
                f"Successfully {'updated' if updated else 'added'} {emoji} to point to {role.mention}",
                delete_after=15
            )
        except discord.Forbidden:
            await ctx.send("I don't have permission to send messages here.")

    @rolereaction.command(description='Remove reaction from a message using ID', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def remove(self, ctx: commands.Context, emoji: Union[discord.Emoji, str]):
        """Remove a reaction role
        
        Parameters
        ----------
        emoji : Union[discord.Emoji, str]
            The emoji to remove from reaction roles
        """
        await self.wait_until_ready()
        
        emote = emoji.name if hasattr(emoji, 'id') else str(emoji)

        if emote not in self.roles:
            return await ctx.send("This emoji is not configured for reaction roles.")

        role_id = self.roles.pop(emote)
        role = ctx.guild.get_role(role_id)

        await self._update_config()

        try:
            await ctx.send(
                f"Removed {emoji} reaction role (previously pointed to {role.mention if role else 'deleted role'})",
                delete_after=15
            )
        except discord.Forbidden:
            pass

    @rolereaction.command(description='Cleanup all reactions from a message using ID', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def cleanup(self, ctx: commands.Context, message_id: int):
        """Remove all reactions from a message
        
        Parameters
        ----------
        message_id : int
            The ID of the message to clean up
        """
        config = await self.db.find_one({"_id": "config"})
        if not config or "channel" not in config:
            return await ctx.send("No reaction role channel has been set!", delete_after=9)

        try:
            channel = self.bot.get_channel(int(config["channel"]))
            if not channel:
                return await ctx.send("Channel not found!", delete_after=9)

            message = await channel.fetch_message(message_id)
            await message.clear_reactions()
            await ctx.send("✅ All reactions have been removed from the message.", delete_after=9)
        except discord.NotFound:
            await ctx.send("Message not found!", delete_after=9)
        except discord.Forbidden:
            await ctx.send("I don't have permissions to manage reactions in that channel!", delete_after=9)
        except Exception as e:
            await ctx.send(f"An error occurred:\n{e}")

    @rolereaction.command(description='View the reaction roles', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def list(self, ctx: commands.Context):
        """List all configured reaction roles"""
        await self.wait_until_ready()
        
        if not self.roles:
            return await ctx.send("No reaction roles have been configured yet.", delete_after=9)

        embed = discord.Embed(title="Configured Reaction Roles", color=discord.Color.blue())
        
        for emoji_str, role_id in self.roles.items():
            role = ctx.guild.get_role(role_id)
            emoji = self.bot.get_emoji(int(emoji_str)) if emoji_str.isdigit() else emoji_str
            
            embed.add_field(
                name=str(emoji),
                value=f"Role: {role.mention if role else 'Deleted Role'} (ID: {role_id})",
                inline=False
            )

        await ctx.send(embed=embed)

    @rolereaction.command(aliases=["sc"], description="Run this command second", no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def set_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for reaction role messages
        
        Parameters
        ----------
        channel : discord.TextChannel
            The channel to use for reaction role messages
        """
        try:
            await self.db.find_one_and_update(
                {"_id": "config"}, 
                {"$set": {"channel": str(channel.id)}}, 
                upsert=True
            )
            await ctx.send(
                f"Reaction role channel has been set to {channel.mention}", 
                delete_after=30
            )
        except Exception as e:
            await ctx.send(f"Failed to set channel: {e}")

    @rolereaction.command(description='Start adding reactions to the message, third', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def react(self, ctx: commands.Context, message_id: int):
        """Add reactions to a message for reaction roles
        
        Parameters
        ----------
        message_id : int
            The ID of the message to add reactions to
        """
        await self.wait_until_ready()
        
        config = await self.db.find_one({"_id": "config"})
        if not config or "channel" not in config:
            return await ctx.send("No reaction role channel has been set!", delete_after=9)

        try:
            channel = self.bot.get_channel(int(config["channel"]))
            if not channel:
                return await ctx.send("Reaction role channel not found!", delete_after=9)

            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                return await ctx.send("Message not found!", delete_after=9)
            except discord.Forbidden:
                return await ctx.send("I don't have permission to read that channel!", delete_after=9)

            for emoji_str in self.roles:
                try:
                    if emoji_str.isdigit():
                        emoji = self.bot.get_emoji(int(emoji_str))
                        if not emoji:
                            continue
                    else:
                        emoji = emoji_str
                    await message.add_reaction(emoji)
                except discord.HTTPException:
                    continue

            await ctx.send("Added all reaction role emojis to the message!", delete_after=9)
        except Exception as e:
            await ctx.send(f"An error occurred:\n{e}")

    @rolereaction.command(description='Toggle if the plugin is active or paused', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def pause(self, ctx: commands.Context):
        """Pause or resume all reaction role functionality"""
        self.paused = not self.paused
        await self._update_config()
        status = "paused" if self.paused else "resumed"
        await ctx.send(f"Reaction roles have been {status}.", delete_after=9)

    @rolereaction.command(description='When a user will not listen', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def blacklist(self, ctx: commands.Context, user: discord.Member):
        """Add/remove a user from reaction role blacklist
        
        Parameters
        ----------
        user : discord.Member
            The user to add/remove from the blacklist
        """
        if user.id in self.blacklist:
            self.blacklist.remove(user.id)
            action = "removed from"
        else:
            self.blacklist.add(user.id)
            action = "added to"
        await self._update_config()
        await ctx.send(f"{user.mention} has been {action} the blacklist.")

    @rolereaction.command(description='Prevent any role from using this feature', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def ignore_role(self, ctx: commands.Context, role: discord.Role):
        """Add/remove a role that will be ignored by reaction roles
        
        Parameters
        ----------
        role : discord.Role
            The role to add/remove from the ignored roles list
        """
        if role.id in self.ignored_roles:
            self.ignored_roles.remove(role.id)
            action = "removed from"
        else:
            self.ignored_roles.add(role.id)
            action = "added to"
        await self._update_config()
        await ctx.send(f"{role.mention} has been {action} the ignored roles list.")

    @rolereaction.command(name="blacklist_list", description="Check who is blacklisted", no_pm=True)
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def blacklist_list(self, ctx: commands.Context):
        """View blacklisted users with pagination"""
        await self.wait_until_ready()
        
        if not self.blacklist:
            return await ctx.send("No users are currently blacklisted.", delete_after=9)

        # Convert user IDs to members
        members = []
        for user_id in self.blacklist:
            member = ctx.guild.get_member(user_id)
            if member:
                members.append(member)
            else:
                # If member not found, try to fetch or show ID
                try:
                    member = await ctx.guild.fetch_member(user_id)
                    members.append(member)
                except discord.NotFound:
                    members.append(f"Unknown User ({user_id})")

        # Split into chunks of 10 for pagination
        chunks = [members[i:i + 10] for i in range(0, len(members), 10)]
        pages = []
        
        for i, chunk in enumerate(chunks, 1):
            embed = discord.Embed(
                title=f"Blacklisted Users (Page {i}/{len(chunks)})",
                color=discord.Color.red()
            )
            
            for member in chunk:
                if isinstance(member, discord.Member):
                    value = f"Joined: {member.joined_at.strftime('%Y-%m-%d')}\nRoles: {len(member.roles)-1}"
                    embed.add_field(
                        name=str(member),
                        value=value,
                        inline=True
                    )
                else:
                    embed.add_field(
                        name=member,
                        value="*User not found in server*",
                        inline=True
                    )
            
            embed.set_footer(text=f"Total blacklisted: {len(members)}")
            pages.append(embed)

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        
        # Set up pagination
        message = await ctx.send(embed=pages[0])
        if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            return await ctx.send("I need 'Manage Messages' permission for pagination!")

        for emoji in ("⬅️", "➡️", "❌"):
            await message.add_reaction(emoji)

        def check(reaction: discord.Reaction, user: discord.User):
            return user == ctx.author and str(reaction.emoji) in ("⬅️", "➡️", "❌")

        current_page = 0
        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", 
                    timeout=60.0, 
                    check=check
                )
                
                if str(reaction.emoji) == "➡️":
                    current_page = min(current_page + 1, len(pages) - 1)
                elif str(reaction.emoji) == "⬅️":
                    current_page = max(current_page - 1, 0)
                elif str(reaction.emoji) == "❌":
                    await message.delete()
                    return

                await message.edit(embed=pages[current_page])
                await message.remove_reaction(reaction, user)
                
            except asyncio.TimeoutError:
                try:
                    await message.clear_reactions()
                except discord.Forbidden:
                    pass
                break

    @rolereaction.command(name="ignored_roles", description="Which roles are ignored", no_pm=True)
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def ignored_roles_list(self, ctx: commands.Context):
        """View ignored roles"""
        await self.wait_until_ready()
        
        if not self.ignored_roles:
            return await ctx.send("No roles are currently being ignored.", delete_after=9)

        # Convert role IDs to role objects
        roles = []
        for role_id in self.ignored_roles:
            role = ctx.guild.get_role(role_id)
            if role:
                roles.append(role)
            else:
                roles.append(f"Deleted Role ({role_id})")

        # Sort roles by position (highest first)
        roles.sort(key=lambda r: r.position if isinstance(r, discord.Role) else 0, reverse=True)

        embed = discord.Embed(
            title="Ignored Roles",
            description="Members with these roles won't get reaction roles",
            color=discord.Color.blue()
        )
        
        for role in roles:
            if isinstance(role, discord.Role):
                members = len(role.members)
                created_at = role.created_at.strftime('%Y-%m-%d')
                embed.add_field(
                    name=role.name,
                    value=f"Members: {members}\nCreated: {created_at}\nPosition: {role.position}",
                    inline=True
                )
            else:
                embed.add_field(
                    name=role,
                    value="*Role no longer exists*",
                    inline=True
                )
        
        embed.set_footer(text=f"Total ignored roles: {len(roles)}")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle when a reaction is added."""
        if payload.user_id == self.bot.user.id:
            return

        await self.wait_until_ready()

        # Check for restricted emojis
        emoji_str = str(payload.emoji)
        if emoji_str in restricted_emojis:
            return
        
        # Check if the reaction is from a bot
        user = self.bot.get_user(payload.user_id)
        if user and user.bot:
            return

        if self.paused:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            return

        # Check blacklist and ignored roles
        if (payload.user_id in self.blacklist or
            any(role.id in self.ignored_roles for role in member.roles)):
            return

        emoji_key = payload.emoji.name if hasattr(payload.emoji, 'id') else str(payload.emoji)
        
        if emoji_key in self.roles:
            role_id = self.roles[emoji_key]
            role = guild.get_role(role_id)
            
            if role:
                try:
                    await member.add_roles(
                        role, 
                        reason=f"Reaction role added by {member} (emoji: {payload.emoji})"
                    )
                    await self._log_action(
                        guild,
                        f"Added {role.name} to {member} via reaction role",
                        color=discord.Color.green()
                    )
                except discord.Forbidden:
                    await self._log_action(
                        guild,
                        f"Failed to add {role.name} to {member} (missing permissions)",
                        color=discord.Color.red()
                    )
                except discord.HTTPException as e:
                    await self._log_action(
                        guild,
                        f"Error adding role to {member}: {str(e)}",
                        color=discord.Color.red()
                    )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Handle when a reaction is removed."""
        await self.wait_until_ready()
        
        if self.paused:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            return

        emoji_key = payload.emoji.name if hasattr(payload.emoji, 'id') else str(payload.emoji)
        
        if emoji_key in self.roles:
            role_id = self.roles[emoji_key]
            role = guild.get_role(role_id)
            
            if role:
                try:
                    await member.remove_roles(
                        role,
                        reason=f"Reaction role removed by {member} (emoji: {payload.emoji})"
                    )
                    await self._log_action(
                        guild,
                        f"Removed {role.name} from {member} via reaction role",
                        color=discord.Color.orange()
                    )
                except discord.Forbidden:
                    await self._log_action(
                        guild,
                        f"Failed to remove {role.name} from {member} (missing permissions)",
                        color=discord.Color.red()
                    )

    async def _log_action(self, guild: discord.Guild, message: str, color: discord.Color):
        """Helper method to log actions to audit log channel.
        
        Parameters
        ----------
        guild : discord.Guild
            The guild where the action occurred
        message : str
            The message to log
        color : discord.Color
            The color of the embed
        """
        if not self.audit_channel_id:
            return

        channel = guild.get_channel(self.audit_channel_id)
        if channel:
            try:
                embed = discord.Embed(
                    description=message,
                    color=color,
                    timestamp=discord.utils.utcnow()
                )
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

    @rolereaction.command(description='Run this command first', no_pm=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def set_audit_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for audit logs.
        
        Parameters
        ----------
        channel : discord.TextChannel
            The channel to send audit logs to
        """
        try:
            await self.db.find_one_and_update(
                {"_id": "audit_channel"},
                {"$set": {"channel_id": str(channel.id)}},
                upsert=True
            )
            self.audit_channel_id = channel.id
            await ctx.send(f"Audit logs will now be sent to {channel.mention}")
        except Exception as e:
            await ctx.send(f"Failed to set audit channel: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleReact(bot))
    
