# asitisnav.py

import random
import time
from typing import List, Tuple, Optional

import discord
from discord.ext import commands

from .asitiscore import (
    BG_CHAPTER_INFO,
    NO_PURPORT,
    EMBED_COLOR,
    AUTHOR_NAME,
    AUTHOR_ICON,
    FOOTER_ICON,
    PURPORT_MAX_CHARS,
    _split_purport,
    load_chapter_data,
    find_verse_data,
    create_verse_embed,
    create_purport_embed,
)

# ╔═══╦══════════════════════════════════════════════════════╦═══╗
# ╠═══╣ Navigation helpers (NavigationButtons & PurportView) ╠═══╣
# ╚═══╩══════════════════════════════════════════════════════╩═══╝

def parse_verse_ref(verse_ref) -> Tuple[int, int]:
    """Return (start, end) integers from a verse reference string or int."""
    if isinstance(verse_ref, int):
        return verse_ref, verse_ref
    s = str(verse_ref)
    if '-' in s:
        parts = s.split("-")
        return int(parts[0]), int(parts[-1])
    return int(s), int(s)


def get_adjacent_verses(
    chapter: int,
    verse_ref: str,
) -> Tuple[Tuple[Optional[int], Optional[str]], Tuple[Optional[int], Optional[str]]]:
    """
    Return ((prev_ch, prev_ref), (next_ch, next_ref)).
    Either tuple element may be (None, None) at the absolute boundaries of the Gītā.
    """
    start, end = parse_verse_ref(verse_ref)

    # ╠═══ previous ═══════════════════════════════════════════════════════╣
    if chapter == 1 and start == 1:
        prev = (None, None)
    elif start == 1:
        prev_ch = chapter - 1
        prev    = (prev_ch, str(BG_CHAPTER_INFO[prev_ch]['total_verses']))
    else:
        pv = start - 1
        prev = (chapter, next(
            (f"{rs}-{re}" for rs, re in BG_CHAPTER_INFO[chapter].get('grouped_ranges', []) if rs <= pv <= re),
            str(pv),
        ))

    # ╠═══ next ═══════════════════════════════════════════════════════╣
    if chapter == 18 and end == BG_CHAPTER_INFO[18]['total_verses']:
        nxt = (None, None)
    elif end == BG_CHAPTER_INFO[chapter]['total_verses']:
        next_ch = chapter + 1
        nxt     = (next_ch, "1")
    else:
        nv = end + 1
        nxt = (chapter, next(
            (f"{rs}-{re}" for rs, re in BG_CHAPTER_INFO[chapter].get('grouped_ranges', []) if rs <= nv <= re),
            str(nv),
        ))

    return prev, nxt


# ╔═══╦════════════════════════════════════════════════════╦═════╗
# ╠═══╣ PurportView — when user presses the Purport button ╠═════╣
# ╚═══╩════════════════════════════════════════════════════╩═════╝

class PurportView(discord.ui.View):
    """
    Four-button view for reading a purport page by page.

    Button layout: ◀ 𝖯𝗋𝖾𝗏  |  𝖵𝖾𝗋𝗌𝖾  |  𝖭𝖾𝗑𝗍 ▶  |  𝖢𝗅𝗈𝗌𝖾

    ◀ 𝖯𝗋𝖾𝗏 / 𝖭𝖾𝗑𝗍 ▶ behaviour:
      • If the purport has multiple pages:
          - On page 1,  ◀ 𝖯𝗋𝖾𝗏  navigates to the *previous verse* in the Gītā.
          - On page N,  𝖭𝖾𝗑𝗍 ▶  navigates to the *next verse* (ebook feel).
          - On inner pages both buttons step through purport pages.
      • If the purport fits in a single page both buttons navigate verse-to-verse
        directly (as if paging through the book).
    """

    def __init__(
        self,
        cog,  # AsItIs cog instance (carries data_path + cache)
        chapter: int,
        verse_ref: str,
        ctx: commands.Context,
        pages: List[str],
        current_page: int = 0,
        timeout: float = 300.0,  # 5 min
    ):
        super().__init__(timeout=timeout)
        self.cog          = cog
        self.chapter      = chapter
        self.verse_ref    = verse_ref
        self.ctx          = ctx
        self.author       = ctx.author
        self.pages        = pages
        self.current_page = current_page
        self.message      = None

        (self._prev_ch, self._prev_ref), (self._next_ch, self._next_ref) = \
            get_adjacent_verses(chapter, verse_ref)

        self._refresh_button_states()

    # ╠═══ internal helpers ═══════════════════════════════════════════════════════╣

    def _is_single_page(self) -> bool:
        return len(self.pages) == 1

    def _refresh_button_states(self):
        """
        Enable/disable ◀ 𝖯𝗋𝖾𝗏 and 𝖭𝖾𝗑𝗍 ▶ buttons.
        Both are always present; they're disabled only at the absolute
        boundaries of the entire Gītā.
        """
        # Button indices in self.children: 0=prev, 1=verse, 2=next, 3=close
        at_book_start = (self._prev_ch is None and
                         (self._is_single_page() or self.current_page == 0))
        at_book_end   = (self._next_ch is None and
                         (self._is_single_page() or self.current_page == len(self.pages) - 1))

        self.children[0].disabled = at_book_start
        self.children[2].disabled = at_book_end

    def _build_embed(self) -> discord.Embed:
        formatted_name = self.author.display_name.title()
        return create_purport_embed(
            self.chapter,
            self.verse_ref,
            self.pages[self.current_page],
            self.current_page + 1,
            len(self.pages),
            display_name=formatted_name,
        )

    async def _go_to_verse(self, interaction: discord.Interaction, chapter: int, verse_ref: str):
        """Switch message back to a full verse view (NavigationButtons)."""
        start_time = time.time()
        if not interaction.response.is_done():
            await interaction.response.defer()
        latency_ms = (time.time() - start_time) * 1000
        try:
            embed = create_verse_embed(
                self.cog.data_path, self.cog._chapter_cache,
                chapter, verse_ref, latency_ms,
                display_name=self.author.display_name,
            )
            new_view = NavigationButtons(self.cog, chapter, verse_ref, self.ctx)
            new_view.message = interaction.message
            await interaction.message.edit(embed=embed, view=new_view)
        except Exception as e:
            await interaction.response.send_message(f"Navigation error: {e}", ephemeral=True)

    # ╠═══ timeout ═══════════════════════════════════════════════════════╣

    async def on_timeout(self):
        """Strip all buttons from the message completely when the purport times out."""
        if self.message:
            try:
                await self.message.edit(view=None)
            except (discord.NotFound, discord.HTTPException):
                pass

    # ╠═══ buttons ═══════════════════════════════════════════════════════╣

    @discord.ui.button(label="◀ 𝖯𝗋𝖾𝗏", style=discord.ButtonStyle.grey, custom_id="purport_prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self._is_single_page() or self.current_page == 0:
            # Navigate to the previous verse in the Gītā
            if self._prev_ch is None:
                await interaction.response.send_message(
                    "This is the first verse of the Bhagavad Gītā.", ephemeral=True
                )
                return
            await self._go_to_verse(interaction, self._prev_ch, self._prev_ref)
        else:
            if not interaction.response.is_done():
                await interaction.response.defer()
            self.current_page -= 1
            self._refresh_button_states()
            await interaction.message.edit(embed=self._build_embed(), view=self)

    @discord.ui.button(label="𝖵𝖾𝗋𝗌𝖾", style=discord.ButtonStyle.blurple, custom_id="purport_verse")
    async def verse_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to the verse embed (same verse, NavigationButtons view)."""
        start_time = time.time()
        if not interaction.response.is_done():
            await interaction.response.defer()
        latency_ms = (time.time() - start_time) * 1000
        try:
            embed = create_verse_embed(
                self.cog.data_path, self.cog._chapter_cache,
                self.chapter, self.verse_ref, latency_ms,
                display_name=self.author.display_name,
            )
            new_view = NavigationButtons(self.cog, self.chapter, self.verse_ref, self.ctx)
            new_view.message = interaction.message
            await interaction.message.edit(embed=embed, view=new_view)
        except Exception as e:
            await interaction.followup.send(f"Error returning to verse: {e}", ephemeral=True)

    @discord.ui.button(label="𝖭𝖾𝗑𝗍 ▶", style=discord.ButtonStyle.grey, custom_id="purport_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self._is_single_page() or self.current_page == len(self.pages) - 1:
            # Navigate to the next verse in the Gītā
            if self._next_ch is None:
                await interaction.response.send_message(
                    "This is the last verse of the Bhagavad Gītā.", ephemeral=True
                )
                return
            await self._go_to_verse(interaction, self._next_ch, self._next_ref)
        else:
            if not interaction.response.is_done():
                await interaction.response.defer()
            self.current_page += 1
            self._refresh_button_states()
            await interaction.message.edit(embed=self._build_embed(), view=self)

    @discord.ui.button(
        label="𝖢𝗅𝗈𝗌𝖾",
        style=discord.ButtonStyle.red,
        custom_id="nav_close",
    )
    async def close_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if interaction.user != self.author:

            await interaction.response.send_message(
                "Only the command author can close this.",
                ephemeral=True,
            )

            return

        try:
            await interaction.message.delete()

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            pass

        try:
            await self.ctx.message.delete()

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            pass


# ╔═══╦══════════════════════════════════════════════════╦═══════╗
# ╠═══╣ NavigationButtons — shown on normal verse embeds ╠═══════╣
# ╚═══╩══════════════════════════════════════════════════╩═══════╝

class NavigationButtons(discord.ui.View):
    """
    Five-button view attached to verse embeds.

    Button layout: ◀ 𝖯𝗋𝖾𝗏  |  𝖯𝗎𝗋𝗉𝗈𝗋𝗍  |  𝖭𝖾𝗑𝗍 ▶  |  𝖢𝗅𝗈𝗌𝖾
    """

    def __init__(
        self,
        cog,
        chapter: int,
        verse_ref: str,
        ctx: commands.Context,
        timeout: float = 300.0,  # 5 min
    ):
        super().__init__(timeout=timeout)
        self.cog       = cog
        self.chapter   = chapter
        self.verse_ref = verse_ref
        self.ctx       = ctx
        self.author    = ctx.author
        self.message   = None

        (self._prev_ch, self._prev_ref), (self._next_ch, self._next_ref) = \
            get_adjacent_verses(chapter, verse_ref)

        # Disable Prev/Next at absolute book boundaries
        # Button index order: 0=prev, 1=purport, 2=next, 3=close
        """
        if self._prev_ch is None:
            self.children[0].disabled = True
        if self._next_ch is None:
            self.children[2].disabled = True
        """

        if len(self.children) >= 3:
            if self._prev_ch is None: self.children[0].disabled = True
            if self._next_ch is None: self.children[2].disabled = True

    # ╠═══ helpers ═══════════════════════════════════════════════════════╣

    async def _navigate(self, interaction: discord.Interaction, chapter: int, verse_ref: str):
        """Replace embed with another verse (same NavigationButtons view)."""
        start_time = time.time()
        if not interaction.response.is_done():
            await interaction.response.defer()
        latency_ms = (time.time() - start_time) * 1000
        try:
            embed = create_verse_embed(
                self.cog.data_path, self.cog._chapter_cache,
                chapter, verse_ref, latency_ms,
                display_name=self.author.display_name,
            )
            new_view = NavigationButtons(self.cog, chapter, verse_ref, self.ctx)
            new_view.message = interaction.message
            await interaction.message.edit(embed=embed, view=new_view)
        except Exception as e:
            await interaction.followup.send(f"Error navigating: {e}", ephemeral=True)

    # ╠═══ timeout ═══════════════════════════════════════════════════════╣

    async def on_timeout(self):
        """Strip all buttons from the message completely when the verse navigation times out."""
        if self.message:
            try:
                await self.message.edit(view=None)
            except (discord.NotFound, discord.HTTPException):
                pass

    # ╠═══ buttons ═══════════════════════════════════════════════════════╣

    @discord.ui.button(label="◀ 𝖯𝗋𝖾𝗏", style=discord.ButtonStyle.grey, custom_id="nav_prev")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self._prev_ch is None:
            await interaction.response.send_message(
                "This is the first verse of the Bhagavad Gītā.", ephemeral=True
            )
            return
        await self._navigate(interaction, self._prev_ch, self._prev_ref)

    @discord.ui.button(label="𝖯𝗎𝗋𝗉𝗈𝗋𝗍", style=discord.ButtonStyle.blurple, custom_id="nav_purport")
    async def purport_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Load the purport for this verse and switch to PurportView."""
        if not interaction.response.is_done():
            await interaction.response.defer()
        try:
            chapter_data = load_chapter_data(
                self.cog.data_path, self.cog._chapter_cache, self.chapter
            )
            verse_data = find_verse_data(chapter_data, self.verse_ref)
            raw_purport = verse_data.get('Purport-En', '').strip()

            # ╔═══╦═══════════════════════════════════════════════════╦══════╗
            # ╠═══╣ 1. Ephemeral message for verses without a Purport ╠══════╣
            raw_purport = "" if raw_purport == "No purport for this śloka." else raw_purport
            if not raw_purport:
                chapter_name = BG_CHAPTER_INFO[self.chapter]['chapter_title'].split('. ', 1)[-1]
                await interaction.followup.send(
                    f"Original 1972 Macmillan edition\n\n"
                    f"To Śrīla Baladeva Vidyābhūṣaṇa who presented so nicely the “Govinda-bhāṣya” commentary on Vedānta philosophy.\n\n"
                    f"Śrīmad Bhagavad Gītā As It Is\n"
                    f"Chapter {self.chapter}, {chapter_name}, text {self.verse_ref}\n\n"
                    f"{random.choice(NO_PURPORT)}",
                    ephemeral=True,
                )
                return

            # ╠═══╣ 2. Edit Embed for verses without Purport ╠═══════════════╣
            # if not raw_purport or raw_purport == "No purport for this śloka.":
            #    np = f"Original 1972 Macmillan edition\n\n"
            #         f"To Śrīla Baladeva Vidyābhūṣaṇa who presented so nicely the “Govinda-bhāṣya” commentary on Vedānta philosophy.\n\n"
            #         f"Śrīmad Bhagavad Gītā As It Is\n"
            #         f"Chapter {self.chapter}, {chapter_name}, text {self.verse_ref}\n\n"
            #         f"{random.choice(NO_PURPORT)}"
            #    raw_purport = np
            # ╚═══╩══════════════════════════════════════════╩═══════════════╝

            verse_end = int(str(self.verse_ref).split('-')[-1])
            if verse_end == BG_CHAPTER_INFO[self.chapter]['total_verses']:
                ordinal, title = BG_CHAPTER_INFO[self.chapter]['chapter_title'].split('. ', 1)
                raw_purport += (
                    f"\n\nThus end the Bhaktivedānta Purports to the {ordinal} Chapter "
                    f"of the Śrīmad Bhagavad-gītā in the matter of {title}."
                )

            pages = _split_purport(raw_purport, PURPORT_MAX_CHARS)
            purport_view = PurportView(self.cog, self.chapter, self.verse_ref, self.ctx, pages)
            purport_view.message = interaction.message

            await interaction.message.edit(embed=purport_view._build_embed(), view=purport_view)

        except Exception as e:
            await interaction.followup.send(f"Error loading purport: {e}", ephemeral=True)

    @discord.ui.button(label="𝖭𝖾𝗑𝗍 ▶", style=discord.ButtonStyle.grey, custom_id="nav_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self._next_ch is None:
            await interaction.response.send_message(
                "This is the last verse of the Bhagavad Gītā.", ephemeral=True
            )
            return
        await self._navigate(interaction, self._next_ch, self._next_ref)

    @discord.ui.button(
        label="𝖢𝗅𝗈𝗌𝖾",
        style=discord.ButtonStyle.red,
        custom_id="nav_close",
    )
    async def close_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if interaction.user != self.author:

            await interaction.response.send_message(
                "Only the command author can close this.",
                ephemeral=True,
            )

            return

        try:
            await interaction.message.delete()

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            pass

        try:
            await self.ctx.message.delete()

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            pass
