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

import discord
import logging
import asyncio
from typing import Optional, Dict, Set
from discord.ext import commands
from discord import User
from core import checks
from core.models import PermissionLevel

# Translation libraries (primary and fallback)
try:
    from deep_translator import GoogleTranslator  # Primary translator
    HAS_DEEP_TRANSLATOR = True
except ImportError:
    HAS_DEEP_TRANSLATOR = False
    from googletrans import Translator  # Fallback 1
    from mtranslate import translate  # Fallback 2

logger = logging.getLogger("Modmail")

__version__ = "2.0.0"

class Translate(commands.Cog):
    """🔠 Translation tools for Modmail with user preferences and auto-translation.
    
    Features:
    - Manual text translation
    - Auto-translation in threads
    - User language preferences
    - Multiple translation service fallbacks
    """

    def __init__(self, bot):
        self.bot = bot
        self.user_color = discord.Colour(0xed791d)  # orange
        self.mod_color = discord.Colour(0x7289da)  # blurple
        self.db = bot.plugin_db.get_partition(self)
        self.tt: Set[int] = set()  # Auto-translate threads
        self.enabled = True
        self.user_prefs: Dict[int, str] = {}  # {user_id: target_lang}
        self.lock = asyncio.Lock()  # For thread-safe operations
        
        # Initialize translator
        if HAS_DEEP_TRANSLATOR:
            self.translator = GoogleTranslator
        else:
            self.translator = Translator()
        
        # Supported languages (ISO 639-1 codes)
        self.languages = {
            "af": "Afrikaans", "sq": "Albanian", "am": "Amharic", "ar": "Arabic",
            "hy": "Armenian", "az": "Azerbaijani", "eu": "Basque", "be": "Belarusian",
            "bn": "Bengali", "bs": "Bosnian", "bg": "Bulgarian", "ca": "Catalan",
            "ceb": "Cebuano", "ny": "Chichewa", "zh": "Chinese", "co": "Corsican",
            "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch",
            "en": "English", "eo": "Esperanto", "et": "Estonian", "tl": "Filipino",
            "fi": "Finnish", "fr": "French", "fy": "Frisian", "gl": "Galician",
            "ka": "Georgian", "de": "German", "el": "Greek", "gu": "Gujarati",
            "ht": "Haitian Creole", "ha": "Hausa", "haw": "Hawaiian", "he": "Hebrew",
            "hi": "Hindi", "hmn": "Hmong", "hu": "Hungarian", "is": "Icelandic",
            "ig": "Igbo", "id": "Indonesian", "ga": "Irish", "it": "Italian",
            "ja": "Japanese", "jw": "Javanese", "kn": "Kannada", "kk": "Kazakh",
            "km": "Khmer", "ko": "Korean", "ku": "Kurdish", "ky": "Kyrgyz",
            "lo": "Lao", "la": "Latin", "lv": "Latvian", "lt": "Lithuanian",
            "lb": "Luxembourgish", "mk": "Macedonian", "mg": "Malagasy", "ms": "Malay",
            "ml": "Malayalam", "mt": "Maltese", "mi": "Maori", "mr": "Marathi",
            "mn": "Mongolian", "my": "Myanmar", "ne": "Nepali", "no": "Norwegian",
            "ps": "Pashto", "fa": "Persian", "pl": "Polish", "pt": "Portuguese",
            "pa": "Punjabi", "ro": "Romanian", "ru": "Russian", "sm": "Samoan",
            "gd": "Scots Gaelic", "sr": "Serbian", "st": "Sesotho", "sn": "Shona",
            "sd": "Sindhi", "si": "Sinhala", "sk": "Slovak", "sl": "Slovenian",
            "so": "Somali", "es": "Spanish", "su": "Sundanese", "sw": "Swahili",
            "sv": "Swedish", "tg": "Tajik", "ta": "Tamil", "te": "Telugu",
            "th": "Thai", "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu",
            "uz": "Uzbek", "vi": "Vietnamese", "cy": "Welsh", "xh": "Xhosa",
            "yi": "Yiddish", "yo": "Yoruba", "zu": "Zulu"
        }
        
        # Reverse mapping for name to code
        self.lang_names = {v.lower(): k for k, v in self.languages.items()}
        
        bot.loop.create_task(self._load_config())

    async def _load_config(self):
        """Load configuration and user preferences from database."""
        try:
            async with self.lock:
                config = await self.db.find_one({'_id': 'config'})
                if config:
                    self.enabled = config.get('enabled', True)
                    self.tt = set(config.get('auto-translate', []))
                
                # Load user preferences
                prefs = await self.db.find_one({'_id': 'user_prefs'})
                if prefs:
                    self.user_prefs = prefs.get('prefs', {})
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)

    async def _translate_text(self, text: str, target: str, source: str = 'auto') -> str:
        """Translate text using available services with fallback.
        
        Args:
            text: The text to translate
            target: Target language code (e.g., 'es')
            source: Source language code (default 'auto' for auto-detection)
            
        Returns:
            Translated text or error message if translation fails
        """
        if not text.strip():
            return "No text provided to translate."
            
        try:
            # Try primary translator first
            if HAS_DEEP_TRANSLATOR:
                translated = GoogleTranslator(source=source, target=target).translate(text)
                return translated
            
            # Fallback to googletrans
            try:
                translated = self.translator.translate(text, dest=target, src=source).text
                return translated
            except Exception:
                # Final fallback to mtranslate
                return translate(text, target)
                
        except Exception as e:
            logger.error(f"Translation failed: {e}", exc_info=True)
            return f"⚠️ Translation failed: {str(e)}"

    @commands.group(aliases=['translate', 'tr'], invoke_without_command=True)
    @commands.guild_only()
    async def translation(self, ctx, target_lang: Optional[str] = None, *, text: Optional[str] = None):
        """Translate text to another language.
        
        Usage:
        {prefix}translation <target_language> <text>
        {prefix}translation set <language> (to set your preferred language)
        
        Examples:
        {prefix}translation french Hello world
        {prefix}translation set spanish
        """
        if target_lang is None:
            return await ctx.send_help(ctx.command)
            
        # Handle set preference command
        if target_lang.lower() == 'set' and text:
            return await self._set_user_language(ctx, text)
            
        # Check if user has a preferred target language
        user_lang = self.user_prefs.get(ctx.author.id)
        if user_lang and not target_lang:
            target_lang = user_lang
            text = target_lang  # Shift arguments
            
        if not text:
            return await ctx.send("Please provide text to translate.")
            
        # Clean and validate language input
        target_lang = target_lang.lower().strip()
        lang_code = self.lang_names.get(target_lang) or target_lang[:2]
        
        if lang_code not in self.languages:
            return await ctx.send(
                f"⚠️ Unsupported language. Use `{ctx.prefix}translation langs` for available languages."
            )
            
        try:
            # Translate the text
            translated = await self._translate_text(text, lang_code)
            
            # Handle message length limits
            if len(translated) > 2000:
                translated = translated[:1990] + "... [truncated]"
                
            # Create embed response
            lang_name = self.languages[lang_code]
            embed = discord.Embed(
                color=self.user_color,
                title=f"Translation to {lang_name}",
                description=translated
            )
            embed.set_author(
                name=f"{ctx.author.display_name} ({ctx.author.id})",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None
            )
            embed.add_field(
                name="Original Text",
                value=text[:1024] + ("..." if len(text) > 1024 else ""),
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Translation command failed: {e}", exc_info=True)
            await ctx.send(f"⚠️ An error occurred during translation: {str(e)}")

    async def _set_user_language(self, ctx, language: str):
        """Set a user's preferred target language."""
        language = language.lower().strip()
        lang_code = self.lang_names.get(language) or language[:2]
        
        if lang_code not in self.languages:
            return await ctx.send(
                f"⚠️ Unsupported language. Use `{ctx.prefix}translation langs` for available languages."
            )
            
        async with self.lock:
            self.user_prefs[ctx.author.id] = lang_code
            await self.db.update_one(
                {'_id': 'user_prefs'},
                {'$set': {'prefs': self.user_prefs}},
                upsert=True
            )
            
        lang_name = self.languages[lang_code]
        await ctx.send(f"✅ Your preferred translation language has been set to {lang_name}.")

    @translation.command(name='langs', aliases=['languages'])
    @commands.guild_only()
    async def list_languages(self, ctx):
        """List all available languages for translation."""
        lang_list = "\n".join(f"{code}: {name}" for code, name in sorted(self.languages.items()))
        
        if len(lang_list) > 2000:
            lang_list = lang_list[:1990] + "... [truncated]"
            
        embed = discord.Embed(
            title="Available Languages",
            description=f"```\n{lang_list}\n```",
            color=self.mod_color
        )
        embed.set_footer(text=f"Use '{ctx.prefix}translation set <language>' to set your preference")
        await ctx.send(embed=embed)

    @commands.command(aliases=['tt'])
    @commands.guild_only()
    async def translatetext(self, ctx, message_id: Optional[int] = None, target_lang: Optional[str] = None):
        """Translate a message by ID or the replied message.
        
        Usage:
        {prefix}tt <message_id> [target_language]
        {prefix}tt [target_language] (when replying to a message)
        
        If no target language is specified, uses your preferred language or English.
        """
        # Determine target language
        if target_lang:
            lang_code = self.lang_names.get(target_lang.lower()) or target_lang[:2]
            if lang_code not in self.languages:
                return await ctx.send("⚠️ Unsupported language.")
        else:
            lang_code = self.user_prefs.get(ctx.author.id, 'en')
            
        # Get the target message
        message = None
        if message_id:
            try:
                message = await ctx.channel.fetch_message(message_id)
            except discord.NotFound:
                return await ctx.send("⚠️ Message not found.")
            except discord.Forbidden:
                return await ctx.send("⚠️ No permission to access that message.")
        elif ctx.message.reference:
            try:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except:
                pass
                
        if not message:
            return await ctx.send("⚠️ Please specify a message ID or reply to a message.")
            
        # Translate the message content
        text = message.content
        if not text.strip():
            return await ctx.send("⚠️ The selected message has no text content.")
            
        try:
            translated = await self._translate_text(text, lang_code)
            lang_name = self.languages[lang_code]
            
            embed = discord.Embed(
                description=translated,
                color=self.user_color,
                timestamp=message.created_at
            )
            embed.set_author(
                name=f"Translated to {lang_name}",
                icon_url="https://i.imgur.com/yeHFKgl.png"
            )
            embed.set_footer(text=f"Original message by {message.author.display_name}")
            
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Translate text command failed: {e}", exc_info=True)
            await ctx.send(f"⚠️ Failed to translate message: {str(e)}")

    @commands.command(aliases=['att'])
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @checks.thread_only()
    async def auto_translate_thread(self, ctx):
        """Toggle auto-translation for this modmail thread."""
        async with self.lock:
            if ctx.channel.id in self.tt:
                self.tt.remove(ctx.channel.id)
                removed = True
            else:
                self.tt.add(ctx.channel.id)
                removed = False
            
            await self.db.update_one(
                {'_id': 'config'},
                {'$set': {'auto-translate': list(self.tt)}},
                upsert=True
            )
            
        status = "disabled" if removed else "enabled"
        await ctx.send(f"✅ Auto-translation has been {status} for this thread.")

    @commands.command(aliases=['tat'])
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.guild_only()
    async def toggle_auto_translations(self, ctx, enabled: bool):
        """Enable or disable auto-translation system-wide.
        
        Usage:
        {prefix}tat <True/False>
        """
        async with self.lock:
            self.enabled = enabled
            await self.db.update_one(
                {'_id': 'config'},
                {'$set': {'enabled': self.enabled}},
                upsert=True
            )
            
        status = "enabled" if enabled else "disabled"
        await ctx.send(f"✅ Auto-translation has been {status} system-wide.")

    async def on_message(self, message):
        """Handle auto-translation of messages in configured threads."""
        if (not self.enabled or 
            not message.guild or 
            message.author.bot or 
            message.channel.id not in self.tt or
            "User ID:" not in getattr(message.channel, 'topic', '')):
            return
            
        try:
            # Get text to translate (from embed or content)
            text = None
            if message.embeds and message.embeds[0].description:
                text = message.embeds[0].description
            elif message.content:
                text = message.content
                
            if not text:
                return
                
            # Get target language (default to English)
            user_id = int(message.channel.topic.split("User ID: ")[1].split("\n")[0])
            lang_code = self.user_prefs.get(user_id, 'en')
            
            # Translate the text
            translated = await self._translate_text(text, lang_code)
            if len(translated) > 2000:
                translated = translated[:1990] + "... [truncated]"
                
            # Send translation
            embed = discord.Embed(
                description=translated,
                color=4388013  # Blurple
            )
            embed.set_footer(text="Auto-translated message")
            await message.channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Auto-translation failed: {e}", exc_info=True)

async def setup(bot):
    await bot.add_cog(Translate(bot))
