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

import discord, logging, asyncio, time, re, random, json

from datetime import datetime as t
from pytz import timezone as z
from discord.ext import commands
from core import checks
from core.models import PermissionLevel

logger = logging.getLogger("Modmail")


class Private(commands.Cog):
    """Private Discord.py plugin for managing notifications and announcements regarding Gauḍīya Vaiṣṇava podcasts"""
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.default_tzs = {
            "IST": "Asia/Kolkata",
            "GMT": "Europe/London",
            "EST": "America/New_York",
            "PST": "America/Los_Angeles",
            "BOT": "America/La_Paz"
        }

    async def get_guild_config(self, guild_id):
        """Retrieve or create guild configuration using Modmail’s plugin_db"""
        config = await self.db.find_one({"_id": str(guild_id)})
        
        if not config:
            # Create default config if none exists
            default_config = {
                "_id": str(guild_id),
                "target_guild": guild_id,
                "target_channel": None,
                "timezones": self.default_tzs,
                "speaker": "and speaker",
                "ping_role": None,
                "last_updater": t.now().timestamp()
            }
            await self.db.insert_one(default_config)
            return config  # default_config

        # Ensure all fields exist
        defaults = {
            "timezones": self.default_tzs,
            "speaker": "and speaker",
            "ping_role": None
        }
        
        for key, value in defaults.items():
            if key not in config:
                config[key] = value

        # Convert timestamp back to datetime if needed
        if isinstance(config.get("last_updater"), (int, float)):
            config["last_updater"] = t.fromtimestamp(config["last_updater"])
        
        return config

    async def update_config(self, guild_id, update_data):
        """Update guild configuration using Modmail’s plugin_db"""
        # Convert datetime to timestamp for storage
        if "last_updater" in update_data and isinstance(update_data["last_updater"], t):
            update_data["last_updater"] = update_data["last_updater"].timestamp()
        
        await self.db.update_one(
            {"_id": str(guild_id)},
            {"$set": update_data},
            upsert=True
        )
    
    # +------------------------------------------------------------+
    # |                   CONFIGURATION COMMANDS                   |
    # +------------------------------------------------------------+
    @commands.command(name="setup_notifications", description="Configure notification settings for this guild")
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def _setup_notifications(self, ctx):
        """Interactive setup for notification configuration"""
        # Step 1: Get target channel
        await ctx.send("Please mention the target channel for notifications:")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.channel_mentions
        
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            target_channel = msg.channel_mentions[0]
        except asyncio.TimeoutError:
            return await ctx.send("Setup timed out. Please try again.")
        
        # Step 2: Get speaker name
        await ctx.send("Please enter the speaker/host display name:")
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=lambda m: m.author == ctx.author)
            speaker = msg.content
        except asyncio.TimeoutError:
            return await ctx.send("Setup timed out. Please try again.")
        
        # Step 3: Get ping role
        await ctx.send("Please mention the role to ping (or type 'skip' to skip):")
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=lambda m: m.author == ctx.author)
            if msg.content.lower() != 'skip' and msg.role_mentions:
                ping_role = msg.role_mentions[0].id
            else:
                ping_role = None
        except asyncio.TimeoutError:
            return await ctx.send("Setup timed out. Please try again.")
        
        # Save configuration
        await self.update_config(ctx.guild.id, {
            "$set": {
                "target_channel": target_channel.id,
                "speaker": speaker,
                "ping_role": ping_role,
                "last_updater": t.now().timestamp()
            }
        })
        
        await ctx.send(f"✅ Notification configuration saved!\n"
                         f"**Channel:** {target_channel.mention}\n"
                         f"**Speaker:** {speaker}\n"
                         f"**Ping Role:** {f'<@&{ping_role}>' if ping_role else 'None'}")

    @commands.command(name="debug_private_config", description="View your configurations")
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def debug_config(self, ctx):
        """Show the current configuration"""
        config = await self.get_guild_config(ctx.guild.id)
        
        printable_config = {
            "_id": config.get("_id"),
            "target_channel": config.get("target_channel"),
            "speaker": config.get("speaker"),
            "ping_role": config.get("ping_role"),
            "timezones": config.get("timezones", {}),
            "last_updater": str(config.get("last_updater"))
        }
        
        await ctx.send(f"Current config:\n```json\n{json.dumps(printable_config, indent=2)}\n```")

    @commands.command(name="reset_timezones", description="Reset timezone configurations")
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def reset_timezones(self, ctx):
        """Reset timezones to default"""
        await self.update_config(ctx.guild.id, {
            "timezones": self.default_tzs,
            "last_updater": t.now()
        })
        await ctx.send("✅ Timezones reset to defaults!")
    
    @commands.command(name="set_timezones", description="Set timezones using reactions")
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    @commands.guild_only()
    async def set_timezones(self, ctx):
        """Interactive timezone setup using reactions"""
        embed = discord.Embed(
            title="Timezone Setup",
            description="React with the flags for timezones you want to include:\n"
                        "🇮🇳 - IST (Asia/Kolkata)\n"
                        "🇬🇧 - GMT (Europe/London)\n"
                        "🗽 - EST (America/New_York)\n"
                        "🇺🇸 - PST (America/Los_Angeles)\n"
                        "🇦🇷 - ART (America/Argentina/Buenos_Aires)\n"
                        "🇧🇴 - BOT (America/La_Paz)\n\n"
                        "Click ✅ when done.",
            color=discord.Color.blue()
        )
        msg = await ctx.send(embed=embed)
        
        # Add reaction options
        emoji_map = {
            "🇮🇳": ("IST", "Asia/Kolkata"),
            "🇬🇧": ("GMT", "Europe/London"),
            "🗽": ("EST", "America/New_York"),
            "🇺🇸": ("PST", "America/Los_Angeles"),
            "🇦🇷": ("ART", "America/Argentina/Buenos_Aires"),
            "🇧🇴": ("BOT", "America/La_Paz"),
            "✅": "done"
        }
        
        for emoji in emoji_map.keys():
            await msg.add_reaction(emoji)
        
        selected_tzs = {}
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in emoji_map
        
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                emoji = str(reaction.emoji)
                
                if emoji == "✅":
                    break
                
                code, tz = emoji_map[emoji]
                selected_tzs[code] = tz
                await msg.remove_reaction(emoji, user)
                
            except asyncio.TimeoutError:
                await ctx.send("Timezone setup timed out.")
                return
        
        if selected_tzs:
            await self.update_config(ctx.guild.id, {
                "timezones": selected_tzs,
                "last_updater": t.now()
            })
            await ctx.send(f"✅ Selected timezones saved: {', '.join(selected_tzs.keys())}")
        else:
            await ctx.send("No timezones selected. Using defaults.")

    # +------------------------------------------------------------+
    # |                    NOTIFICATION COMMANDS                   |
    # +------------------------------------------------------------+
    @commands.command(description='Sends notification into same channel', aliases=['poke'], no_pm=True)
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    async def radhe(self, ctx: commands.Context, *, event_today: str = None):
        """Send a push notification in the current channel"""
        config = await self.get_guild_config(ctx.guild.id)
        await self._send_notification(ctx, ctx.channel, event_today, config)

    @commands.command(description='Sends the push notification to the General channel', aliases=['nudge'], no_pm=True)
    @commands.has_any_role('Admin', 'Mod', 'Moderator')
    async def gaura(self, ctx, *, _event_today: str = None):
        """Send a push notification to the configured channel"""
        config = await self.get_guild_config(ctx.guild.id)
        target_channel = self.bot.get_channel(config.get('target_channel', 358429353966698500))
        
        if not target_channel:
            return await ctx.send("Couldn’t find the target channel! Please configure one first.", delete_after=10)
        
        await self._send_notification(ctx, target_channel, _event_today, config)
    
    # +------------------------------------------------------------+
    # |                    NOTIFICATION LOGIC                      |
    # +------------------------------------------------------------+
    async def _send_notification(self, ctx, channel, _event_today=None, config=None):
        """Notification sending logic"""
        if config is None:
            config = await self.get_guild_config(channel.guild.id)
        
        start_time = time.time()
        
        # Delete original message if not in target channel
        if channel.id != ctx.channel.id:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
        
        # Get guild name from target channel’s guild
        guild_name = channel.guild.name
        _avy_img = ctx.guild.icon.url if ctx.guild.icon else ctx.author.avatar.url
        
        # Get ping role if configured
        ping_role = config.get('ping_role')
        _poke = f'<@&{ping_role}> || ℍ𝕒𝕣𝕚 𝕜𝕒𝕥𝕙𝕒̄ 𝖯𝗎𝗌𝗁-𝗇𝗈𝗍𝗂𝖿𝗂𝖼𝖺𝗍𝗂𝗈𝗇 ||' if ping_role else 'ℍ𝕒𝕣𝕚 𝕜𝕒𝕥𝕙𝕒̄ 𝖯𝗎𝗌𝗁-𝗇𝗈𝗍𝗂𝖿𝗂𝖼𝖺𝗍𝗂𝗈𝗇 @here'

        # Get speaker from config
        _host = config.get('speaker', 'and speaker')

        err_m = f"{ctx.author.mention}, update this channel’s **Topic**.\n\n" \
                f"**Tip:** ask a Mod for help setting up this channel for the commands to work."

        INTRO = [
            f'*Turn off and tune into* the **{guild_name}** Podcast, ',
            f'Bring auspiciousness to your day with the **{guild_name}** Podcast, ',
            f'Hello and welcome to the **{guild_name}** Podcast, ',
            f'It’s a beautiful day to listen to the **{guild_name}** Podcast, ',
            f'It is a nice day to listen to the **{guild_name}** Podcast, ',
            f'Make your day succesfull by listening to the **{guild_name}** Podcast, ',
            f'This is the **{guild_name}** Podcast, ',
            f'Tune into the **{guild_name}** Podcast, ',
            f'Welcome to the **{guild_name}** Podcast, '
        ]

        TEACHINGS = [
            'our Rūpānuga Guru-varga',
            'our Vaiṣṇava Ācāryas',
            'the Śrī Gauḍīya Vaiṣṇavas'
        ]

        JOIN = [
            ', to delve deeper into',
            ', to explore and connect with',
            ', so that you can learn, grow, and connect personally on'
        ]

        OUTRO = [
            'So, let’s dive into this valuable study together and learn about this wanderful process',
            'So, sit back, relax, and listen attentively as we embark on this spiritual journey together',
            'Without further ado, sit back, relax and, listen attentively',
            'Hold on to your chairs, and simply “lend us your ears”',
            'You’ve been eagerly waiting for this, and so have we. Sit back, relax and, listen attentively'
        ]

        """
        if isinstance(channel, discord.TextChannel):
            if not channel.topic:
                return await ctx.send(err_m, delete_after=23)

            if '—' in channel.topic:
                _host = channel.topic.split('—')[-1]
            else:
                _host = config.get('speaker', 'and speaker')
        """

        def get_ordinal_suffix(num):
            if 11 <= num % 32 <= 13:
                suffix = 'ᵗʰ'
            else:
                suffix = {1: 'ˢᵗ', 2: 'ⁿᵈ', 3: 'ʳᵈ'}.get(num % 10, 'ᵗʰ')
            return suffix

        print("Stored timezones:", config.get('timezones'))
        def get_t_str():
            t_str = []
            # Get the current config (make sure this is passed correctly from the calling function)
            timezones = config.get('timezones', self.default_tzs)
            
            # Emoji mapping that matches what you used in set_timezones
            emoji_map = {
                "IST": "🇮🇳",
                "GMT": "🇬🇧",
                "EST": "🗽",
                "PST": "🇺🇸",
                "ART": "🇦🇷",
                "BOT": "🇧🇴"
            }
            
            for code, tz_name in timezones.items():
                try:
                    tz = z(tz_name)
                    t_now = t.now(tz)
                    suffix = get_ordinal_suffix(t_now.day)
                    
                    # Get the emoji from our mapping
                    flag_emoji = emoji_map.get(code, f":flag_{code.lower()}:")
                    
                    date_str = t_now.strftime('**%H**:%M:%S, %A %b %d, %Y')
                    date_str = date_str.replace(f"{t_now.day},", f"{t_now.day}{suffix},")
                    
                    t_str.append(f"{flag_emoji} {code} — {date_str}")
                except Exception as e:
                    print(f"Error processing timezone {code}: {str(e)}")
                    continue
            return "\n".join(t_str)

        if _event_today is not None and _event_today.startswith('extra'):
            def _intro():
                intro_text = f'\u200b{random.choice(INTRO)}where we explore the teachings of {random.choice(TEACHINGS)}. Join our host {_host} for a thought-provoking discussion{random.choice(JOIN)} your spiritual journey throught the path of Rūpānuga Ujjvala Mādhurya-prema.\n\n{random.choice(OUTRO)}.'
                return intro_text.encode('utf-8').decode('utf-8')

            _what = ' '.join(_event_today.split(' ')[1:])
            _notif = 'https://cdn.discordapp.com/attachments/375179500604096512/1079876674235154442/flyerdesign_27022023_172353.png'
            em = discord.Embed(colour=discord.Colour(0xff7722), description=get_t_str())
            em.set_author(name='𝖧𝖺𝗋𝗂-𝗄𝖺𝗍𝗁𝖺̄ 𝗋𝖾𝗆𝗂𝗇𝖽𝖾𝗋', icon_url=_avy_img)
            em.add_field(name='Event today:', value=_what, inline=False)
            em.add_field(name='Attentive Listeners', value=_intro(), inline=False)
            em.set_thumbnail(url=_notif)
            em.set_footer(text=f'⇐ Join the Voice Channel NOW! — {self.bot.latency*1000:.2f}ms')
            message = await channel.send(content=_poke, embed=em)
        else:
            def _intro():
                intro_text = f'\u200b{random.choice(INTRO)}where we explore the teachings of {random.choice(TEACHINGS)}. Join our host {_host} for a thought-provoking discussion{random.choice(JOIN)} your spiritual journey throught the path of Rūpānuga Ujjvala Mādhurya-prema.\n\n{random.choice(OUTRO)}.'
                return intro_text.encode('utf-8').decode('utf-8')

            try:
                em = discord.Embed(colour=discord.Colour(0xff7722), description=get_t_str())
                em.set_author(name='𝖧𝖺𝗋𝗂-𝗄𝖺𝗍𝗁𝖺̄ 𝗋𝖾𝗆𝗂𝗇𝖽𝖾𝗋', icon_url=_avy_img)
                em.add_field(name='Attentive Listeners', value=_intro(), inline=False)
                em.set_thumbnail(url='https://i.imgur.com/93A0Kdk.png')
                em.set_footer(text=f'⇐ Join the Voice Channel NOW! — {self.bot.latency*1000:.2f}ms')
                message = await channel.send(content=_poke, embed=em)
            except discord.Forbidden:
                _simple = f'{_poke}\n{get_t_str()}\n\n{_intro()}'
                message = await channel.send(_simple)

        try:
            await asyncio.sleep(2)
            await message.add_reaction('thankful:695101751707303998')
        except discord.HTTPException:
            pass

        # Send confirmation to original text channel
        if channel.id != ctx.channel.id:
            try:
                confirmation = await ctx.send(f"ℍ𝕒𝕣𝕚 𝕜𝕒𝕥𝕙𝕒̄ Push-Notification sent to **{channel.mention}**! \nSent in {self.bot.latency*1000:.2f}ms'")
                await asyncio.sleep(2)
                await confirmation.add_reaction('✅')
            except discord.HTTPException:
                pass

async def setup(bot):
    await bot.add_cog(Private(bot))
