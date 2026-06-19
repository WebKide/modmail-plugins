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

import discord, random, string, time, re
import unicodedata as ud2

from discord.ext import commands
from collections import defaultdict
from discord import ui


class NameGeneratorView(discord.ui.View):
    def __init__(self, parent_cog, ctx, count, min_length, max_length, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.parent_cog = parent_cog
        self.count = count
        self.min_length = min_length
        self.max_length = max_length

    async def send_new_embed(self, interaction: discord.Interaction):
        start_time = time.time()
        names = await self.parent_cog.generate_names(
            self.count, self.min_length, self.max_length
        )
        embed = discord.Embed(
            title="Fantasy Name Generator",
            description=f'```rb\n{", ".join(names)}```',
            color=self.ctx.author.colour
        )
        embed.set_footer(text=f"Generated {len(names)} names in {(time.time() - start_time) * 1000:.2f}ms")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Generate More", style=discord.ButtonStyle.green)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This button isn't for you!", ephemeral=True)
            return
        await self.send_new_embed(interaction)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This button isn't for you!", ephemeral=True)
            return
        await interaction.message.delete()
        self.stop()

class Transform(commands.Cog):
    """░ (∩｀-´)⊃━☆ﾟ.*･｡ﾟ this Discord.py Plugin provides various text transformation utilities

    Key Features:
    - AI-powered word generation using Markov chains
    - ASCII Banners group-command:
      - 2linesthick 
      - 3linedouble 
      - 3lineingle 
      - 3linethick 
      - 3linesthin 
    - Text transformers:
      - ᵗⁱⁿʸ, 𝒸𝓊𝓇𝓈𝒾𝓋ℯ, 𝕕𝕠𝕦𝕓𝕝𝕖-𝕤𝕥𝕣𝕦𝕔𝕜
      - 𝐁𝐨𝐥𝐝, 𝘽𝙤𝙡𝙙𝙄𝙩𝙖𝙡𝙞𝙘, 𝕲𝖔𝖙𝖍𝖎𝖈, 𝓘𝓽𝓪𝓵𝓲𝓬
      - sᴍᴀʟʟ ᴄᴀᴘs, 1337 5P34K, MoCkInG CaSe
      - ＶＡＰＯＲ, 𝖲𝖺𝗇𝗌-𝗌𝖾𝗋𝗂𝖿, Z͌͆a͠l̓g͊ő
    - UNICODE <--> Character
    - Caesar cipher with optional rotation `(default:13)`
    - Smart binary converter with encoder and decoder
    - Fun text modifiers (👏, 🙏)
    """
    def __init__(self, bot):
        self.bot = bot
        self.user_color = discord.Colour(0xed791d)  # Orange
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.build_transitions()

    async def _add_footer(self, em):
        """Add latency information to embed footer"""
        latency = self.bot.latency * 1000  # Convert to milliseconds
        duration = f'Transformed in {latency:.2f} ms'
        em.set_footer(text=duration)
        return em

    # +------------------------------------------------------------+
    # |                     WORD/NAME-GENERATOR                    |
    # +------------------------------------------------------------+
    def build_transitions(self):
        """Build Markov chain transitions for word generation"""
        # Vowel set with weights
        vow = ['a']*5 + ['e']*5 + ['i']*4 + ['o']*4 + ['u']*3 + ['y']*2
        
        # Consonant set with weights
        con = [
            'b', 'br', 'c', 'ch', 'd', 'dr', 'f', 'fr', 'g', 'gr',
            'h', 'j', 'k', 'kr', 'l', 'll', 'm', 'n', 'p', 'ph', 
            'qu', 'r', 's', 'sh', 't', 'th', 'tr', 'v', 'w', 'wh',
            'y', 'z', '', '', ''
        ]
        
        # Common vowel combinations
        vow_combos = [
            'ai', 'au', 'ea', 'ei', 'eo', 'ia', 'ie', 'io', 'iu',
            'oa', 'oe', 'oi', 'ou', 'ua', 'ue', 'ui', 'uo'
        ]
        
        # Generate training data
        for _ in range(999):
            # Syllable patterns
            patterns = [
                f'{random.choice(con)}{random.choice(vow)}',
                f'{random.choice(con)}{random.choice(vow_combos)}',
                f'{random.choice(vow)}{random.choice(con)}',
                f'{random.choice(vow_combos)}{random.choice(con)}'
            ]
            
            # Build word from 2-3 syllables
            syllables = random.randint(2, 3)
            word = ''.join([random.choice(patterns) for _ in range(syllables)])
            
            # Add to transitions if valid length
            if 3 <= len(word) <= 15:
                for i in range(len(word) - 2):
                    pair = word[i:i+2]
                    next_letter = word[i+2]
                    self.transitions[pair][next_letter] += 1
        
        # Fallback transitions if empty
        if not self.transitions:
            for pair in ['ar', 'el', 'is', 'th', 'qu']:
                self.transitions[pair]['a'] = 1

    def clean_name(self, name):
        """Clean up generated names to be more pronounceable"""
        # Remove triple letters
        for letter in 'aeiouybcdfghjklmnpqrstvwxyz':
            while letter*3 in name:
                name = name.replace(letter*3, letter*2)
        
        # Fix specific awkward clusters
        awkward = ['hfh', 'jc', 'zq', 'yy', 'ww', 'jh', 'uu', 'aa', 'zz', 'ii']
        for cluster in awkward:
            name = name.replace(cluster, cluster[0])
        
        # Remove double consonants at start
        if len(name) > 2 and name[0] == name[1] and name[0] in 'bcdfghjklmnpqrstvwxyz':
            name = name[1:]
        
        return name

    def generate_word(self, min_len=4, max_len=12):
        """Generate a single fantasy name using Markov chain"""
        word = ''
        # Start with a vowel or common starting pair
        starters = [p for p in self.transitions.keys() if p[0] in 'aeiouy' or p in ['th', 'sh', 'ch', 'qu']]
        pair = random.choice(starters or list(self.transitions.keys()))
        word += pair
        
        while len(word) < max_len:
            try:
                next_letters = list(self.transitions[pair].keys())
                weights = list(self.transitions[pair].values())
                next_letter = random.choices(next_letters, weights=weights)[0]
                word += next_letter
                pair = pair[1] + next_letter
                
                # Random chance to stop if we've reached min length
                if len(word) >= min_len and random.random() < 0.3:
                    break
            except:
                break
        
        # Ensure minimum length
        while len(word) < min_len:
            word += random.choice('aeiouy')
        
        return self.clean_name(word)

    async def generate_names(self, count=10, min_length=4, max_length=12):
        """Generate multiple fantasy names with optional endings"""
        # Validate parameters
        count = max(1, min(25, count))
        min_length = max(3, min(15, min_length))
        max_length = max(min_length, min(20, max_length))
        
        # Common fantasy suffixes
        suffixes = ['ion', 'ar', 'is', 'an', 'us', 'or', 'en', 'ith', 'ath', 'as', 'on']
        
        names = []
        for _ in range(count):
            name = self.generate_word(min_length, max_length)
            
            # 40% chance to add suffix if it fits
            if random.random() < 0.4 and len(name) < max_length - 2:
                suffix = random.choice(suffixes)
                if len(name) + len(suffix) <= max_length:
                    name += suffix
            
            names.append(name.title())
        
        return names

    @commands.command(description='Generate fantasy character names', aliases=['aiword', 'fantasynames'])
    @commands.guild_only()
    async def ainame(self, ctx, count: int = 10, min_length: int = 4, max_length: int = 12):
        """Generate fantasy names that sound authentic
        
        Parameters:
        - count: Number of names to generate (1-25)
        - min_length: Minimum name length (3-15)
        - max_length: Maximum name length (3-20)
        """
        start_time = time.time()
        names = await self.generate_names(count, min_length, max_length)
        
        embed = discord.Embed(
            title="Fantasy Name Generator",
            description=f'```rb\n{", ".join(names)}```',
            color=self.user_color
        )
        embed.set_footer(text=f"Generated {len(names)} names in {(time.time() - start_time)*1000:.2f}ms")
        view = NameGeneratorView(self, ctx, count, min_length, max_length)
        await ctx.send(embed=embed, view=view)

    # +------------------------------------------------------------+
    # |                   REGION COMMANDS                          |
    # +------------------------------------------------------------+
    @commands.group(name="banner", invoke_without_command=True)
    @commands.guild_only()
    async def banner_group(self, ctx):
        """Convert text to 3-line ASCII banners
        ```
        ▀█   █░░ █ █▄░█ █▀▀ █▀   ▀█▀ █░█ █ █▀▀ █▄▀
        █▄   █▄▄ █ █░▀█ ██▄ ▄█   ░█░ █▀█ █ █▄▄ █░█

        ┌─┐   ┬  ┬┌╮┌┌─┐   ╭─┐┬┌╮┌┌─┐┬  ┌─┐
         ─┤ ─ │  ││││├┤  ─ ╰─╮│││││ ┬│  ├┤ 
        └─┘   ┴─┘┴┘└┘└─┘   └─╯┴┘└┘└─┘┴─┘└─┘

        ┌─╮   ┬  ┬┌╮┌┌─┐   ┌┬┐┬ ┬┬┌╮┌
         ─┧   ╽  ╽╽╽╽┟┧     ╽ ┟─┧╽╽╽╽
        ┗━┛   ┻━┛┻┛┗┛┗━┛    ┻ ┻ ┻┻┛┗┛

        ╔═╗   ╦  ╦╔╗╦╔═╗   ╔╦╗╔═╗╦ ╦╔╗ ╦  ╔═╗
         ═╣ ═ ║  ║║║║╠═  ═  ║║║ ║║ ║╠╩╗║  ╠═ 
        ╚═╝   ╩═╝╩╝╚╝╚═╝   ═╩╝╚═╝╚═╝╚═╝╩═╝╚═╝

        ▀▀█░░█░░░░▀█▀░█▄░█░█▀▀▀░░▀▀█▀▀░█░░█░▀█▀░█▀▀▀░█░▄▀░
        ░▀█░░█░░░░░█░░█▒▀█░█▀▀░░░░░█░░░█▀▀█░░█░░█░░░░█▀▄░
        ▀▀▀░░▀▀▀▀░▀▀▀░▀░░▀░▀▀▀▀░░░░▀░░░▀░░▀░▀▀▀░▀▀▀▀░▀░▀▀░
        ```
        """
        await ctx.send_help(ctx.command)

    @banner_group.command(description="Generate 2-line-thick ASCII banners", name="2linesthick")
    @commands.guild_only()
    async def _banner_zero(self, ctx, *, text: str):
        """Convert text to 2-line ASCII banners
        ```
        ▀█   █░░ █ █▄░█ █▀▀ █▀   ▀█▀ █░█ █ █▀▀ █▄▀
        █▄   █▄▄ █ █░▀█ ██▄ ▄█   ░█░ █▀█ █ █▄▄ █░█
        ```
        """
        if not text:
            return await ctx.send("Please provide text to bannerize!", delete_after=23)
        start_time = time.time()

        # Define the 3-line font (uppercase only)
        font = {
            'A': ['▄▀█', '█▀█'],
            'B': ['█▄▄', '█▄█'],
            'C': ['█▀▀', '█▄▄'],
            'D': ['█▀▄', '█▄▀'],
            'E': ['█▀▀', '██▄'],
            'F': ['█▀▀', '█▀░'],
            'G': ['█▀▀', '█▄█'],
            'H': ['█░█', '█▀█'],
            'I': ['█', '█'],
            'J': ['░░█', '█▄█'],
            'K': ['█▄▀', '█░█'],
            'L': ['█░░', '█▄▄'],
            'M': ['█▀▄▀█', '█░▀░█'],
            'N': ['█▄░█', '█░▀█'],
            'O': ['█▀█', '█▄█'],
            'P': ['█▀█', '█▀▀'],
            'Q': ['█▀█', '▀▀█'],
            'R': ['█▀█', '█▀▄'],
            'S': ['█▀', '▄█'],
            'T': ['▀█▀', '░█░'],
            'U': ['█░█', '█▄█'],
            'V': ['█░█', '▀▄▀'],
            'W': ['█░█░█', '▀▄▀▄▀'],
            'X': ['▀▄▀', '█░█'],
            'Y': ['█▄█', '░█░'],
            'Z': ['▀▀█▀', '▄█▄▄'],
            '0': ['█▀█', '█▄█'],
            '1': ['▄█', '░█'],
            '2': ['▀█', '█▄'],
            '3': ['▀▀█', '▄██'],
            '4': ['█░█', '▀▀█'],
            '5': ['█▀░', '▄█░'],
            '6': ['█▄▄', '█▄█'],
            '7': ['▀▀█', '░░█'],
            '8': ['█▀█', '███'],
            '9': ['█▀█', '▀▀█'],
            '!': ['█░', '▄░'],
            '?': ['▀▀█', '░▄░'],
            ' ': [' ', ' '],
            '.': ['░░', '▄░'],
            '_': ['░░░░', '▄▄▄▄'],
            '+': ['░▄░', '▀█▀'],
            '=': ['▄▄', '▄▄'],
            }

        max_chars_per_line = 10
        banner_lines = []

        # Split input manually using '|' and then auto-wrap each segment
        user_lines = text.upper().split('|')

        for line in user_lines:
            for i in range(0, len(line), max_chars_per_line):
                chunk = line[i:i + max_chars_per_line]
                if not chunk:
                    continue

                line_block = ['', '']
                for char in chunk:
                    char_art = font.get(char, font[' '])
                    for j in range(2):
                        line_block[j] += char_art[j] + ' '  # add space between characters
                banner_lines.append('\n'.join(line_block))

        full_banner = '\n\n'.join(banner_lines)

        em = discord.Embed(color=self.user_color)
        em.add_field(name="Input:", value=f'```bf\n{text}\n```', inline=False)
        em.add_field(name="2-Line Banner:", value=f'```\n{full_banner}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                     BANNER 1                               |
    # +------------------------------------------------------------+
    @banner_group.command(description="Generate 3-single-line ASCII banners", name="3lineingle")
    @commands.guild_only()
    async def _banner_one(self, ctx, *, text: str):
        """Convert text to 3-single-line ASCII banners
        ```
        ┌─┐   ┬  ┬┌╮┌┌─┐   ╭─┐┬┌╮┌┌─┐┬  ┌─┐
         ─┤ ─ │  ││││├┤  ─ ╰─╮│││││ ┬│  ├┤ 
        └─┘   ┴─┘┴┘└┘└─┘   └─╯┴┘└┘└─┘┴─┘└─┘
        ```
        """
        if not text:
            return await ctx.send("Please provide text to bannerize!", delete_after=23)
        start_time = time.time()

        # Define the 3-line font (uppercase only)
        font = {
            'A': ['╭─╮', '├─┤', '┴ ┴'],
            'B': ['┌┐ ', '├┴┐', '└─┘'],
            'C': ['┌─┐', '│  ', '└─┘'],
            'D': ['┌─╮', '│ │', '┴─┘'],
            'E': ['┌─┐', '├┤ ', '└─┘'],
            'F': ['┌─┐', '├┤ ', '└  '],
            'G': ['┌─┐', '│ ┬', '└─┘'],
            'H': ['┬ ┬', '├─┤', '┴ ┴'],
            'I': ['┬', '│', '┴'],
            'J': [' ┬', '  ', ' └┘'],
            'K': ['┬┌─', '├┴┐', '┴ ┴'],
            'L': ['┬  ', '│  ', '┴─┘'],
            'M': ['┌┬┐', '│││', '┴ ┴'],
            'N': ['┌╮┌', '│││', '┘└┘'],
            'O': ['┌─┐', '│ │', '└─┘'],
            'P': ['┌─┐', '├─┘', '┴  '],
            'Q': ['┌─╮', '│╮│', '└┼┘'],
            'R': ['┬─╮', '├┬┘', '┴╰─'],
            'S': ['╭─┐', '╰─╮', '└─╯'],
            'T': ['┌┬┐', ' │ ', ' ┴ '],
            'U': ['┬ ┬', '│ │', '╰─╯'],
            'V': ['┬ ┬', '└┐│', ' └┘'],
            'W': ['┬ ┬', '│││', '└┴┘'],
            'X': ['┬ ┬', ' ╳ ', '┴ ┴'],
            'Y': ['┬ ┬', '└┬┘', ' ┴ '],
            'Z': ['──┐', '┌─┘', '└─┘'],
            '0': ['┌─┐', '│╱│', '└─┘'],
            '1': ['┌┐ ', ' │ ', '─┴─'],
            '2': ['┌─┐', '╭─┘', '└──'],
            '3': ['┌─┐', ' ─┤', '└─┘'],
            '4': ['┬ ┬', '└─┤', '  ┴'],
            '5': ['┌─┐', '└─╮', '└─┘'],
            '6': ['╭──', '├─┐', '└─┘'],
            '7': ['──┐', '  │', '  ┴'],
            '8': ['┌─┐', '├─┤', '└─┘'],
            '9': ['┌─┐', '└─┤', '──┘'],
            '!': ['┬', '│', '￮'],
            '?': ['┌─╮', ' ┌┘', ' ￮ '],
            ' ': ['   ', '   ', '   '],
            '-': ['   ', ' ─ ', '   '],
            '_': ['   ', '   ', '───'],
            '+': ['   ', '─┼─', '   '],
            '=': ['   ', '───', '───'],
            '.': ['  ', '  ', '￮ '],
        }

        # Convert text to uppercase and limit length
        text = text.upper()[:20]  # Prevent abuse with long text
        banner_lines = ['', '', '']  # Initialize 3 empty lines

        for char in text:
            # Get the character's ASCII art or default to space
            char_art = font.get(char, font[' '])
            for i in range(3):
                banner_lines[i] += char_art[i] #+ ' '  # Add spacing between chars

        # Combine into a single string
        banner = '\n'.join(banner_lines)
        
        em = discord.Embed(color=self.user_color)
        em.add_field(name="Input:", value=f'```bf\n{text}\n```', inline=False)
        em.add_field(name="3-Line Banner:", value=f'```\n{banner}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                     BANNER 2                               |
    # +------------------------------------------------------------+
    @banner_group.command(description="Generate 3-line-thin ASCII banners", name="3linethin")
    @commands.guild_only()
    async def _banner_two(self, ctx, *, text: str):
        """Convert text to 3-single-line ASCII banners
        ```
        ┌─╮   ┬  ┬┌╮┌┌─┐  ┌┬┐┬ ┬┬┌╮┌
         ─┧   ╽  ╽╽╽╽┟┧    ╽ ┟─┧╽╽╽╽
        ┗━┛   ┻━┛┻┛┗┛┗━┛   ┻ ┻ ┻┻┛┗┛
        ```
        """
        if not text:
            return await ctx.send("Please provide text to bannerize!", delete_after=23)
        start_time = time.time()

        # Define the 3-line font (uppercase only)
        font = {
            'A': ['╭─╮', '┟─┧', '┻ ┻'],
            'B': ['┌┐ ', '┟┴┒', '┗━┛'],
            'C': ['┌─┐', '╽  ', '┗━┛'],
            'D': ['┌─╮', '╽ ╽', '┻━┛'],
            'E': ['┌─┐', '┟┧ ', '┗━┛'],
            'F': ['┌─┐', '┟┧ ', '┗  '],
            'G': ['┌─┐', '╽ ┰', '┗━┛'],
            'H': ['┬ ┬', '┟─┧', '┻ ┻'],
            'I': ['┬', '╽', '┻'],
            'J': [' ┬', '  ', '┗┛'],
            'K': ['┬┌─', '┟┴┒', '┻ ┻'],
            'L': ['┬  ', '╽  ', '┻━┛'],
            'M': ['┌┬┐', '╽╽╽', '┻ ┻'],
            'N': ['┌╮┌', '╽╽╽', '┛┗┛'],
            'O': ['┌─┐', '╽ ╽', '┗━┛'],
            'P': ['┌─┐', '┟─┘', '┻  '],
            'Q': ['┌─╮', '╽┧╽', '┗╋┛'],
            'R': ['┬─╮', '┟┰┘', '┻┗━'],
            'S': ['╭─┐', '╰─┒', '┗━┛'],
            'T': ['┌┬┐', ' ╽ ', ' ┻ '],
            'U': ['┬ ┬', '╽ ╽', '┗━┛'],
            'V': ['┬ ┬', '└┒╽', ' ┗┛'],
            'W': ['┬ ┬', '╽╽╽', '┗┻┛'],
            'X': ['┬ ┬', ' ╳ ', '┻ ┻'],
            'Y': ['┬ ┬', '└┰┘', ' ┻ '],
            'Z': ['──┐', '┎─┘', '┗━┛'],
            '0': ['┌─┐', '╽╱╽', '┗━┛'],
            '1': ['┌┐ ', ' ╽ ', '━┻━'],
            '2': ['┌─╮', '┎─┘', '┗━━'],
            '3': ['┌─╮', ' ─┧', '┗━┛'],
            '4': ['┬ ┬', '└─┧', '  ┻'],
            '5': ['┌──', '└─┒', '┗━┛'],
            '6': ['╭──', '┟─┒', '┗━┛'],
            '7': ['──┐', '  ╽', '  ┻'],
            '8': ['┌─┐', '┟─┧', '┗━┛'],
            '9': ['┌─┐', '└─┧', '━━┛'],
            '!': ['┬', '╽', '●'],
            '?': ['┌─╮', ' ┎┘', ' ● '],
            ' ': ['   ', '   ', '   '],
            '-': ['   ', ' ━ ', '   '],
            '_': ['   ', '   ', '━━━'],
            '+': ['   ', '─╁─', '   '],
            '=': ['   ', '━━━', '━━━'],
            '.': ['  ', '  ', '● '],
        }

        # Convert text to uppercase and limit length
        text = text.upper()[:20]  # Prevent abuse with long text
        banner_lines = ['', '', '']  # Initialize 3 empty lines

        for char in text:
            # Get the character's ASCII art or default to space
            char_art = font.get(char, font[' '])
            for i in range(3):
                banner_lines[i] += char_art[i] #+ ' '  # Add spacing between chars

        # Combine into a single string
        banner = '\n'.join(banner_lines)
        
        em = discord.Embed(color=self.user_color)
        em.add_field(name="Input:", value=f'```bf\n{text}\n```', inline=False)
        em.add_field(name="3-Single-Line Banner:", value=f'```\n{banner}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                     BANNER 3                               |
    # +------------------------------------------------------------+
    @banner_group.command(description="Generate 3-double-line ASCII banners", name="3linedouble")
    @commands.guild_only()
    async def _banner_three(self, ctx, *, text: str):
        """Convert text to 3-double-line ASCII banners
        ```
        ╔═╗   ╦  ╦╔╗╦╔═╗   ╔╦╗╔═╗╦ ╦╔╗ ╦  ╔═╗
         ═╣ ═ ║  ║║║║╠═  ═  ║║║ ║║ ║╠╩╗║  ╠═ 
        ╚═╝   ╩═╝╩╝╚╝╚═╝   ═╩╝╚═╝╚═╝╚═╝╩═╝╚═╝
        ```
        """
        if not text:
            return await ctx.send("Please provide text to bannerize!", delete_after=23)
        start_time = time.time()

        # Define the 3-line font (uppercase only)
        font = {
            'A': ['╔═╗', '╠═╣', '╩ ╩'],
            'B': ['╔╗ ', '╠╩╗', '╚═╝'],
            'C': ['╔═╗', '║  ', '╚═╝'],
            'D': ['╔╦╗', ' ║║', '═╩╝'],
            'E': ['╔═╗', '╠═ ', '╚═╝'],
            'F': ['╔═╗', '╠═ ', '╩  '],
            'G': ['╔═╗', '║ ╦', '╚═╝'],
            'H': ['╦ ╦', '╠═╣', '╩ ╩'],
            'I': ['╦', '║', '╩'],
            'J': [' ╦', ' ║', '╚╝'],
            'K': ['╦╔═', '╠╩╗', '╩ ╩'],
            'L': ['╦  ', '║  ', '╩═╝'],
            'M': ['╔╦╗', '║║║', '╩ ╩'],
            'N': ['╔╗╦', '║║║', '╝╚╝'],
            'O': ['╔═╗', '║ ║', '╚═╝'],
            'P': ['╔═╗', '╠═╝', '╩  '],
            'Q': ['╔═╗', '║║║', '╚╬╝'],
            'R': ['╔═╗', '╠《 ', '╩ ╚'],
            'S': ['╔═╗', '╚═╗', '╚═╝'],
            'T': ['╔╦╗', ' ║ ', ' ╩ '],
            'U': ['╦ ╦', '║ ║', '╚═╝'],
            'V': ['╦ ╦', '╚╗║', ' ╚╝'],
            'W': ['╦ ╦', '║║║', '╚╩╝'],
            'X': ['╦ ╦', '╚╬╗', '╩ ╩'],
            'Y': ['╦ ╦', '╚╦╝', ' ╩ '],
            'Z': ['╔═╗', '╔═╝', '╚═╝'],
            '0': ['╔═╗', '║╱║', '╚═╝'],
            '1': [' ╔╗', '  ║', '  ╩'],
            '2': ['╔═╗', '╔═╝', '╚═╝'],
            '3': ['╔═╗', ' ═╣', '╚═╝'],
            '4': ['╦ ╦', '╚═╣', '  ╩'],
            '5': ['╔═╗', '╚═╗', '╚═╝'],
            '6': ['╔══', '╠═╗', '╚═╝'],
            '7': ['══╗', '  ║', '  ╩'],
            '8': ['╔═╗', '╠═╣', '╚═╝'],
            '9': ['╔═╗', '╚═╣', '══╝'],
            '!': ['╦', '║', '○'],
            '?': ['╔═╗', ' ╔╝', ' ○ '],
            ' ': ['   ', '   ', '   '],
            '-': ['   ', ' ═ ', '   '],
            '_': ['   ', '   ', '═══'],
            '+': ['   ', '═╬═', '   '],
            '=': ['   ', '═══', '═══'],
            '.': ['  ', '  ', '○ '],
        }

        # Convert text to uppercase and limit length
        text = text.upper()[:20]  # Prevent abuse with long text
        banner_lines = ['', '', '']  # Initialize 3 empty lines

        for char in text:
            # Get the character's ASCII art or default to space
            char_art = font.get(char, font[' '])
            for i in range(3):
                banner_lines[i] += char_art[i] #+ ' '  # Add spacing between chars

        # Combine into a single string
        banner = '\n'.join(banner_lines)
        
        em = discord.Embed(color=self.user_color)
        em.add_field(name="Input:", value=f'```bf\n{text}\n```', inline=False)
        em.add_field(name="3-Double-Line Banner:", value=f'```\n{banner}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                     BANNER 4                               |
    # +------------------------------------------------------------+
    @banner_group.command(description="Generate 3-line-thick ASCII banners", name="3linethick")
    @commands.guild_only()
    async def _banner_four(self, ctx, *, text: str):
        """Convert text to 3-double-line ASCII banners
        ```
        ▀▀█░░█░░░░▀█▀░█▄░█░█▀▀▀░▀▀█▀▀░█░░█░▀█▀░█▀▀▀░█░▄▀░
        ░▀█░░█░░░░░█░░█▒▀█░█▀▀░░░░█░░░█▀▀█░░█░░█░░░░█▀▄░
        ▀▀▀░░▀▀▀▀░▀▀▀░▀░░▀░▀▀▀▀░░░▀░░░▀░░▀░▀▀▀░▀▀▀▀░▀░▀▀░
        ```
        Convert text to 3-double-line ASCII banners with auto-wrap and manual breaks using '|'
        Example:
        !banner 3linethick hello|world
        """
        if not text:
            return await ctx.send("Please provide text to bannerize!", delete_after=23)
        start_time = time.time()

        # Define the 3-line font (uppercase only)  # 'N': ['█▀▀▄', '█░░█', '▀░░▀'],
        font = {
            'A': ['█▀▀█░', '█▄▄█░', '▀░░▀░'],
            'B': ['█▀▀▄░', '█▀▀▄░', '▀▀▀░░'],
            'C': ['█▀▀▀░', '█░░░░', '▀▀▀▀░'],
            'D': ['█▀▀▄░', '█░░█░', '▀▀▀░░'],
            'E': ['█▀▀▀░', '█▀▀░░', '▀▀▀▀░'],
            'F': ['█▀▀▀░', '█▀▀░░', '▀░░░░'],
            'G': ['█▀▀▀░', '█░▀█░', '▀▀▀▀░'],
            'H': ['█░░█░', '█▀▀█░', '▀░░▀░'],
            'I': ['▀█▀░', '░█░░', '▀▀▀░'],
            'J': ['░░▀░', '░░█░', '█▄█░'],
            'K': ['█░▄▀░', '█▀▄░', '▀░▀▀░'],
            'L': ['█░░░░', '█░░░░', '▀▀▀▀░'],
            'M': ['█▀▄▀█░', '█░▀░█░', '▀░░░▀░'],
            'N': ['█▄░█░', '█▒▀█░', '▀░░▀░'],
            'O': ['█▀▀█░', '█░░█░', '▀▀▀▀░'],
            'P': ['█▀▀█░', '█░░█░', '█▀▀▀░'],
            'Q': ['█▀▀█░', '█░░█░', '▀▀█▄░'],
            'R': ['█▀▀█░', '█▄▄▀░', '▀░▀▀░'],
            'S': ['█▀▀░', '▀▀█░', '▀▀▀░'],
            'T': ['▀▀█▀▀░', '░░█░░░', '░░▀░░░'],
            'U': ['█░░█░', '█░░█░', '░▀▀▀░'],
            'V': ['▀█░█░', '░█▄█░', '░░▀░░'],
            'W': ['█░░░█░', '█▄█▄█░', '░▀░▀░░'],
            'X': ['▀█░█░░', '░▄▀▄░░', '░▀░▀▀░'],
            'Y': ['▀█░█░', '░█▄█░', '░▄▄█░'],
            'Z': ['▀▀█░', '▄▀░░', '▀▀▀░'],
            '0': ['▄▀▀█░', '█░░█░', '▀▀▀░░'],
            '1': ['▀█░░', '░█░░', '▄█▄░'],
            '2': ['▀▀▄░', '▄▀░░', '▀▀▀░'],
            '3': ['▀▀█░', '░▀█░', '▀▀▀░'],
            '4': ['█░▄░', '▀▀█░', '░░▀░'],
            '5': ['█▀▀▀░', '▀▀▀▄░', '▀▀▀░░'],
            '6': ['█▀▀░', '█▀█░', '▀▀▀░'],
            '7': ['▀▀█░', '░▀█░', '░░▀░'],
            '8': ['▄▀▀▄░', '▄▀▀▄░', '▀▀▀░░'],
            '9': ['█▀█░', '▀▀█░', '░░▀░'],
            '!': ['█░', '█░', '▄░'],
            '?': ['▀▀█░', '░█░░', '░▄░░'],
            ' ': ['░', '░', '░'],
            '-': ['░░░', '▀▀░', '░░░'],
            '+': ['░▄░░', '▀█▀░', '░░░░'],
            '=': ['▄▄░', '▄▄░', '░░░'],
            '.': ['░░', '░░', '▀░'],
        }

        max_chars_per_line = 8
        banner_lines = []  # Will hold groups of 3-line outputs

        # Preprocess: manual split with '|', then auto-wrap each line
        user_lines = text.upper().split('|')

        for line in user_lines:
            # Auto-wrap long lines into chunks of max_chars_per_line
            for i in range(0, len(line), max_chars_per_line):
                chunk = line[i:i + max_chars_per_line]
                if not chunk:
                    continue

                line_block = ['', '', '']
                for char in chunk:
                    char_art = font.get(char, font[' '])
                    for j in range(3):
                        line_block[j] += char_art[j]
                banner_lines.append('\n'.join(line_block))

        full_banner = '\n\n'.join(banner_lines)

        em = discord.Embed(color=self.user_color)
        em.add_field(name="Input:", value=f'```bf\n{text}\n```', inline=False)
        em.add_field(name="3-Double-Line Banner:", value=f'```\n{full_banner}```', inline=False)
        em = await self._add_footer(em)

        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                     CHARINFO                               |
    # +------------------------------------------------------------+
    @commands.command(description='Command to identify characters', aliases=['charingo', 'char'])
    @commands.guild_only()
    async def charinfo(self, ctx, *, characters: str = None):
        """Transform 𝐔𝐧𝐢𝐜𝐨𝐝𝐞 <--> 𝐂𝐡𝐚𝐫𝐚𝐜𝐭𝐞𝐫
        
        - Show info about unicode characters:
          - Character `@` to `\\U0040`
        - Convert unicode escapes to character:
          - `\\U0040` to character `@`
          - `\\N{{WHITE HEAVY CHECK MARK}}` to `✅`
        """
        if not characters:
            return await ctx.send_help(self.charinfo)

        start_time = time.time()
        characters = characters.strip()

        # Detect mode: unicode escape to char if starts with "\"
        if characters.startswith("\\"):
            pattern = re.compile(
                r'(\\N\{[^}]+\})|(\\U\+?[0-9a-fA-F]+)|(\\u[0-9a-fA-F]{4})|(0x[0-9a-fA-F]+)|(\\[0-9a-fA-F]+)'
            )
            matches = pattern.findall(characters)
            results = []

            for match in matches:
                token = next(filter(None, match))  # get the non-empty group

                try:
                    if token.startswith("\\N{"):
                        # Handle \N{name}
                        name = token[3:-1]  # Strip \N{ and }
                        char = ud2.lookup(name)
                        results.append(f"# `{token}` → `{char}`")
                    else:
                        # Normalise and decode hex
                        code = token.upper().lstrip('\\U').lstrip('u').lstrip('+').lstrip('0X').lstrip('\\')
                        char = chr(int(code, 16))
                        results.append(f"# `{token}` → `{char}`")
                except Exception as e:
                    results.append(f"`{token}` → ❌ Invalid code")

            em = discord.Embed(title="Transform", description='\n'.join(results), color=self.user_color)
            em.set_author(name="Unicode → Character", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
            em = await self._add_footer(em)
            return await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

        # Character to Unicode info
        if len(characters) > 15:
            return await ctx.send(f'Too many characters ({len(characters)}/15)', delete_after=9)

        fmt = '# `{2}` — `\\U{0:>08}`\n```tex\n\\N{{{1}}}```'

        def to_string(c):
            digit = format(ord(c), 'X')
            name = ud2.name(c, 'Name not found.')
            return fmt.format(ord(c), name, c)

        em = discord.Embed(title="Transform", description='\n'.join(map(to_string, characters)), color=self.user_color)
        em.set_author(name="Character → Unicode Info", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                     TEXT TRANSFORMERS                      |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def tiny(self, ctx, *, text: str):
        """Convert text to ᵗⁱⁿʸ letters"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        char = "abcdefghijklmnopqrstuvwxyz0123456789+-+()."
        tran = "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖ٩ʳˢᵗᵘᵛʷˣʸᶻ₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎•"
        result = text.translate(str.maketrans(char, tran))
        
        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  CURSIVE FONT                              |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def cursive(self, ctx, *, text: str):
        """Convert text to 𝒸𝓊𝓇𝓈𝒾𝓋ℯ"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        char = "abcdefghijklmnopqrstuvwxyz0123456789+-+()."
        tran = "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫+-+()."
        result = text.translate(str.maketrans(char, tran))
        
        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  SMALL CAPS FONT                           |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def smallcaps(self, ctx, *, text: str):
        """Convert text to sᴍᴀʟʟ ᴄᴀᴘs"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        alpha = list(string.ascii_lowercase)
        converter = ['ᴀ', 'ʙ', 'ᴄ', 'ᴅ', 'ᴇ', 'ꜰ', 'ɢ', 'ʜ', 'ɪ', 'ᴊ', 'ᴋ', 'ʟ', 
                    'ᴍ', 'ɴ', 'ᴏ', 'ᴘ', 'ǫ', 'ʀ', 'ꜱ', 'ᴛ', 'ᴜ', 'ᴠ', 'ᴡ', 'x', 'ʏ', 'ᴢ']
        result = []
        
        for letter in text.lower():
            if letter in alpha:
                result.append(converter[alpha.index(letter)])
            else:
                result.append(letter)
        
        result_text = ''.join(result)
        
        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result_text}```', inline=False)
        em = await self._add_footer(em)
        
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  MOCK CASE TRANSFORMER                     |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def mock(self, ctx, *, text: str):
        """Convert text to MoCkInG CaSe (alternating case)"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        result = []
        should_upper = random.choice([True, False])  # Random starting case
        for char in text:
            if char.isalpha():  # Only alter letters
                result.append(char.upper() if should_upper else char.lower())
                should_upper = not should_upper  # Flip case for next letter
            else:
                result.append(char)  # Leave spaces/symbols untouched

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{"".join(result)}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em)

    # +------------------------------------------------------------+
    # |                  A E S T H E T I C S                       |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def vapor(self, ctx, *, text: str):
        """Convert text to ＶＡＰＯＲＷＡＶＥ ＡＥＳＴＨＥＴＩＣ"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        char = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        tran = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９"
        result = text.upper().translate(str.maketrans(char, tran))

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  SANS SERIF FONT                           |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def sans(self, ctx, *, text: str):
        """Convert text to 𝖲𝖺𝗇𝗌-𝗌𝖾𝗋𝗂𝖿"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        char = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        tran = "𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓"

        # Precomposed transliteration characters → ASCII base
        translit_map = str.maketrans({
            "ḍ": "d", "Ḍ": "D", "ḥ": "h", "Ḥ": "H", "ḣ": "h", "Ḣ": "H", "ṁ": "m", 
            "Ṁ": "M", "ḷ": "l", "Ḷ": "L", "ṇ": "n", "Ṇ": "N", "ṅ": "n", "Ṅ": "N", 
            "ṛ": "r", "Ṛ": "R", "ś": "s", "Ś": "S", "ṣ": "s", "Ṣ": "S", "ṭ": "t", 
            "Ṭ": "T", "ā": "a", "Ā": "A", "ū": "u", "Ū": "U", "ī": "i", "Ī": "I", 
            "ñ": "n", "Ñ": "N", "ç": "c", "Ç": "C", "á": "a", "à": "a", "â": "a", 
            "ã": "a", "ä": "a", "Á": "A", "À": "A", "Â": "A", "Ã": "A", "Ä": "A", 
            "é": "e", "è": "e", "ê": "e", "ë": "e", "É": "E", "È": "E", "Ê": "E", 
            "Ë": "E", "í": "i", "ì": "i", "î": "i", "ï": "i", "Í": "I", "Ì": "I", 
            "Î": "I", "Ï": "I", "ó": "o", "ò": "o", "ô": "o", "õ": "o", "ö": "o", 
            "Ó": "O", "Ò": "O", "Ô": "O", "Õ": "O", "Ö": "O", "ú": "u", "ù": "u", 
            "û": "u", "ü": "u", "Ú": "U", "Ù": "U", "Û": "U", "Ü": "U", "ý": "y", 
            "ÿ": "y", "Ý": "Y", "Ÿ": "Y", "ø": "o", "Ø": "O", "å": "a", "Å": "A",
        })

        def strip_diacritics(t):
            return ''.join(
                c for c in unicodedata.normalize('NFD', t)
                if unicodedata.category(c) != 'Mn'
            )

        # Apply transliteration, then strip remaining diacritics, then style
        cleaned = strip_diacritics(t.translate(translit_map))
        result = cleaned.translate(str.maketrans(char, tran))

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  DOUBLE-STRUCK (BLACKBOARD BOLD) FONT      |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def double(self, ctx, *, text: str):
        """Convert text to 𝕕𝕠𝕦𝕓𝕝𝕖-𝕤𝕥𝕣𝕦𝕔𝕜"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        # Create translation tables for lowercase and uppercase
        lower_char = "abcdefghijklmnopqrstuvwxyz0123456789"
        lower_tran = "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡"
        
        upper_char = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        upper_tran = "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"
        
        # Create combined translation table
        combined_char = lower_char + upper_char
        combined_tran = lower_tran + upper_tran
        
        # Handle brackets separately since they appear in both cases
        bracket_map = {
            '[': '〚',
            ']': '〛',
            '(': '〘',
            ')': '〙',
            '<': '《',
            '>': '》'
        }
        
        # Translate character by character to handle case properly
        result = []
        for char in text:
            if char in bracket_map:
                result.append(bracket_map[char])
            elif char in combined_char:
                result.append(combined_tran[combined_char.index(char)])
            else:
                result.append(char)
        
        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{"".join(result)}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  BOLD FONT                                 |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def bold(self, ctx, *, text: str):
        """Convert text to 𝐁𝐨𝐥𝐝"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        char = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"
        tran = "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗𝟎"
        # result = text.upper().translate(str.maketrans(char, tran))
        result = text.translate(str.maketrans(char, tran))

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  BOLDITALIC FONT                           |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def bolditalic(self, ctx, *, text: str):
        """Convert text to 𝘽𝙤𝙡𝙙𝙄𝙩𝙖𝙡𝙞𝙘"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        char = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        tran = "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯"
        # result = text.upper().translate(str.maketrans(char, tran))
        result = text.translate(str.maketrans(char, tran))

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                     ITALIC FONT                            |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def italic(self, ctx, *, text: str):
        """Convert text to 𝓘𝓽𝓪𝓵𝓲𝓬"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        char = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        tran = "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃"
        # result = text.upper().translate(str.maketrans(char, tran))
        result = text.translate(str.maketrans(char, tran))

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                     GOTHIC FONT                            |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def gothic(self, ctx, *, text: str):
        """Convert text to 𝕲𝖔𝖙𝖍𝖎𝖈"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)
        start_time = time.time()

        char = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        tran = "𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟"
        # result = text.upper().translate(str.maketrans(char, tran))
        result = text.translate(str.maketrans(char, tran))

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  BINARY ENCODER/DECODER                    |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def binary(self, ctx, bits: int = 8, *, text: str = None):
        """Smart binary converter with format detection
        
        Usage:
        !binary Hello       → Text → binary
        !binary 01000001    → Binary → text
        !binary 16 Hello    → 16-bit encoding
        """
        if text is None:
            # If no text was provided, and only one argument was passed, treat bits as text
            if bits in (8, 16, 32):  # legit bit values
                return await ctx.send_help(self.binary)
            else:
                text = str(bits)
                bits = 8  # fallback to default

        if bits not in (8, 16, 32):
            return await ctx.send("Please specify a valid bit size: 8, 16, or 32.")

        # Enhanced detection
        start_time = time.time()
        def is_binary(t):
            t = ''.join(t.split()).lower()
            if t.startswith(('0b', 'b''', '0x')):
                return True
            return all(c in '01' for c in t) and len(t) % 8 == 0

        try:
            if is_binary(text):
                # Binary → Text
                clean = text.replace(' ', '').lower()
                if clean.startswith('0b'):
                    clean = clean[2:]
                elif clean.startswith('0x'):
                    result = bytes.fromhex(clean[2:]).decode('utf-8')
                else:
                    result = ''.join(chr(int(clean[i:i+8], 2)) 
                              for i in range(0, len(clean), 8))
                conversion_type = "Binary → Text"
            else:
                # Text → Binary
                result = ' '.join(format(ord(c), f'0{bits}b') for c in text)
                conversion_type = f"Text → Binary ({bits}-bit)"
        
        except Exception as e:
            return await ctx.send(f"Error: {str(e)}", delete_after=130)

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```cs\n{result}```', inline=False)
        em.set_footer(text=f"{conversion_type} | {self.bot.latency*1000:.2f}ms")
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  LEET FONT TRANSFORMER                     |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def leet(self, ctx, *, text: str):
        """Convert text to 1337 5P34K"""
        if not text:
            return await ctx.send_help(self.leet)
        start_time = time.time()

        char = "abcdefghijklmnopqrstuvwxyz0123456789+-()."
        tran = "4b<D3ƒ6#!JK1M^0PQЯ57UVωXY20123456789+-「」･"
        result = text.translate(str.maketrans(char, tran))

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  CAESAR ROTATE CIPHER                      |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command', aliases=['rot', 'rotate'])
    @commands.guild_only()
    async def caesar(self, ctx, *, message: str):
        """Apply Caesar cipher with optional rot `(default: 13)`
        
        - `rot:` Rotation amount (1–25).
          - Values outside this range will wrap using modulo 26.
        - `text:` Text message to encode or decode.
        """
        start_time = time.time()
        args_split = message.strip().split()
        rot = 13  # default
        text = message
        # Try parsing first token as int
        if args_split:
            try:
                parsed_rot = int(args_split[0])
                if 1 <= parsed_rot <= 25:
                    rot = parsed_rot
                    text = ' '.join(args_split[1:])  # rest is the actual text
            except ValueError:
                pass  # No valid rotation given, use default 13

        if not text:
            return await ctx.send_help(self.caesar)

        original_rot = rot
        rot %= 26
        result = []
        for c in text:
            if c.isupper():
                result.append(chr((ord(c) - 65 + rot) % 26 + 65))
            elif c.islower():
                result.append(chr((ord(c) - 97 + rot) % 26 + 97))
            else:
                result.append(c)

        transformed = ''.join(result)
        msg_block = f"```bf\n{transformed[:1024]}```"

        em = discord.Embed(
            title="🔐 Caesar Cipher",
            description=f"Caesar cipher applied with `rot={rot}`",
            color=self.user_color
        )
        em.add_field(name="Input:", value=f"```\n{text[:1024]}```", inline=False)
        em.add_field(name="Result:", value=msg_block, inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  ZALGO FONT                                |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def zalgo(self, ctx, *, text: str = None):
        """Z͆͌̓̑͗̀a͒͠l̓͌̾̀̚g͊͝o͋̑̿͝ your text"""
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)

        marks = [chr(c) for c in range(768, 879)]
        result = []
        
        for word in text.replace('@', '')[:100].split():
            zalgo_word = []
            for i, char in enumerate(word):
                zalgo_word.append(char)
                if char.isalnum():
                    zalgo_word.extend(random.choice(marks) for _ in range(i//2 + 1))
            result.append(''.join(zalgo_word))
        
        await ctx.send(' '.join(result))

    # +------------------------------------------------------------+
    # |                     FUN COMMANDS                           |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def clap(self, ctx, *, text: str = None):
        """Add 👏 between 👏 words 👏"""
        if text and len(text.split()) > 1:
            await ctx.send(
                text.replace(' ', ' 👏 '),
                allowed_mentions=discord.AllowedMentions.none()
            )
        else:
            await ctx.send('👏')

    @commands.command(description='Text transformer command')
    @commands.guild_only()
    async def pray(self, ctx, *, text: str = None):
        """Add 🙏 between 🙏 words 🙏"""
        if text and len(text.split()) > 1:
            await ctx.send(
                text.replace(' ', ' 🙏 '),
                allowed_mentions=discord.AllowedMentions.none()
            )
        else:
            await ctx.send('🙏')

async def setup(bot):
    await bot.add_cog(Transform(bot))
