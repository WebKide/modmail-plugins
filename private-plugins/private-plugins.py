import asyncio
import io
import json
import logging
import os
import shutil
import sys
import typing
import zipfile
import importlib
from difflib import get_close_matches
from pathlib import Path, PurePath
from re import match
from site import USER_SITE
from subprocess import PIPE

import discord
from discord.ext import commands
from pkg_resources import parse_version

from core import checks
from core.models import PermissionLevel, getLogger
from core.paginator import EmbedPaginatorSession
from core.utils import truncate, trigger_typing


logger = logging.getLogger("Modmail")

class Plugin:
    """Represents a private GitHub plugin"""
    def __init__(self, user, repo, name, branch="main"):  # Changed default to "main"
        self.user = user
        self.repo = repo
        self.name = name
        self.branch = branch
        self.url = f"https://api.github.com/repos/{user}/{repo}/zipball/{branch}"

        # Path where the plugin will be stored
        plugins_dir = Path("plugins/private")
        self.abs_path = plugins_dir / name
        self.ext_string = f"plugins.private.{name}"

    def __str__(self):
        return f"{self.name}@{self.branch}"

    def __repr__(self):
        return f"<Plugin {self.user}/{self.repo}/{self.name}@{self.branch}>"

    def __hash__(self):
        return hash((self.user, self.repo, self.name, self.branch))

    def __eq__(self, other):
        if not isinstance(other, Plugin):
            return False
        return (self.user, self.repo, self.name, self.branch) == (
            other.user, other.repo, other.name, other.branch
        )

class PrivatePluginManager:
    """Handles the core logic for private-plugin management"""
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self._token_cache = None
        self.loaded_private_plugins = set()
        self.emoji_map = {
            "1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3,
            "5️⃣": 4, "6️⃣": 5, "7️⃣": 6, "8️⃣": 7,
            "⬅️": "prev", "➡️": "next"
        }

    async def get_github_token(self):
        """Retrieve GitHub token from database"""
        if self._token_cache:
            return self._token_cache

        config = await self.db.find_one({"_id": "github_config"})
        if config and "token" in config:
            self._token_cache = config["token"]
            return self._token_cache
        return None

    async def set_github_token(self, token):
        """Store GitHub token in database"""
        await self.db.update_one(
            {"_id": "github_config"},
            {"$set": {"token": token}},
            upsert=True
        )
        self._token_cache = token

    async def verify_github_token(self, token):
        """Verify if GitHub token has repo access"""
        headers = {"Authorization": f"token {token}"}
        try:
            async with self.bot.session.get(
                "https://api.github.com/user/repos",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return True
                return False
        except Exception:
            return False

    async def download_private_plugin(self, plugin):
        """Download and install a private-plugin from GitHub"""
        token = await self.get_github_token()
        if not token:
            raise ValueError("GitHub token not configured")

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        plugin_io = None

        try:
            # Verify repo exists
            repo_url = f"https://api.github.com/repos/{plugin.user}/{plugin.repo}"
            async with self.bot.session.get(repo_url, headers=headers) as resp:
                if resp.status == 404:
                    raise ValueError(f"Repository not found: {plugin.user}/{plugin.repo}")
                if resp.status != 200:
                    raise ValueError(f"GitHub API returned status {resp.status}")

            # Download zip
            async with self.bot.session.get(plugin.url, headers=headers) as resp:
                if resp.status != 200:
                    raise ValueError(f"Failed to download: {resp.status} - {plugin.url}")

                raw = await resp.read()
                plugin_io = io.BytesIO(raw)

            # Create plugin directory if it doesn't exist
            plugin.abs_path.mkdir(parents=True, exist_ok=True)

            # Extract zip
            with zipfile.ZipFile(plugin_io) as zipf:
                logger.debug("=== ZIP CONTENTS ===")
                for name in zipf.namelist():
                    logger.debug(name)

                # Get the root directory (contains commit hash)
                root_dir = zipf.namelist()[0]
                
                # Special handling for sadhusevanacog structure
                if plugin.name == "sadhusevanacog":
                    # The plugin files are in root_dir/sadhusevanacog/
                    plugin_dir = f"{root_dir}sadhusevanacog/"
                else:
                    # Try to find the plugin directory automatically
                    plugin_dir = None
                    for name in zipf.namelist():
                        if name.lower().endswith(plugin.name.lower() + '/') or f'/{plugin.name.lower()}/' in name.lower():
                            plugin_dir = name
                            break

                    if not plugin_dir:
                        raise ValueError(f"Could not find plugin directory '{plugin.name}' in the repository")

                # Extract only the plugin files
                for info in zipf.infolist():
                    if info.filename.startswith(plugin_dir):
                        # Remove the plugin_dir prefix from the path
                        rel_path = info.filename[len(plugin_dir):]
                        if not rel_path:  # Skip the root directory
                            continue

                        plugin_path = plugin.abs_path / rel_path

                        if info.is_dir():
                            plugin_path.mkdir(parents=True, exist_ok=True)
                        else:
                            plugin_path.parent.mkdir(parents=True, exist_ok=True)
                            with zipf.open(info) as src, plugin_path.open("wb") as dst:
                                shutil.copyfileobj(src, dst)

            # Verify __init__.py exists
            if not (plugin.abs_path / "__init__.py").exists():
                # Provide detailed directory listing for debugging
                dir_contents = []
                for f in plugin.abs_path.iterdir():
                    dir_contents.append(f"- {f.name} ({'dir' if f.is_dir() else 'file'})")
                    if f.is_dir():
                        for sub_f in f.iterdir():
                            dir_contents.append(f"  - {sub_f.name} ({'dir' if sub_f.is_dir() else 'file'})")
                
                raise ValueError(
                    f"Plugin directory '{plugin.name}' does not contain required '__init__.py' file.\n"
                    f"Directory contents:\n" + "\n".join(dir_contents)
                )

        except Exception as e:
            # Clean up if something went wrong
            if plugin.abs_path.exists():
                shutil.rmtree(plugin.abs_path, ignore_errors=True)
            raise ValueError(f"Download failed: {str(e)}")
        finally:
            if plugin_io:
                plugin_io.close()

    async def load_private_plugin(self, plugin):
        """Load a private-plugin into the Bot"""
        # First, verify the plugin directory exists
        if not plugin.abs_path.exists():
            raise ValueError(f"Plugin directory not found: {plugin.abs_path}")

        # Check for __init__.py specifically
        init_file = plugin.abs_path / "__init__.py"
        if not init_file.exists():
            # Debug: List all files in the directory recursively
            files = []
            for f in plugin.abs_path.rglob("*"):
                files.append(f"- {f.relative_to(plugin.abs_path)}")
            raise ValueError(
                f"Plugin '{plugin.name}' is missing __init__.py file.\n"
                f"Directory contents:\n" + "\n".join(files)
            )

        # Handle requirements
        req_txt = plugin.abs_path / "requirements.txt"
        if req_txt.exists():
            try:
                # Don't use --user in virtualenv
                venv = hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
                user_install = "" if venv else " --user"
                proc = await asyncio.create_subprocess_shell(
                    f"{sys.executable} -m pip install --upgrade{user_install} -r {req_txt}",
                    stderr=PIPE,
                    stdout=PIPE,
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode != 0:
                    error_msg = stderr.decode().strip() or stdout.decode().strip()
                    raise ValueError(f"Requirements install failed: {error_msg}")
                    
            except Exception as e:
                raise ValueError(f"Failed to install requirements: {str(e)}")

        try:
            # First verify the setup function exists
            spec = importlib.util.spec_from_file_location(
                plugin.ext_string,
                plugin.abs_path / "__init__.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, 'setup'):
                raise ValueError(
                    f"Plugin '{plugin.name}' is missing required 'setup' function. "
                    "It must contain: `def setup(bot): bot.add_cog(YourCogClass(bot))`"
                )

            await self.bot.load_extension(plugin.ext_string)
            self.loaded_private_plugins.add(plugin)
            return True

        except Exception as e:
            # Get detailed error info for debugging
            error_type = type(e).__name__
            tb = getattr(e, "__traceback__", None)
            if tb:
                # Proper way to get frame information
                frames = []
                while tb:
                    frames.append(f"{tb.tb_frame.f_code.co_filename}:{tb.tb_lineno}")
                    tb = tb.tb_next
                error_trace = "\n".join(frames[-3:])  # Last 3 frames
            else:
                error_trace = "No traceback available"
                
            raise ValueError(
                f"Failed to load plugin '{plugin.name}':\n"
                f"Type: {error_type}\n"
                f"Error: {str(e)}\n"
                f"Trace: {error_trace}"
            )

    async def create_plugin_embed(self, page=0, interactive=False):
        """Create paginated embed of private plugins"""
        plugins = sorted(self.loaded_private_plugins, key=lambda p: p.name)
        total_pages = (len(plugins) + 7) // 8
        page = max(0, min(page, total_pages - 1))

        embed = discord.Embed(
            title=f"Private Plugins (Page {page + 1}/{total_pages})",
            color=self.bot.main_color
        )

        for i in range(8):
            idx = page * 8 + i
            if idx >= len(plugins):
                break

            plugin = plugins[idx]
            emoji = list(self.emoji_map.keys())[i]
            embed.add_field(
                name=f"{emoji} {plugin.name}@{plugin.branch}",
                value=f"{plugin.user}/{plugin.repo}\n{self.get_plugin_description(plugin)}",
                inline=False
            )

        if interactive:
            embed.set_footer(text="React with the corresponding emoji to update a plugin")
        return embed

    def get_plugin_description(self, plugin):
        """Get description of a loaded plugin"""
        cog = self.bot.get_cog(plugin.name)
        if cog and cog.description:
            return truncate(cog.description, 100)
        return "No description available"

class PrivatePlugins(commands.Cog):
    """Manage private GitHub plugins for your Bot"""
    def __init__(self, bot):
        self.bot = bot
        self.manager = PrivatePluginManager(bot)
        self.active_messages = {}

    # ╔════════════════╦══════════════════════╦════════════════════╗
    # ╠════════════════╣PRIVATE GROUP COMMANDS╠════════════════════╣
    # ╚════════════════╩══════════════════════╩════════════════════╝
    @commands.group(name="private", aliases=['pr'], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.OWNER)
    async def private_group(self, ctx):
        """Manage private GitHub plugins"""
        await ctx.send_help(ctx.command)

    @private_group.command(name="token")
    @trigger_typing
    @checks.has_permissions(PermissionLevel.OWNER)
    async def set_token(self, ctx, token: str = None):
        """Set or verify your GitHub TOKEN with repo access"""
        if not token:
            embed = discord.Embed(
                title="GitHub Token Setup",
                description="Please provide your GitHub token with repo access.\n"
                            "Create one at: https://github.com/settings/tokens/new\n\n"
                            "⚠️ **Warning:** This will be stored in the Bot’s database.",
                color=self.bot.error_color
            )
            embed.add_field(
                name="Required Scopes", 
                value="`repo` (Full control of private repositories)\n- Private repository contents (read/write)\n- Repository metadata\n- Commit status", 
                inline=False
            )
            embed.add_field(
                name="Recommended Settings", 
                value="**Token Name:** `Modmail Private Plugins`\n(or any descriptive name)", 
                inline=False
            )
            embed.add_field(
                name="Expiration", 
                value="For security, set an expiration date (e.g., 6 months)\nYou’ll need to generate a new TOKEN after expiration", 
                inline=False
            )
            embed.add_field(
                name="Scope Selection", 
                value="✅ **repo** (Full control of private repositories)\n❌ No other scopes needed", 
                inline=False
            )
            embed.add_field(
                name="Generate token", 
                value="**Copy the token immediately** (you won’t see it again!)", 
                inline=False
            )
            embed.set_footer(text="IMPORTANT!! Treat this token like a password")
            return await ctx.send(embed=embed)

        embed = discord.Embed(color=self.bot.main_color)
        try:
            if await self.manager.verify_github_token(token):
                await self.manager.set_github_token(token)
                embed.description = "✅ GitHub token verified and stored successfully!"
            else:
                embed.description = "❌ Invalid token or missing repo access"
                embed.color = self.bot.error_color
        except Exception as e:
            embed.description = f"❌ Error verifying token: {str(e)}"
            embed.color = self.bot.error_color

        await ctx.send(embed=embed)

    @private_group.command(name="load", aliases=["add", "install"])
    @trigger_typing
    @checks.has_permissions(PermissionLevel.OWNER)
    async def load_plugin(self, ctx, *, plugin_ref: str):
        """Load a private-plugin from GitHub"""
        # Check for token first
        token = await self.manager.get_github_token()
        if not token:
            embed = discord.Embed(
                title="GitHub Token Required",
                description="No GitHub token configured. Please set one first with:\n"
                           f"`{ctx.prefix}private token YOUR_TOKEN`",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)

        # Parse plugin reference
        try:
            m = match(r"^(.+?)/(.+?)/(.+?)(?:@(.+?))?$", plugin_ref)
            if not m:
                raise ValueError("Invalid format. Use: user/repo/name@branch")
            user, repo, name, branch = m.groups()
            plugin = Plugin(user, repo, name, branch or "main")  # Changed default to "main"
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ Invalid plugin reference: {str(e)}",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            description=f"Downloading **{plugin}**...",
            color=self.bot.main_color
        )
        msg = await ctx.send(embed=embed)

        try:
            # Force clean install
            if plugin.abs_path.exists():
                shutil.rmtree(plugin.abs_path, ignore_errors=True)
                await asyncio.sleep(1)  # Give filesystem time to update

            await self.manager.download_private_plugin(plugin)

            # Debug: List downloaded files
            downloaded_files = "\n".join(p.name for p in plugin.abs_path.glob("*"))
            logger.debug(f"Downloaded files in {plugin.abs_path}:\n{downloaded_files}")

            # Load the plugin
            success = await self.manager.load_private_plugin(plugin)
            if success:
                embed.description = f"✅ Successfully loaded **{plugin}**!"
                # Add debug info to footer
                embed.set_footer(text=f"Path: {plugin.abs_path}")
            else:
                embed.description = f"❌ Failed to load **{plugin}**"
                embed.color = self.bot.error_color

        except Exception as e:
            # Get detailed error info
            error_msg = str(e)
            if isinstance(e, ValueError) and hasattr(e, "__traceback__"):
                error_type = type(e).__name__
                tb = e.__traceback__
                frames = []
                while tb:
                    frames.append(f"{tb.tb_frame.f_code.co_filename}:{tb.tb_lineno}")
                    tb = tb.tb_next
                error_trace = "\n".join(frames[-3:])
                error_msg = (f"❌ Error loading plugin:\n"
                            f"```\n"
                            f"Repository: {plugin.user}/{plugin.repo}\n"
                            f"Branch: {plugin.branch}\n"
                            f"Error Type: {error_type}\n"
                            f"Error: {str(e)}\n"
                            f"Trace: {error_trace}\n"
                            f"```")

            embed = discord.Embed(
                description=error_msg,
                color=self.bot.error_color
            )
            await msg.edit(embed=embed)

    @private_group.command(name="unload", aliases=["remove", "delete"])
    @trigger_typing
    @checks.has_permissions(PermissionLevel.OWNER)
    async def unload_plugin(self, ctx, *, plugin_ref: str):
        """Unload a private-plugin"""
        try:
            m = match(r"^(.+?)/(.+?)/(.+?)(?:@(.+?))?$", plugin_ref)
            if not m:
                raise ValueError("Invalid format. Use: user/repo/name@branch")
            user, repo, name, branch = m.groups()
            plugin = Plugin(user, repo, name, branch or "master")
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ Invalid plugin reference: {str(e)}",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)

        success = await self.manager.unload_private_plugin(plugin)
        embed = discord.Embed(color=self.bot.main_color)
        if success:
            embed.description = f"✅ Successfully unloaded **{plugin}**!"
            # Clean up files
            try:
                shutil.rmtree(plugin.abs_path)
            except Exception as e:
                logger.warning(f"Failed to remove plugin files: {str(e)}")
        else:
            embed.description = f"❌ Plugin **{plugin}** not loaded or failed to unload"
            embed.color = self.bot.error_color

        await ctx.send(embed=embed)

    @private_group.command(name="update")
    @trigger_typing
    @checks.has_permissions(PermissionLevel.OWNER)
    async def update_plugins(self, ctx):
        """Interactive plugin update interface"""
        if not self.manager.loaded_private_plugins:
            embed = discord.Embed(
                description="No private-plugins loaded",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)

        embed = await self.manager.create_plugin_embed(page=0, interactive=True)
        msg = await ctx.send(embed=embed)

        for emoji in list(self.manager.emoji_map.keys())[:8]:
            await msg.add_reaction(emoji)
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")

        self.active_messages[msg.id] = {
            "page": 0,
            "user_id": ctx.author.id
        }

    @private_group.command(name="loaded")
    @trigger_typing
    @checks.has_permissions(PermissionLevel.OWNER)
    async def loaded_plugins(self, ctx):
        """Show loaded private-plugins"""
        if not self.manager.loaded_private_plugins:
            embed = discord.Embed(
                description="No private plugins loaded",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)

        embed = await self.manager.create_plugin_embed(page=0, interactive=False)
        await ctx.send(embed=embed)

    @private_group.command(name="testtoken")
    async def test_token(self, ctx):
        """Test if your GitHub token is working"""
        token = await self.manager.get_github_token()
        if not token:
            return await ctx.send("❌ No token configured")

        headers = {"Authorization": f"token {token}"}
        try:
            async with self.bot.session.get(
                "https://api.github.com/user",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return await ctx.send(f"✅ Token valid for user: {data['login']}")
                return await ctx.send(f"❌ Token error: {resp.status}")
        except Exception as e:
            await ctx.send(f"❌ Connection failed: {str(e)}")

    @private_group.command(name="testrepo")
    async def test_repo(self, ctx, user: str, repo: str):
        """Test if you can access a repository"""
        token = await self.manager.get_github_token()
        if not token:
            return await ctx.send("❌ No token configured")

        headers = {"Authorization": f"token {token}"}
        try:
            async with self.bot.session.get(
                f"https://api.github.com/repos/{user}/{repo}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return await ctx.send(f"✅ Access granted to {user}/{repo}\nPrivate: {data['private']}")
                return await ctx.send(f"❌ Access denied: {resp.status}")
        except Exception as e:
            await ctx.send(f"❌ Connection failed: {str(e)}")

    @private_group.command(name="debug")
    async def debug_plugin(self, ctx, user: str, repo: str, branch: str = "main"):
        """Debug repository access issues"""
        token = await self.manager.get_github_token()
        if not token:
            return await ctx.send("❌ No GitHub token configured")

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Test 1: Check repo access
        repo_url = f"https://api.github.com/repos/{user}/{repo}"
        async with self.bot.session.get(repo_url, headers=headers) as resp:
            repo_status = resp.status
            repo_data = await resp.json() if resp.status == 200 else None

        # Test 2: Check zip download
        zip_url = f"https://api.github.com/repos/{user}/{repo}/zipball/{branch}"
        async with self.bot.session.get(zip_url, headers=headers) as resp:
            zip_status = resp.status

        embed = discord.Embed(title="GitHub Debug Information", color=self.bot.main_color)
        embed.add_field(name="Repository Access", value=f"`{repo_url}`\nStatus: {repo_status}")

        if repo_status == 200:
            embed.add_field(name="Repository Info", 
                            value=f"Name: {repo_data['full_name']}\n"
                                f"Private: {repo_data['private']}\n"
                                f"Default Branch: {repo_data['default_branch']}",
                            inline=False)

        embed.add_field(name="Zip Download", value=f"`{zip_url}`\nStatus: {zip_status}", inline=False)

        if repo_status == 200 and zip_status == 200:
            embed.description = "✅ All checks passed!"
            embed.color = discord.Color.green()
        else:
            embed.description = "❌ Issues detected"
            embed.color = discord.Color.red()

            if repo_status == 404:
                embed.add_field(name="Repo 404 Solution", 
                                value="1. Check the repository exists\n"
                                    "2. Ensure your token has `repo` scope\n"
                                    "3. For organizations, check your access level",
                                inline=False)

            if zip_status == 404:
                embed.add_field(name="Zip 404 Solution", 
                                value="1. Verify the branch exists\n"
                                    "2. Try the default branch\n"
                                    "3. Check repository visibility",
                                inline=False)

        await ctx.send(embed=embed)

    @private_group.command(name="validate")
    async def validate_plugin(self, ctx, plugin_name: str):
        """Validate a plugin's structure"""
        plugin = next((p for p in self.manager.loaded_private_plugins if p.name == plugin_name), None)
        if not plugin:
            return await ctx.send("Plugin not found or not loaded")

        try:
            spec = importlib.util.spec_from_file_location(
                plugin.ext_string,
                plugin.abs_path / "__init__.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, 'setup'):
                return await ctx.send("❌ Missing 'setup' function")

            await ctx.send("✅ Plugin structure is valid")
        except Exception as e:
            await ctx.send(f"❌ Validation failed: {str(e)}")


    # ╔════════════════════╦════════════╦══════════════════════════╗
    # ╠════════════════════╣COG.LISTENER╠══════════════════════════╣
    # ╚════════════════════╩════════════╩══════════════════════════╝
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle reactions for interactive plugin updates"""
        if user.bot or reaction.message.id not in self.active_messages:
            return

        msg_info = self.active_messages[reaction.message.id]
        if user.id != msg_info["user_id"]:
            return

        emoji = str(reaction.emoji)
        if emoji not in self.manager.emoji_map:
            return

        action = self.manager.emoji_map[emoji]
        plugins = sorted(self.manager.loaded_private_plugins)

        if isinstance(action, int):  # Update specific plugin
            idx = msg_info["page"] * 8 + action
            if idx >= len(plugins):
                return

            plugin = plugins[idx]
            embed = reaction.message.embeds[0]

            try:
                await self.manager.unload_private_plugin(plugin)
                await self.manager.download_private_plugin(plugin)
                await self.manager.load_private_plugin(plugin)

                # Update embed field
                for i, field in enumerate(embed.fields):
                    if i == action:
                        field.value = f"{plugin.user}/{plugin.repo}\n✅ Updated successfully!"
                        break

                await reaction.message.edit(embed=embed)
            except Exception as e:
                error_msg = await reaction.message.channel.send(
                    f"Failed to update **{plugin}**: ```{str(e)}```"
                )
                await asyncio.sleep(10)
                await error_msg.delete()

            await reaction.remove(user)

        elif action in ["prev", "next"]:  # Pagination
            new_page = msg_info["page"] + (-1 if action == "prev" else 1)
            total_pages = (len(plugins) + 7) // 8

            if 0 <= new_page < total_pages:
                msg_info["page"] = new_page
                embed = await self.manager.create_plugin_embed(
                    page=new_page,
                    interactive=True
                )
                await reaction.message.edit(embed=embed)

            await reaction.remove(user)

async def setup(bot):
    await bot.add_cog(PrivatePlugins(bot))
