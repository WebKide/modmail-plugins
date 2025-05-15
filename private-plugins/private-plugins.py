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
__version__ = "v2.0.01"

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

                # Find the plugin directory automatically
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

    async def unload_private_plugin(self, plugin):
        """Unload a private plugin"""
        try:
            # Detect the actual cog name
            cog_name = self.detect_cog_name(plugin)
            ext_string = f"plugins.private.{plugin.name}"

            # First try to unload the extension
            await self.bot.unload_extension(ext_string)

            # Remove from loaded plugins set
            self.loaded_private_plugins.discard(plugin)

            return True
        except commands.ExtensionNotLoaded:
            return True
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin}: {str(e)}")
            return False

    @private_group.command(name="update")
    @trigger_typing
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def update_plugins(self, ctx):
        """Interactive plugin update interface"""
        # Debug: Log currently tracked plugins
        logger.info(f"Tracked plugins: {[str(p) for p in self.manager.loaded_private_plugins]}")

        # Get actually loaded extensions for verification
        loaded_extensions = set(self.bot.extensions.keys())
        available_plugins = [
            p for p in self.manager.loaded_private_plugins 
            if p.ext_string in loaded_extensions
        ]
        
        if not available_plugins:
            embed = discord.Embed(
                description="❌ No properly loaded private plugins found\n"
                          f"Tracked: {len(self.manager.loaded_private_plugins)}\n"
                          f"Loaded: {len(loaded_extensions)}",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)

        if not self.manager.loaded_private_plugins:
            embed = discord.Embed(
                description="❌ No private plugins loaded yet",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)

        plugins = sorted(available_plugins, key=lambda p: p.name)
        current_index = 0

        async def create_plugin_embed(plugin):
            """Generate detailed embed for a plugin"""
            cog_name = self.manager.detect_cog_name(plugin)
            cog = self.bot.get_cog(cog_name)
            
            embed = discord.Embed(
                title=f"🔄 Plugin Update: {plugin.name}",
                color=self.bot.main_color
            )
            
            # Add plugin description
            if cog and cog.description:
                embed.description = cog.description
            else:
                embed.description = "No description available"
            
            # Add command list
            if cog:
                commands_list = []
                for cmd in cog.get_commands():
                    cmd_help = cmd.help or "No description"
                    commands_list.append(f"`{ctx.prefix}{cmd.name}` - {cmd_help}")
                
                if commands_list:
                    embed.add_field(
                        name="🤖 Available Commands",
                        value="\n".join(commands_list)[:1024],
                        inline=False
                    )
            
            # Add plugin reference
            embed.add_field(
                name="🔗 Plugin Reference",
                value=f"```bash\n{ctx.prefix}private load {plugin.user}/{plugin.repo}/{plugin.name}@{plugin.branch}```",
                inline=False
            )
            
            # Add user info
            embed.add_field(
                name="👤 Requested By",
                value=f"{ctx.author.mention} (`{ctx.author.id}`)",
                inline=False
            )
            
            embed.set_footer(text="𝖳𝗁𝗂𝗌 𝗂𝗇𝗍𝖾𝗋𝖿𝖺𝖼𝖾 𝗐𝗂𝗅𝗅 𝗍𝗂𝗆𝖾𝗈𝗎𝗍 𝗂𝗇 𝖺 𝗆𝗂𝗇𝗎𝗍𝖾")
            return embed

        # Create initial view with buttons
        class UpdateView(discord.ui.View):
            def __init__(self, *, timeout=60):
                super().__init__(timeout=timeout)
                self.message = None
                self.index = current_index
                
            async def update_embed(self, interaction):
                plugin = plugins[self.index]
                embed = await create_plugin_embed(plugin)
                await interaction.response.edit_message(embed=embed, view=self)
                
            @discord.ui.button(label="PREV", style=discord.ButtonStyle.blurple)
            async def previous(self, interaction, button):
                self.index = (self.index - 1) % len(plugins)
                await self.update_embed(interaction)
                
            @discord.ui.button(label="Remove", style=discord.ButtonStyle.red)
            async def remove(self, interaction, button):
                plugin = plugins[self.index]
                try:
                    await self.manager.unload_private_plugin(plugin)
                    shutil.rmtree(plugin.abs_path, ignore_errors=True)
                    plugins.pop(self.index)
                    
                    if not plugins:
                        embed = discord.Embed(
                            description="✅ All plugins have been removed",
                            color=self.bot.main_color
                        )
                        await interaction.response.edit_message(embed=embed, view=None)
                        return
                        
                    self.index = min(self.index, len(plugins) - 1)
                    await self.update_embed(interaction)
                    
                except Exception as e:
                    error_embed = discord.Embed(
                        title="❌ Removal Failed",
                        description=f"```py\n{str(e)[:1900]}```",
                        color=self.bot.error_color
                    )
                    await interaction.response.edit_message(embed=error_embed, view=None)
                
            @discord.ui.button(label="Update", style=discord.ButtonStyle.green)
            async def update(self, interaction, button):
                plugin = plugins[self.index]
                try:
                    # Show updating status
                    updating_embed = discord.Embed(
                        description=f"🔄 Updating **{plugin}**...",
                        color=self.bot.main_color
                    )
                    await interaction.response.edit_message(embed=updating_embed, view=None)
                    
                    # Perform update
                    await self.manager.unload_private_plugin(plugin)
                    await self.manager.download_private_plugin(plugin)
                    await self.manager.load_private_plugin(plugin)
                    
                    # Show success
                    success_embed = discord.Embed(
                        description=f"✅ Successfully updated **{plugin}**!",
                        color=self.bot.main_color
                    )
                    await interaction.message.edit(embed=success_embed)
                    
                except Exception as e:
                    # Format traceback
                    tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                    error_embed = discord.Embed(
                        title="❌ Update Failed",
                        description=f"```py\n{tb[:1900]}```",
                        color=self.bot.error_color
                    )
                    await interaction.message.edit(embed=error_embed)
                
            @discord.ui.button(label="NEXT", style=discord.ButtonStyle.blurple)
            async def next(self, interaction, button):
                self.index = (self.index + 1) % len(plugins)
                await self.update_embed(interaction)
                
            async def on_timeout(self):
                try:
                    plugin = plugins[self.index]
                    embed = await create_plugin_embed(plugin)
                    embed.set_footer(text="𝖳𝗁𝗂𝗌 𝗂𝗇𝗍𝖾𝗋𝖿𝖺𝖼𝖾 𝗍𝗂𝗆𝖾𝖽 𝗈𝗎𝗍")
                    await self.message.edit(embed=embed, view=None)
                except Exception:
                    pass

        # Send initial message
        view = UpdateView()
        initial_embed = await create_plugin_embed(plugins[current_index])
        view.message = await ctx.send(embed=initial_embed, view=view)

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

    def detect_cog_name(self, plugin):
        """Detect the actual cog name by parsing the python files"""
        init_file = plugin.abs_path / "__init__.py"
        py_files = list(plugin.abs_path.glob("*.py"))

        # Check all Python files in the plugin directory
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Look for class definitions that inherit from commands.Cog
                        if line.strip().startswith('class ') and '(commands.Cog)' in line:
                            # Extract the class name
                            cog_name = line.split('class ')[1].split('(')[0].strip()
                            return cog_name
            except Exception as e:
                logger.warning(f"Error reading {py_file}: {str(e)}")

        # Fallback to the plugin name if no cog class found
        return plugin.name

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
        self.bot.loop.create_task(self.manager.sync_loaded_plugins())

    # ╔════════════════╦══════════════════════╦════════════════════╗
    # ╠════════════════╣PRIVATE GROUP COMMANDS╠════════════════════╣
    # ╚════════════════╩══════════════════════╩════════════════════╝
    @commands.group(name="private", aliases=['pr'], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def private_group(self, ctx):
        """Manage private GitHub plugins"""
        await ctx.send_help(ctx.command)

    @private_group.command(name="token")
    @trigger_typing
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
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
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
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
            plugin = Plugin(user, repo, name, branch or "main")
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ Invalid plugin reference: {str(e)}",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)

        # Create initial loading embed
        embed = discord.Embed(
            title=f"Loading Plugin: {name}",
            description=f"Downloading **{plugin}** from GitHub...",
            color=self.bot.main_color
        )
        msg = await ctx.send(embed=embed)

        try:
            # Force clean install
            if plugin.abs_path.exists():
                shutil.rmtree(plugin.abs_path, ignore_errors=True)
                await asyncio.sleep(1)

            await self.manager.download_private_plugin(plugin)
            embed.description = f"✅ Successfully downloaded **{plugin}**!\n\nNow loading the plugin..."
            await msg.edit(embed=embed)

            # Load the plugin
            success = await self.manager.load_private_plugin(plugin)
            if success:
                # Detect the actual cog name
                cog_name = self.manager.detect_cog_name(plugin)
                cog = self.bot.get_cog(cog_name)

                if cog:
                    # Create help embed using the detected cog name
                    help_embed = discord.Embed(
                        title=f"{cog_name} Plugin Commands",
                        description=f"Type `{ctx.prefix}help {cog_name}` for more details",
                        color=discord.Colour(0xed791d)
                    )

                    # Get all commands from the cog
                    commands_list = []
                    for cmd in cog.get_commands():
                        commands_list.append(f"`{ctx.prefix}{cmd.name}` - {cmd.short_doc or 'No description'}")

                    if commands_list:
                        help_embed.add_field(
                            name="Available Commands",
                            value="\n".join(commands_list),
                            inline=False
                        )
                    else:
                        help_embed.add_field(
                            name="Note",
                            value="This plugin doesn't expose any commands",
                            inline=False
                        )

                    # Update success embed
                    embed.description = f"✅ Successfully loaded **{plugin}**!"
                    embed.add_field(
                        name="Plugin Ready",
                        value=f"Type `{ctx.prefix}help {cog_name}` for command details",
                        inline=False
                    )
                    await msg.edit(embed=embed)
                    await ctx.send(embed=help_embed)
                else:
                    embed.description = f"✅ Plugin loaded but no cog found with name: {cog_name}"
                    await msg.edit(embed=embed)
            else:
                embed.description = (
                    f"✅ Plugin loaded but no cog found with name: {cog_name}\n"
                    f"(Tried to find cog class named '{cog_name}')"
                )
                await msg.edit(embed=embed)

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
                title=f"Failed to Load: {name}",
                description=error_msg,
                color=self.bot.error_color
            )
            await msg.edit(embed=embed)

    @private_group.command(name="unload", aliases=["remove", "delete"])
    @trigger_typing
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def unload_plugin(self, ctx, *, plugin_ref: str):
        """Unload a private-plugin"""
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

        try:
            success = await self.manager.unload_private_plugin(plugin)
            embed = discord.Embed(color=self.bot.main_color)

            if success:
                embed.description = f"✅ Successfully unloaded **{plugin}**!"
                # Clean up files
                try:
                    shutil.rmtree(plugin.abs_path)
                    embed.set_footer(text="Plugin files were removed")
                except Exception as e:
                    logger.warning(f"Failed to remove plugin files: {str(e)}")
                    embed.set_footer(text="Plugin was unloaded but files could not be removed")
            else:
                embed.description = f"❌ Failed to unload **{plugin}**"
                embed.color = self.bot.error_color

            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ Error unloading plugin: {str(e)}",
                color=self.bot.error_color
            )
            await ctx.send(embed=embed)

    @private_group.command(name="update")
    @trigger_typing
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def update_plugins(self, ctx):
        """Interactive plugin update interface"""
        # Debug: Log currently tracked plugins
        logger.info(f"Tracked plugins: {[str(p) for p in self.manager.loaded_private_plugins]}")

        # Get actually loaded extensions for verification
        loaded_extensions = set(self.bot.extensions.keys())
        available_plugins = [
            p for p in self.manager.loaded_private_plugins 
            if p.ext_string in loaded_extensions
        ]
        
        if not available_plugins:
            embed = discord.Embed(
                description="❌ No properly loaded private plugins found\n"
                          f"Tracked: {len(self.manager.loaded_private_plugins)}\n"
                          f"Loaded: {len(loaded_extensions)}",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)

        if not self.manager.loaded_private_plugins:
            embed = discord.Embed(
                description="❌ No private plugins loaded yet",
                color=self.bot.error_color
            )
            return await ctx.send(embed=embed)

        plugins = sorted(available_plugins, key=lambda p: p.name)
        current_index = 0

        async def create_plugin_embed(plugin):
            """Generate detailed embed for a plugin"""
            cog_name = self.manager.detect_cog_name(plugin)
            cog = self.bot.get_cog(cog_name)
            
            embed = discord.Embed(
                title=f"🔄 Plugin Update: {plugin.name}",
                color=self.bot.main_color
            )
            
            # Add plugin description
            if cog and cog.description:
                embed.description = cog.description
            else:
                embed.description = "No description available"
            
            # Add command list
            if cog:
                commands_list = []
                for cmd in cog.get_commands():
                    cmd_help = cmd.help or "No description"
                    commands_list.append(f"`{ctx.prefix}{cmd.name}` - {cmd_help}")
                
                if commands_list:
                    embed.add_field(
                        name="🤖 Available Commands",
                        value="\n".join(commands_list)[:1024],
                        inline=False
                    )
            
            # Add plugin reference
            embed.add_field(
                name="🔗 Plugin Reference",
                value=f"```bash\n{ctx.prefix}private load {plugin.user}/{plugin.repo}/{plugin.name}@{plugin.branch}```",
                inline=False
            )
            
            # Add user info
            embed.add_field(
                name="👤 Requested By",
                value=f"{ctx.author.mention} (`{ctx.author.id}`)",
                inline=False
            )
            
            embed.set_footer(text="𝖳𝗁𝗂𝗌 𝗂𝗇𝗍𝖾𝗋𝖿𝖺𝖼𝖾 𝗐𝗂𝗅𝗅 𝗍𝗂𝗆𝖾𝗈𝗎𝗍 𝗂𝗇 𝖺 𝗆𝗂𝗇𝗎𝗍𝖾")
            return embed

        # Create initial view with buttons
        class UpdateView(discord.ui.View):
            def __init__(self, *, timeout=60):
                super().__init__(timeout=timeout)
                self.message = None
                self.index = current_index
                
            async def update_embed(self, interaction):
                plugin = plugins[self.index]
                embed = await create_plugin_embed(plugin)
                await interaction.response.edit_message(embed=embed, view=self)
                
            @discord.ui.button(label="PREV", style=discord.ButtonStyle.blurple)
            async def previous(self, interaction, button):
                self.index = (self.index - 1) % len(plugins)
                await self.update_embed(interaction)
                
            @discord.ui.button(label="Remove", style=discord.ButtonStyle.red)
            async def remove(self, interaction, button):
                plugin = plugins[self.index]
                try:
                    await self.manager.unload_private_plugin(plugin)
                    shutil.rmtree(plugin.abs_path, ignore_errors=True)
                    plugins.pop(self.index)
                    
                    if not plugins:
                        embed = discord.Embed(
                            description="✅ All plugins have been removed",
                            color=self.bot.main_color
                        )
                        await interaction.response.edit_message(embed=embed, view=None)
                        return
                        
                    self.index = min(self.index, len(plugins) - 1)
                    await self.update_embed(interaction)
                    
                except Exception as e:
                    error_embed = discord.Embed(
                        title="❌ Removal Failed",
                        description=f"```py\n{str(e)[:1900]}```",
                        color=self.bot.error_color
                    )
                    await interaction.response.edit_message(embed=error_embed, view=None)
                
            @discord.ui.button(label="Update", style=discord.ButtonStyle.green)
            async def update(self, interaction, button):
                plugin = plugins[self.index]
                try:
                    # Show updating status
                    updating_embed = discord.Embed(
                        description=f"🔄 Updating **{plugin}**...",
                        color=self.bot.main_color
                    )
                    await interaction.response.edit_message(embed=updating_embed, view=None)
                    
                    # Perform update
                    await self.manager.unload_private_plugin(plugin)
                    await self.manager.download_private_plugin(plugin)
                    await self.manager.load_private_plugin(plugin)
                    
                    # Show success
                    success_embed = discord.Embed(
                        description=f"✅ Successfully updated **{plugin}**!",
                        color=self.bot.main_color
                    )
                    await interaction.message.edit(embed=success_embed)
                    
                except Exception as e:
                    # Format traceback
                    tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                    error_embed = discord.Embed(
                        title="❌ Update Failed",
                        description=f"```py\n{tb[:1900]}```",
                        color=self.bot.error_color
                    )
                    await interaction.message.edit(embed=error_embed)
                
            @discord.ui.button(label="NEXT", style=discord.ButtonStyle.blurple)
            async def next(self, interaction, button):
                self.index = (self.index + 1) % len(plugins)
                await self.update_embed(interaction)
                
            async def on_timeout(self):
                try:
                    plugin = plugins[self.index]
                    embed = await create_plugin_embed(plugin)
                    embed.set_footer(text="𝖳𝗁𝗂𝗌 𝗂𝗇𝗍𝖾𝗋𝖿𝖺𝖼𝖾 𝗍𝗂𝗆𝖾𝖽 𝗈𝗎𝗍")
                    await self.message.edit(embed=embed, view=None)
                except Exception:
                    pass

        # Send initial message
        view = UpdateView()
        initial_embed = await create_plugin_embed(plugins[current_index])
        view.message = await ctx.send(embed=initial_embed, view=view)

    @private_group.command(name="loaded")
    @trigger_typing
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
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
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
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
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
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
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
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
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
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

    @private_group.command(name="guide")
    @commands.guild_only()
    async def plugin_guide(self, ctx):
        """Show how to structure private plugins"""
        example_ini = """```py
    # __init__.py
    from .yourprivatecogname import setup

    __all__ = ['setup']
    ```"""
        example_code = """```py
    # yourprivatecogname.py
    import discord
    from discord.ext import commands

    class YourPrivateCogName(commands.Cog):
        '''Basic example of a plugin'''  
        def __init__(self, bot):
            self.bot = bot
            
        @commands.command()
        async def repeat(self, ctx, *, msg=''):
            '''Bot repeats message'''
            if msg is None:
                return await ctx.send('Nice try. (｡◝‿◜｡)', delete_after=6)
            else:
                await ctx.send(f"\U0000200b{msg}")

    async def setup(bot):
        await bot.add_cog(YourPrivateCogName(bot))
    ```"""

        embed = discord.Embed(
            title="🚧 Example Plugin Guidelines",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="📁 Private Repository Structure",
            value=(
                "```mathematica\n"
                "your-private-repo/\n"
                "╚═ pluginname/\n"
                "   ╠═ __init__.py       # Required\n"
                "   ╠═ pluginname.py     # Required\n"
                "   ╚═ requirements.txt  # Optional\n"
                "```"
            ),
            inline=False
        )
        embed.add_field(
            name="💾 Basic \_\_init\_\_.py Example",
            value=example_ini,
            inline=False
        )
        embed.add_field(
            name="💻 Basic Cog.py Example",
            value=example_code,
            inline=False
        )        
        embed.add_field(
            name="🔧 Installation",
            value=f"`{ctx.prefix}private load your-username/your-repo/plugin-name@branch`",
            inline=False
        )
        embed.set_footer(text="Remember: Your cog class name doesn’t need to match the plugin folder name")
        
        await ctx.send(embed=embed)

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
    # await cog.manager.sync_loaded_plugins()
