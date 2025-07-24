# sadhucore.py
import random
import discord
from datetime import datetime as t
from pytz import timezone as z

from .sadhubase import HardCoded


class SadhuUI:
    """UI components and static data for SadhuSevana plugin"""

    # Class attributes from sadhubase
    INTRO = HardCoded["INTRO"]
    TEACHINGS = HardCoded["TEACHINGS"]
    JOIN = HardCoded["JOIN"]
    OUTRO = HardCoded["OUTRO"]
    DEFAULT_TIMEZONES = HardCoded["DEFAULT_TIMEZONES"]
    TIMEZONE_OPTIONS = HardCoded["TIMEZONE_OPTIONS"]
    EMOJI_MAP = HardCoded["EMOJI_MAP"]
    NOTIFICATION_BANNERS = HardCoded["NOTIFICATION_BANNERS"]

    @staticmethod
    def get_ordinal_suffix(num):
        """Get ordinal suffix for day numbers"""
        if 11 <= num % 32 <= 13:
            suffix = 'ᵗʰ'
        else:
            suffix = {1: 'ˢᵗ', 2: 'ⁿᵈ', 3: 'ʳᵈ'}.get(num % 10, 'ᵗʰ')
        return suffix

    @staticmethod
    def generate_intro_text(guild_name, speaker):
        """Generate random intro text for notifications"""
        intro_base = random.choice(HardCoded["INTRO"]).format(guild_name=guild_name)
        teachings = random.choice(HardCoded["TEACHINGS"])
        join_text = random.choice(HardCoded["JOIN"])
        outro = random.choice(HardCoded["OUTRO"])

        intro_text = f'\u200b{intro_base}where we explore the teachings of {teachings}. Join our host {speaker} for a thought-provoking discussion{join_text} your spiritual journey through the path of Rūpānuga Ujjvala Mādhurya-prema.\n\n{outro}.'
        return intro_text.encode('utf-8').decode('utf-8')

    @staticmethod
    def format_timezones(timezones):
        """Format timezone strings for display"""
        t_str = []
        for code, tz_name in timezones.items():
            try:
                tz = z(tz_name)
                t_now = t.now(tz)
                suffix = SadhuUI.get_ordinal_suffix(t_now.day)

                flag_emoji = SadhuUI.EMOJI_MAP.get(code, f":flag_{code.lower()}:")
                date_str = t_now.strftime('**%H**:%M:%S — %A %b %d, %Y')
                date_str = date_str.replace(f"{t_now.day},", f"{t_now.day}{suffix},")

                t_str.append(f"{flag_emoji} {date_str} 「{code}」")
            except Exception as e:
                print(f"Error processing timezone {code}: {str(e)}")
                t_str.append(f"⚠️ {code} — Timezone Error")
                continue
        return "\n".join(t_str)

    @staticmethod
    def create_notification_embed(guild, author, config, event_today=None, bot_latency=0):
        """Create notification embed"""
        guild_name = guild.name
        avatar_img = guild.icon.url if guild.icon else author.avatar.url
        speaker = config.get('speaker', 'and speaker')
        timezones = config.get('timezones', SadhuUI.DEFAULT_TIMEZONES)

        if event_today and event_today.startswith('extra'):
            what = ' '.join(event_today.split(' ')[1:])
            notif_image = 'https://cdn.discordapp.com/attachments/375179500604096512/1079876674235154442/flyerdesign_27022023_172353.png'

            em = discord.Embed(colour=discord.Colour(0xff7722), description=SadhuUI.format_timezones(timezones))
            em.set_author(name='𝖧𝖺𝗋𝗂-𝗄𝖺𝗍𝗁𝖺̄ 𝗋𝖾𝗆𝗂𝗇𝖽𝖾𝗋', icon_url=avatar_img)
            em.add_field(name='Event today:', value=what, inline=False)
            em.add_field(name='Attentive Listeners', value=SadhuUI.generate_intro_text(guild_name, speaker), inline=False)
            em.set_thumbnail(url=notif_image)
            em.set_footer(text=f'⇐ Join the Voice Channel NOW! — {bot_latency*1000:.2f}ms')
        else:
            em = discord.Embed(colour=discord.Colour(0xff7722), description=SadhuUI.format_timezones(timezones))
            em.set_author(name='𝖧𝖺𝗋𝗂-𝗄𝖺𝗍𝗁𝖺̄ 𝗋𝖾𝗆𝗂𝗇𝖽𝖾𝗋', icon_url=avatar_img)
            em.add_field(name='Attentive Listeners', value=SadhuUI.generate_intro_text(guild_name, speaker), inline=False)
            em.set_image(url=random.choice(HardCoded['NOTIFICATION_BANNERS']))
            em.set_footer(text=f'⇐ Join the Voice Channel NOW! — {bot_latency*1000:.2f}ms')

        return em

    @staticmethod
    def create_disconnection_warning_embed(guild, users_in_voice):
        """Create disconnection warning embed"""
        user_list = ", ".join([user.display_name for user in users_in_voice])

        em = discord.Embed(
            title="Harikatha",
            description=f"Seems that {user_list} {'is' if len(users_in_voice) == 1 else 'are'} still connected to the Harikatha.",
            colour=discord.Colour(0xff7722)
        )
        em.set_thumbnail(url=guild.icon.url if guild.icon else None)
        em.set_footer(text="Cancel disconnection for Mods and Admins")

        return em


class DisconnectionWarningView(discord.ui.View):
    """View for disconnection warning with cancel button"""
    def __init__(self, voice_channel, timeout=30):
        super().__init__(timeout=timeout)
        self.voice_channel = voice_channel
        self.cancelled = False

    @discord.ui.button(label="Cancel Disconnection", style=discord.ButtonStyle.red, emoji="🛑")
    async def cancel_disconnection(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has proper permissions
        user_roles = [role.name.lower() for role in interaction.user.roles]
        if not any(role in ['admin', 'mod', 'moderator'] for role in user_roles):
            await interaction.response.send_message(
                "Sorry, only Admins and Mods can prevent disconnection.",
                ephemeral=True
            )
            return

        self.cancelled = True
        self.stop()
        await interaction.response.edit_message(
            content="✅ Disconnection cancelled by a moderator.",
            embed=None,
            view=None
        )

    async def on_timeout(self):
        """Called when the view times out - just mark as timed out, don't disconnect"""
        if not self.cancelled:
            # Don't disconnect here - let the main loop handle it
            # Just log that the timeout occurred
            print(f"Warning timeout occurred for voice channel {self.voice_channel.name}")
            # Optionally update the message to show timeout
            try:
                # This will only work if the message is still accessible
                pass
            except:
                pass


class TimezoneView(discord.ui.View):
    """Interactive timezone selection view"""

    def __init__(self, cog, ctx, timeout=60):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.ctx = ctx
        self.selected_tzs = {}
        self.message = None
        # Fixed: Create deep copies to avoid modifying original data
        self.options = [opt.copy() for opt in SadhuUI.TIMEZONE_OPTIONS]

        # Create buttons for each timezone
        for opt in self.options:
            btn = discord.ui.Button(
                style=discord.ButtonStyle.gray,
                label=f"「{opt['code']}」",
                custom_id=opt['code']
            )
            btn.callback = self.create_callback(opt)
            self.add_item(btn)

        # Add done button
        done_btn = discord.ui.Button(
            style=discord.ButtonStyle.blurple,
            label="✅ Done",
            row=4
        )
        done_btn.callback = self.finish_selection
        self.add_item(done_btn)

    def create_callback(self, option):
        async def callback(interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("Only the command author can select timezones.", ephemeral=True)
                return

            # Toggle selection
            option['selected'] = not option['selected']

            # Update button style
            for child in self.children:
                if getattr(child, 'custom_id', None) == option['code']:
                    child.style = discord.ButtonStyle.green if option['selected'] else discord.ButtonStyle.gray

            # Update selected timezones
            if option['selected']:
                self.selected_tzs[option['code']] = option['tz']
            else:
                self.selected_tzs.pop(option['code'], None)

            await interaction.response.edit_message(view=self)
        return callback

    async def finish_selection(self, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Only the command author can finish selection.", ephemeral=True)
            return

        self.stop()
        # Add error handling for message editing
        try:
            await self.message.edit(view=None)
        except discord.NotFound:
            pass  # Message was deleted

        if self.selected_tzs:
            # Add error handling for database operations
            try:
                await self.cog.db.update_one(
                    {"_id": str(interaction.guild.id)},
                    {"$set": {
                        "timezones": self.selected_tzs,
                        "last_updater": t.now().timestamp()
                    }}
                )
                await interaction.response.send_message(
                    f"✅ Selected timezones saved: {', '.join(self.selected_tzs.keys())}",
                    delete_after=15
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"Error saving timezones: {str(e)}",
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                "No timezones selected. Using defaults.",
                delete_after=15
            )

    async def on_timeout(self):
        try:
            await self.message.edit(view=None)
            await self.ctx.send("Timezone setup timed out.", delete_after=15)
        except (discord.NotFound, AttributeError):
            pass  # Message was deleted or ctx is unavailable
