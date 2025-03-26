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

import discord
import random
import string
import time
import unicodedata2 as ud2

from discord.ext import commands
from collections import defaultdict

class Transform(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ this Discord.py Plugin provides various text transformation utilities.

    Key Features:
    - AI-powered word generation using Markov chains
    - Multiple text transformation (ᵗⁱⁿʸ, 𝒸𝓊𝓇𝓈𝒾𝓋ℯ, 𝕓𝕠𝕝𝕕, sᴍᴀʟʟ ᴄᴀᴘs, 1337 5P34K)
    - UNICODE character information display
    - Caesar cipher with optional shift (default: 3)
    - Smart binary converter with decoder
    - Fun text modifiers (👏, 🙏, Z͌͆a͠l̓g͊ő)
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
        vow = ['a', 'i', 'u', 'e', 'o', 'y', '', 'a', 'i', 'u', 'e', 'o', '']
        con = [
            'qu', 'w', 'wh', 'r', 't', 'th', 'y', 'p', 'mp', 's', 'ss', 'd', 
            'f', 'g', 'gü', 'ß', 'h', 'j', 'ji', 'k', '', 'l', 'z', 'x', 'c', 
            'v', 'b', 'n', 'm', ''
        ]
        
        for _ in range(999):
            word = f'{random.choice(vow)}{random.choice(con)}{random.choice(vow)}' \
                   f'{random.choice(vow)}{random.choice(con)}{random.choice(vow)}' \
                   f'{random.choice(con)}{random.choice(vow)}{random.choice(con)}'
            
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    pair = word[i:i+2]
                    next_letter = word[i+2]
                    self.transitions[pair][next_letter] += 1
        
        if not self.transitions:
            self.transitions['aa']['a'] = 1
            self.transitions['ab']['b'] = 1
            self.transitions['ba']['a'] = 1

    @commands.command(description='Command to generate random names', no_pm=True)
    async def aiword(self, ctx, count: int = 10, min_length: int = 4, max_length: int = 12):
        """Generate realistic-sounding artificial words
        
        Parameters:
        - count:      Number of words to generate (1-25)
        - min_length: Minimum word length (3-15)
        - max_length: Maximum word length (3-20)
        """
        # Validate parameters
        start_time = time.time()
        count = max(1, min(25, count))
        min_length = max(3, min(15, min_length))
        max_length = max(min_length, min(20, max_length))
        
        if not self.transitions:
            self.build_transitions()
            if not self.transitions:
                return await ctx.send("Failed to generate word patterns. Please try again later.")

        words = []
        for _ in range(count):
            word = self._generate_word(min_length, max_length)
            words.append(word.title())
        
        result_ai_words = ', '.join(words)
        em = discord.Embed(
            title="AI-Generated Words:",
            description=f'```\n{result_ai_words}```',
            color=self.user_color
        )
        em.set_footer(text=f"Generated {len(words)} words in {(time.time() - start_time) * 1000:.2f} ms")
        await ctx.send(embed=em)

    def _generate_word(self, min_len, max_len):
        """Generate a single ai_word using Markov chain"""
        word = ''
        vowel_start_pairs = [p for p in self.transitions.keys() if p[0] in 'aeiouy']
        pair = random.choice(vowel_start_pairs or list(self.transitions.keys()))
        word += pair
        
        while len(word) < max_len:
            try:
                next_letters = list(self.transitions[pair].keys())
                weights = list(self.transitions[pair].values())
                next_letter = random.choices(next_letters, weights=weights)[0]
                word += next_letter
                pair = pair[1] + next_letter
                
                if len(word) >= min_len and random.random() < (len(word) - min_len) / (max_len - min_len + 1):
                    break
            except:
                break
        
        if len(word) < min_len:
            word += random.choice('aeiouy')
        
        return word

    # +------------------------------------------------------------+
    # |                     CHARINFO                               |
    # +------------------------------------------------------------+
    @commands.command(description='Command to identify characters', no_pm=True)
    async def charinfo(self, ctx, *, characters: str):
        """Show Unicode character information"""
        start_time = time.time()

        if len(characters) > 15:
            return await ctx.send(f'Too many characters ({len(characters)}/15)')

        fmt = '`{2}` — `\\U{0:>08}`\n```tex\n\\N{{{1}}}```'
        
        def to_string(c):
            digit = format(ord(c), 'x')
            name = ud2.name(c, 'Name not found.')
            return fmt.format(digit, name, c)

        em = discord.Embed(color=self.user_color)
        em.description = '\n'.join(map(to_string, characters))
        em = await self._add_footer(em)
        await ctx.send(embed=em)

    # +------------------------------------------------------------+
    # |                     TEXT TRANSFORMERS                      |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command', no_pm=True)
    async def tiny(self, ctx, *, text: str):
        """Convert text to ᵗⁱⁿʸ letters"""
        start_time = time.time()

        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)

        char = "abcdefghijklmnopqrstuvwxyz0123456789+-+()."
        tran = "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖ٩ʳˢᵗᵘᵛʷˣʸᶻ₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎•"
        result = text.translate(str.maketrans(char, tran))
        
        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(description='Text transformer command', no_pm=True)
    async def cursive(self, ctx, *, text: str):
        """Convert text to 𝒸𝓊𝓇𝓈𝒾𝓋ℯ"""
        start_time = time.time()

        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)

        char = "abcdefghijklmnopqrstuvwxyz0123456789+-+()."
        tran = "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫+-+()."
        result = text.translate(str.maketrans(char, tran))
        
        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(description='Text transformer command', no_pm=True)
    async def bold(self, ctx, *, text: str):
        """Convert text to 𝕓𝕠𝕝𝕕"""
        start_time = time.time()

        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)

        char = "aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ0123456789+-+()."
        tran = "𝕒𝔸𝕓𝔹𝕔ℂ𝕕𝔻𝕖𝔼𝕗𝔽𝕘𝔾𝕙ℍ𝕚𝕀𝕛𝕁𝕜𝕂𝕝𝕃𝕞𝕄𝕟ℕ𝕠𝕆𝕡ℙ𝕢ℚ𝕣ℝ𝕤𝕊𝕥𝕋𝕦𝕌𝕧𝕍𝕨𝕎𝕩𝕏𝕪𝕐𝕫ℤ𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡+-+()."

        result = text.translate(str.maketrans(char, tran))
        
        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(description='Text transformer command', no_pm=True)
    async def smallcaps(self, ctx, *, text: str):
        """Convert text to sᴍᴀʟʟ ᴄᴀᴘs"""
        start_time = time.time()
        
        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)

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
        
        # Add processing time to footer
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        em.set_footer(text=f"Transformed in {processing_time:.2f} ms")
        
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                  NEW TRANSFORMERS 2025                     |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command', no_pm=True)
    async def mock(self, ctx, *, text: str):
        """Convert text to MoCkInG CaSe (alternating case)"""
        start_time = time.time()

        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)

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

    @commands.command(description='Text transformer command', no_pm=True)
    async def vapor(self, ctx, *, text: str):
        """Convert text to ＶＡＰＯＲＷＡＶＥ ＡＥＳＴＨＥＴＩＣ"""
        start_time = time.time()

        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)

        char = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        tran = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９"
        result = text.upper().translate(str.maketrans(char, tran))

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(description='Text transformer command', no_pm=True)
    async def binary(self, ctx, bits: int = 8, *, text: str = None):
        """Smart binary converter with format detection
        
        Usage:
        !binary Hello       → Text→binary
        !binary 01000001    → Binary→text
        !binary 16 Hello    → 16-bit encoding
        !binary 0b1010      → Handles prefix
        """
        start_time = time.time()

        if not text:
            return await ctx.send("Please provide text or binary.", delete_after=23)

        # Enhanced detection
        def is_binary(t):
            t = ''.join(t.split()).lower()
            if t.startswith(('0b', 'b''', '0x')):
                return True
            return all(c in '01' for c in t) and len(t) % 8 == 0

        try:
            if is_binary(text):
                # Binary→Text conversion
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
                # Text→Binary conversion
                result = ' '.join(format(ord(c), f'0{bits}b') for c in text)
                conversion_type = f"Text → Binary ({bits}-bit)"
        
        except Exception as e:
            return await ctx.send(f"Error: {str(e)}", delete_after=30)

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em.set_footer(text=f"Converted {conversion_type} in {self.bot.latency*1000:.2f}ms")
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(description='Text transformer command', no_pm=True)
    async def leet(self, ctx, *, text: str):
        """Convert text to 1337 5P34K"""
        start_time = time.time()

        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)

        char = "aAeElLoOtTsSgGbB"
        tran = "443311007755992288"
        result = text.translate(str.maketrans(char, tran))

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name='Result:', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(description='Text transformer command', no_pm=True)
    async def caesar(self, ctx, shift: int = 3, *, text: str):
        """Apply Caesar cipher with optional shift (default: 3)"""
        start_time = time.time()

        if not text:
            return await ctx.send("Please provide some text.", delete_after=23)

        result = []
        for c in text:
            if c.isupper():
                result.append(chr((ord(c) - 65 + shift) % 26 + 65))
            elif c.islower():
                result.append(chr((ord(c) - 97 + shift) % 26 + 97))
            else:
                result.append(c)
        result = ''.join(result)

        em = discord.Embed(color=self.user_color)
        em.add_field(name='Input:', value=f'```\n{text}```', inline=False)
        em.add_field(name=f'Result (shift={shift}):', value=f'```\n{result}```', inline=False)
        em = await self._add_footer(em)
        await ctx.send(embed=em, allowed_mentions=discord.AllowedMentions.none())

    # +------------------------------------------------------------+
    # |                     FUN COMMANDS                           |
    # +------------------------------------------------------------+
    @commands.command(description='Text transformer command', no_pm=True)
    async def clap(self, ctx, *, text: str = None):
        """Add 👏 between 👏 words 👏"""
        if text and len(text.split()) > 1:
            await ctx.send(text.replace(' ', ' 👏 '))
        else:
            await ctx.send('👏')

    @commands.command(description='Text transformer command', no_pm=True)
    async def pray(self, ctx, *, text: str = None):
        """Add 🙏 between 🙏 words 🙏"""
        if text and len(text.split()) > 1:
            await ctx.send(
                text.replace(' ', ' 🙏 '),
                allowed_mentions=discord.AllowedMentions.none()
            )
        else:
            await ctx.send('🙏')

    @commands.command(description='Text transformer command', no_pm=True)
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

async def setup(bot):
    await bot.add_cog(Transform(bot))
    
