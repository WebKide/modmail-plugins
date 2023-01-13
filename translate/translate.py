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

import discord, traceback, asyncio

from discord.ext import commands
from discord import User
from core import checks
from core.models import PermissionLevel

from mtranslate import translate
from googletrans import Translator


conv = {
    "ab": "Abkhaz",
    "aa": "Afar",
    "af": "Afrikaans",
    "ak": "Akan",
    "sq": "Albanian",
    "am": "Amharic",
    "ar": "Arabic",
    "an": "Aragonese",
    "hy": "Armenian",
    "as": "Assamese",
    "av": "Avaric",
    "ae": "Avestan",
    "ay": "Aymara",
    "az": "Azerbaijani",
    "bm": "Bambara",
    "ba": "Bashkir",
    "eu": "Basque",
    "be": "Belarusian",
    "bn": "Bengali",
    "bh": "Bihari",
    "bi": "Bislama",
    "bs": "Bosnian",
    "br": "Breton",
    "bg": "Bulgarian",
    "my": "Burmese",
    "ca": "Catalan",
    "ch": "Chamorro",
    "ce": "Chechen",
    "ny": "Nyanja",
    "zh": "Chinese",
    "cv": "Chuvash",
    "kw": "Cornish",
    "co": "Corsican",
    "cr": "Cree",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "dv": "Divehi",
    "nl": "Dutch",
    "dz": "Dzongkha",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian",
    "ee": "Ewe",
    "fo": "Faroese",
    "fj": "Fijian",
    "fi": "Finnish",
    "fr": "French",
    "ff": "Fula",
    "gl": "Galician",
    "ka": "Georgian",
    "de": "German",
    "el": "Greek",
    "gn": "Guarani",
    "gu": "Gujarati",
    "ht": "Haitian",
    "ha": "Hausa",
    "he": "Hebrew",
    "hz": "Herero",
    "hi": "Hindi",
    "ho": "Hiri-Motu",
    "hu": "Hungarian",
    "ia": "Interlingua",
    "id": "Indonesian",
    "ie": "Interlingue",
    "ga": "Irish",
    "ig": "Igbo",
    "ik": "Inupiaq",
    "io": "Ido",
    "is": "Icelandic",
    "it": "Italian",
    "iu": "Inuktitut",
    "ja": "Japanese",
    "jv": "Javanese",
    "kl": "Kalaallisut",
    "kn": "Kannada",
    "kr": "Kanuri",
    "ks": "Kashmiri",
    "kk": "Kazakh",
    "km": "Khmer",
    "ki": "Kikuyu",
    "rw": "Kinyarwanda",
    "ky": "Kyrgyz",
    "kv": "Komi",
    "kg": "Kongo",
    "ko": "Korean",
    "ku": "Kurdish",
    "kj": "Kwanyama",
    "la": "Latin",
    "lb": "Luxembourgish",
    "lg": "Luganda",
    "li": "Limburgish",
    "ln": "Lingala",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lu": "Luba-Katanga",
    "lv": "Latvian",
    "gv": "Manx",
    "mk": "Macedonian",
    "mg": "Malagasy",
    "ms": "Malay",
    "ml": "Malayalam",
    "mt": "Maltese",
    "mi": "M\u0101ori",
    "mr": "Marathi",
    "mh": "Marshallese",
    "mn": "Mongolian",
    "na": "Nauru",
    "nv": "Navajo",
    "nb": "Norwegian Bokm\u00e5l",
    "nd": "North-Ndebele",
    "ne": "Nepali",
    "ng": "Ndonga",
    "nn": "Norwegian-Nynorsk",
    "no": "Norwegian",
    "ii": "Nuosu",
    "nr": "South-Ndebele",
    "oc": "Occitan",
    "oj": "Ojibwe",
    "cu": "Old-Church-Slavonic",
    "om": "Oromo",
    "or": "Oriya",
    "os": "Ossetian",
    "pa": "Panjabi",
    "pi": "P\u0101li",
    "fa": "Persian",
    "pl": "Polish",
    "ps": "Pashto",
    "pt": "Portuguese",
    "qu": "Quechua",
    "rm": "Romansh",
    "rn": "Kirundi",
    "ro": "Romanian",
    "ru": "Russian",
    "sa": "Sanskrit",
    "sc": "Sardinian",
    "sd": "Sindhi",
    "se": "Northern-Sami",
    "sm": "Samoan",
    "sg": "Sango",
    "sr": "Serbian",
    "gd": "Scottish-Gaelic",
    "sn": "Shona",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovene",
    "so": "Somali",
    "st": "Southern-Sotho",
    "es": "Spanish",
    "su": "Sundanese",
    "sw": "Swahili",
    "ss": "Swati",
    "sv": "Swedish",
    "ta": "Tamil",
    "te": "Telugu",
    "tg": "Tajik",
    "th": "Thai",
    "ti": "Tigrinya",
    "bo": "Tibetan",
    "tk": "Turkmen",
    "tl": "Tagalog",
    "tn": "Tswana",
    "to": "Tonga",
    "tr": "Turkish",
    "ts": "Tsonga",
    "tt": "Tatar",
    "tw": "Twi",
    "ty": "Tahitian",
    "ug": "Uighur",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "ve": "Venda",
    "vi": "Vietnamese",
    "vo": "Volapuk",
    "wa": "Walloon",
    "cy": "Welsh",
    "wo": "Wolof",
    "fy": "Western-Frisian",
    "xh": "Xhosa",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "za": "Zhuang",
    "zu": "Zulu"
}

class Translate(commands.Cog):
    """ (∩｀-´)⊃━☆ﾟ.*･｡ﾟ translate text from one language to another """
    def __init__(self, bot):
        self.bot = bot
        self.user_color = discord.Colour(0xed791d) ## orange
        self.mod_color = discord.Colour(0x7289da) ## blurple
        self.db = bot.plugin_db.get_partition(self)
        self.translator = Translator()
        self.tt = set()
        self.enabled = True
        asyncio.create_task(self._set_config())
    
    async def _set_config(self):  # exception=AttributeError("'NoneType' object has no attribute 'get'")>
        try:
            config = await self.db.find_one({'_id': 'config'})
            self.enabled = config.get('enabled', True)
            self.tt = set(config.get('auto-translate', []))  # AttributeError: 'NoneType' object has no attribute 'get'
        except:
            pass


    # +------------------------------------------------------------+
    # |                   Translate cmd                            |
    # +------------------------------------------------------------+
    @commands.group(description='Command to translate across languages', aliases=['translate'],  invoke_without_command=True)
    async def tr(self, ctx, language: str = None, *, text: str = None):
        """
        (∩｀-´)⊃━☆ﾟ.*･｡ﾟ translate text from one language to another

        Usage:
        {prefix}tr Zulu hello world, welcome to this server
        """
        lang = language.title()
        available = ', '.join(conv.values())
        languages = 'Albanian, Arabic, Aymara, Belarusian, Bulgarian, Catalan, Chinese, Croatian, Czech, ' \
                    'Danish, Dutch, English, Estonian, Fijian, Finnish, French, Georgian, German, Greek, ' \
                    'Hebrew, Hindi, Irish, Icelandic, Italian, Japanese, Kannada, Kashmiri, Korean, Latin, ' \
                    'Lithuanian, Malayalam, Marathi, Norwegian, Panjabi, Persian, Polish, Portuguese, ' \
                    'Quechua, Romanian, Russian, Sanskrit, Scottish-Gaelic, Spanish, Swahili, Swedish, ' \
                    'Tamil, Telugu, Tagalog, Turkish, Urdu, Welsh, Yiddish, Zulu \n\nFor full list: \n' \
                    'https://github.com/WebKide/modmail-plugins/translate/langs.json'
        m = f'{ctx.message.author.display_name} | {ctx.message.author.id}'
        msg = f'**Usage:** {ctx.prefix}{ctx.invoked_with} <Language_target> <message>\n\n```bf\n{languages}```'
        distance = self.bot or self.bot.message
        duration = f'Translated in {distance.ws.latency * 990:.2f} ms'

        try:
            em = discord.Embed(color=self.mod_color)
            em.set_author(name='Available Languages:', icon_url=ctx.message.author.avatar_url),
            em.description = f'```bf\n{available}```'
            em.set_footer(text=duration, icon_url='https://i.imgur.com/yeHFKgl.png')

            if lang in conv:
                t = f'{translate(text, lang)}'
                e = discord.Embed(color=self.user_color)
                e.set_author(name=m, icon_url=ctx.message.author.avatar_url),
                e.add_field(name='Original1', value=f'*```css\n{text}```*', inline=False)
                e.add_field(name='Translation1', value=f'```css\n{t}```', inline=False)
                e.set_footer(text=duration, icon_url='https://i.imgur.com/yeHFKgl.png')
                try:
                    await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                except discord.Forbidden:  # FORBIDDEN (status code: 403): Missing Permissions
                    pass
                return await ctx.send(embed=e)

            lang = dict(zip(conv.values(), conv.keys())).get(lang.lower().title())
            if lang:
                tn = f'{translate(text, lang)}'
                em = discord.Embed(color=self.user_color)
                em.set_author(name=m, icon_url=ctx.message.author.avatar_url),
                em.add_field(name='Original Message', value=f'*```bf\n{text}```*', inline=False)
                em.add_field(name=f'Translation to {language}', value=tn, inline=False)
                em.set_footer(text=duration, icon_url='https://i.imgur.com/yeHFKgl.png')
                try:
                    await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                except discord.Forbidden:  # FORBIDDEN (status code: 403): Missing Permissions
                    pass
                await ctx.send(embed=em)

            else:
                await ctx.send(msg, delete_after=23)

        except discord.Forbidden:
            if lang in conv:
                trans = f'{ctx.message.author.mention} | *{translate(text, lang)}*'
                return await ctx.send(trans)

            lang = dict(zip(conv.values(), conv.keys())).get(lang.lower().title())
            if lang:
                trans = f'{ctx.message.author.mention} | *{translate(text, lang)}*'
                await ctx.send(trans)
                try:
                    await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
                except discord.Forbidden:  # FORBIDDEN (status code: 403): Missing Permissions
                    pass

            else:
                await ctx.send(msg, delete_after=23)
                try:
                    await ctx.message.add_reaction('\N{BLACK QUESTION MARK ORNAMENT}')
                except discord.Forbidden:  # FORBIDDEN (status code: 403): Missing Permissions
                    pass

    # +------------------------------------------------------------+
    # |                Translate plain text                        |
    # +------------------------------------------------------------+
    @commands.command(no_pm=True)
    async def t(self, ctx, language: str = None, *, text: str = None):
        """
        (∩｀-´)⊃━☆ﾟ.*･｡ﾟ translate some text
        """
        lang = language.title()
        available = ', '.join(conv.values())
        try:
            await ctx.message.delete()
            if lang in conv:
                t = f'{translate(text, lang)}'
                if (len(t) > 2000):
                    cropped = t[:2000]
                    await ctx.send(cropped, delete_after=360)
                else:
                    await ctx.send(t, delete_after=360)

            lang = dict(zip(conv.values(), conv.keys())).get(lang.lower().title())
            if lang:
                tn = f'{translate(text, lang)}'
                if (len(tn) > 2000):
                    cropped = tn[:2000]
                    await ctx.send(cropped, delete_after=360)
                else:
                    await ctx.send(tn, delete_after=360)
            else:
                return

        except discord.Forbidden:
            if lang in conv:
                trans = translate(text, lang)
                if (len(trans) > 2000):
                    cropped = trans[:2000]
                    return await ctx.send(cropped, delete_after=360)
                else:
                    return await ctx.send(trans, delete_after=360)

            lang = dict(zip(conv.values(), conv.keys())).get(lang.lower().title())
            if lang:
                trans = f'{ctx.message.author.mention} | *{translate(text, lang)}*'
                if (len(trans) > 2000):
                    cropped = trans[:2000]
                    await ctx.send(cropped, delete_after=360)
                else:
                    await ctx.send(trans, delete_after=360)

    # +------------------------------------------------------------+
    # |                   Available Langs                          |
    # +------------------------------------------------------------+
    @tr.command()
    async def langs(self, ctx):
        """ List of available languages """
        available = ', '.join(conv.values())
        foo = 'Full list in https://github.com/WebKide/modmail-plugins/translate/langs.json'

        em = discord.Embed(color=discord.Color.blue())
        em.set_author(name='Available Languages:', icon_url=ctx.message.author.avatar_url),
        em.description = f'```bf\n{available}```'
        em.set_footer(text=foo, icon_url='https://i.imgur.com/yeHFKgl.png')

        try:
            await ctx.send(embed=em, delete_after=420)

        except discord.Forbidden:
            msg = f'Available languages:\n```bf\n{available}```\n{foo}'
            await ctx.send(msg, delete_after=420)

    # +------------------------------------------------------------+
    # |              Translate Message with ID                     |
    # +------------------------------------------------------------+
    @commands.command(aliases=["tt"])
    async def translatetext(self, ctx, *, message):
        """
        Translates given messageID into English
        original command by officialpiyush
        """
        tmsg = self.translator.translate(message)
        em = discord.Embed()
        em.color = 4388013
        em.description = tmsg.text
        await ctx.channel.send(embed=em)

    # +------------------------------------------------------------+
    # |                 Auto Translate Text                        |
    # +------------------------------------------------------------+
    @commands.command(aliases=["att"])
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    async def auto_translate_thread(self, ctx):
        """ to be used inside ticket threads
        original command by officialpiyush
        """
        if "User ID:" not in ctx.channel.topic:
            await ctx.send("The Channel Is Not A Modmail Thread")
            return

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

        await ctx.send(f"{'Removed' if removed else 'Added'} Channel {'from' if removed else 'to'} Auto Translations List.")
    
    # +------------------------------------------------------------+
    # |              Toggle Auto Translate on/off                  |
    # +------------------------------------------------------------+
    @commands.command(aliases=["tat"])
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    async def toggle_auto_translations(self, ctx, enabled: bool):
        """ to be used inside ticket threads
        original command by officialpiyush
        """
        self.enabled = enabled
        await self.coll.update_one(
            {'_id': 'config'},
            {'$set': {'at-enabled': self.enabled}}, 
            upsert=True
            )
        await ctx.send(f"{'Enabled' if enabled else 'Disabled'} Auto Translations")
    
    async def on_message(self, message):
        if not self.enabled:
            return
        
        channel = message.channel

        if channel.id not in self.tt:
            return
        
        if isinstance(message.author,User):
            return
        
        if "User ID:" not in channel.topic:
            return
        
        if not message.embeds:
            return
        
        msg = message.embeds[0].description
        tmsg = self.translator.translate(msg)
        em = discord.Embed()
        em.description = tmsg.text
        em.color = 4388013
        em.footer = "Auto Translate Plugin"

        await channel.send(embed=em)


async def setup(bot):
    await bot.add_cog(Translate(bot))
