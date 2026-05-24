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

import random
from datetime import datetime
from pathlib import Path

import discord
from discord.ext import commands

from .asitiscore import (
    BG_CHAPTER_INFO,
    create_verse_embed,
    validate_verse,
)
from .asitisnav import (
    NavigationButtons,
    PurportView,
)

__version__ = "v3.0 asitis.py — Modmail plugin entry point"

class AsItIs(commands.Cog):
    """Bhagavad Gītā As It Is* — Original 1972 Macmillan edition
    ```
    █▀▀█░█▀▀░░░▀█▀░▀▀█▀▀░░░▀█▀░█▀▀
    █▄▄█░▀▀█░░░░█░░░░█░░░░░░█░░▀▀█
    ▀░░▀░▀▀▀░░░▀▀▀░░░▀░░░░░▀▀▀░▀▀▀```

    To ŚRĪLA BALADEVA VIDYĀBHŪṢAṆA who presented so nicely the
    “Govinda-bhāṣya” commentary on Vedānta philosophy.

    - Usage: `!bg <chapter> <verse>`  e.g.  `!bg 2 13`  or  `!bg 17 8-10`

    - No other philosophical or religious work reveals, in such a lucid and
      profound way, the nature of consciousness, the self, the universe and
      the Supreme.
    - Bhagavad Gītā As It Is is the largest-selling, most widely used
      edition of the Gītā in the world.
    """

    def __init__(self, bot: commands.Bot):
        self.bot            = bot
        self.data_path      = Path(__file__).parent / "gita"
        self._chapter_cache: dict = {}   # shared with NavigationButtons / PurportView via self

    # ╔════════════════════╦══════════════╦════════════════════════╗
    # ╠════════════════════╣ GITA COMMAND ╠════════════════════════╣
    # ╚════════════════════╩══════════════╩════════════════════════╝

    @commands.command(name='asitis', aliases=['1972', 'bg'])
    @commands.guild_only()
    async def gita_verse(self, ctx: commands.Context, chapter: int, verse: str):
        """Bhagavad Gītā — As It Is (Original 1972 Macmillan edition)

        To ŚRĪLA BALADEVA VIDYĀBHŪṢAṆA who presented so nicely the
        “Govinda-bhāṣya” commentary on Vedānta philosophy.

        **Usage:** `!bg <chapter> <verse>`  e.g.  `!bg 2 13`  or  `!bg 17 8-10`
        """
        start_time = datetime.now()

        # ╔════════════════════╦═══════════════════╦═══════════════════╗
        # ╠════════════════════╣ 1. Validate input ╠═══════════════════╣
        # ╚════════════════════╩═══════════════════╩═══════════════════╝
        is_valid, verse_ref = validate_verse(chapter, verse)
        if not is_valid:
            return await ctx.send(f"🚫 {verse_ref}", delete_after=9)

        # ╔════════════════════╦════════════════╦══════════════════════╗
        # ╠════════════════════╣ 2. Build embed ╠══════════════════════╣
        # ╚════════════════════╩════════════════╩══════════════════════╝
        try:
            embed = create_verse_embed(
                self.data_path, self._chapter_cache,
                chapter, verse_ref,
                display_name=ctx.author.display_name,
            )
            # Append retrieval latency to footer
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            embed.set_footer(
                text=f"{embed.footer.text} ➜ 𝗋𝖾𝗍𝗋𝗂𝖾𝗏𝖾𝖽 𝗂𝗇 {latency_ms:.1f} 𝗆𝗌",
                icon_url=embed.footer.icon_url,
            )

            # ╔═══════════╦════════════════════════════════════╦═══════════╗
            # ╠═══════════╣ 3. Attach navigation view and send ╠═══════════╣
            # ╚═══════════╩════════════════════════════════════╩═══════════╝
            view         = NavigationButtons(self, chapter, verse_ref, ctx)
            message      = await ctx.send(embed=embed, view=view)
            view.message = message

        except FileNotFoundError as e:
            await ctx.send(f"🚫 {e}", delete_after=90)
        except ValueError as e:
            await ctx.send(f"🚫 Error in verse data:\n\n{e}", delete_after=90)
        except Exception as e:
            await ctx.send(f"🚫 Unexpected error retrieving verse:\n\n{e}", delete_after=90)

    # ╔════════════════════╦══════════════╦════════════════════════╗
    # ╠════════════════════╣ GITAS WISDOM ╠════════════════════════╣
    # ╚════════════════════╩══════════════╩════════════════════════╝

    @commands.command(name='wisdom', description="Inspiration from the Bhagavad Gītā")
    @commands.guild_only()
    async def _wisdom(self, ctx: commands.Context):
        """Bhagavad Gītā’s wisdom, find inspiration reading a verse that was chosen just for you."""
        start_time = datetime.now()

        # 1. Select a completely random chapter and valid verse index
        chapter   = random.choice(list(BG_CHAPTER_INFO.keys()))
        total     = BG_CHAPTER_INFO[chapter]['total_verses']
        verse_num = random.randint(1, total)

        is_valid, verse_ref = self.validate_verse(chapter, str(verse_num))
        if not is_valid:
            return await ctx.send(f"🚫 Random selection validation failure: {verse_ref}", delete_after=9)

        try:
            # 2. Build the visual verse card component using cached chapter maps
            embed = create_verse_embed(
                self.data_path, self._chapter_cache,
                chapter, verse_ref,
                display_name=ctx.author.display_name,
            )

            # 3. Chart performance latency metric markers safely into embed footer
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            embed.set_footer(
                text=f"{embed.footer.text} ➜ 𝗋𝖾𝗍𝗋𝗂𝖾𝗏𝖾𝖽 𝗂𝗇 {latency_ms:.1f} 𝗆𝗌",
                icon_url=embed.footer.icon_url,
            )

            # 4. Bind view structures to message context window trackers
            view         = NavigationButtons(self, chapter, verse_ref, ctx)
            message      = await ctx.send(embed=embed, view=view)
            view.message = message

        except FileNotFoundError as e:
            await ctx.send(f"🚫 {e}", delete_after=90)
        except ValueError as e:
            await ctx.send(f"🚫 Error in verse data:\n\n{e}", delete_after=90)
        except Exception as e:
            await ctx.send(f"🚫 Unexpected error retrieving verse:\n\n{e}", delete_after=90)


async def setup(bot: commands.Bot):
    await bot.add_cog(AsItIs(bot))
