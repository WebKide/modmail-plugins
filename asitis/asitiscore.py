# asitiscore.py

import json
import random
import time
from pathlib import Path
from typing import List, Tuple, Optional

import discord
from discord.ext import commands

# ╔═══╦════════════════════════════════════════════════════╦═════╗
# ╠═══╣ Chapter metadata — single source of boundary logic ╠═════╣
# ╚═══╩════════════════════════════════════════════════════╩═════╝
BG_CHAPTER_INFO = {
    1: {'total_verses': 46, 'grouped_ranges': [(16, 18), (21, 22), (32, 35), (37, 38)], 'chapter_title': 'First. Observing the Armies on the Battlefield of Kurukṣetra'},
    2: {'total_verses': 72, 'grouped_ranges': [(42, 43)], 'chapter_title': 'Second. Contents of the Gītā Summarized'},
    3: {'total_verses': 43, 'grouped_ranges': [], 'chapter_title': 'Third. Karma-yoga'},
    4: {'total_verses': 42, 'grouped_ranges': [], 'chapter_title': 'Fourth. Transcendental Knowledge'},
    5: {'total_verses': 29, 'grouped_ranges': [(8, 9), (27, 28)], 'chapter_title': 'Fifth. Karma-yoga — Action in Kṛṣṇa Consciousness'},
    6: {'total_verses': 47, 'grouped_ranges': [(11, 12), (13, 14), (20, 23)], 'chapter_title': 'Sixth. Sāṅkhya-yoga'},
    7: {'total_verses': 30, 'grouped_ranges': [], 'chapter_title': 'Seventh. Knowledge of the Absolute'},
    8: {'total_verses': 28, 'grouped_ranges': [], 'chapter_title': 'Eighth. Attaining the Supreme'},
    9: {'total_verses': 34, 'grouped_ranges': [], 'chapter_title': 'Ninth. The Most Confidential Knowledge'},
    10: {'total_verses': 42, 'grouped_ranges': [(4, 5), (12, 13)], 'chapter_title': 'Tenth. The Opulence of the Absolute'},
    11: {'total_verses': 55, 'grouped_ranges': [(10, 11), (26, 27), (41, 42)], 'chapter_title': 'Eleventh. The Universal Form'},
    12: {'total_verses': 20, 'grouped_ranges': [(3, 4), (6, 7), (13, 14), (18, 19)], 'chapter_title': 'Twelfth. Devotional Service'},
    13: {'total_verses': 35, 'grouped_ranges': [(1, 2), (6, 7), (8, 12)], 'chapter_title': 'Thirteenth. Nature, the Enjoyer, and Consciousness'},
    14: {'total_verses': 27, 'grouped_ranges': [(22, 25)], 'chapter_title': 'Fourteenth. The Three Modes of Material Nature'},
    15: {'total_verses': 20, 'grouped_ranges': [(3, 4)], 'chapter_title': 'Fifteenth. The Yoga of the Supreme Person'},
    16: {'total_verses': 24, 'grouped_ranges': [(1, 3), (11, 12), (13, 15)], 'chapter_title': 'Sixteenth. The Divine and Demoniac Natures'},
    17: {'total_verses': 28, 'grouped_ranges': [(5, 6), (8, 10), (26, 27)], 'chapter_title': 'Seventeenth. The Divisions of Faith'},
    18: {'total_verses': 78, 'grouped_ranges': [(13, 14), (36, 37), (51, 53)], 'chapter_title': 'Eighteenth. Conclusion — The Perfection of Renunciation'}
}

# ╔═══╦═════════════════╦════════════════════════════════════════╗
# ╠═══╣ Embed constants ╠════════════════════════════════════════╣
# ╚═══╩═════════════════╩════════════════════════════════════════╝

EMBED_COLOR = discord.Color(0xF5A623)
AUTHOR_NAME = "Bhagavad Gītā — As It Is (Original 1972 edition)"
AUTHOR_ICON = "https://i.imgur.com/iZ6CHAz.png"
FOOTER_ICON = "https://i.imgur.com/10jxmCh.png"
DEDICATORY  = (
    "-# 𝗈ṁ 𝗇𝖺𝗆𝗈 𝖻𝗁𝖺𝗀𝖺𝗏𝖺𝗍𝖾 𝗏ā𝗌𝗎𝖽𝖾𝗏ā𝗒𝖺"
)
NO_PURPORT = [
    "This śloka does not contain a purport.",
    "No purport for this śloka.",
    "There is no purport provided for this śloka.",
    "This verse has no accompanying purport.",
    "This śloka does not include a Bhaktivedānta purport.",
    "No Bhaktivedānta purport provided for this verse.",
    "No Bhaktivedānta purport accompanies this śloka.",
]
PURPORT_MAX_CHARS = 2500  # safe Discord embed description limit
FIELD_MAX_CHARS = 1008  # Discord embed field value limit

# ╔═══╦═══════════════════════════════╦══════════════════════════╗
# ╠═══╣ Helper: purport page splitter ╠══════════════════════════╣
# ╚═══╩═══════════════════════════════╩══════════════════════════╝

def _split_purport(raw: str, max_len: int = PURPORT_MAX_CHARS) -> List[str]:
    """
    Split a purport into pages that each fit within *max_len* characters.

    Strategy:
      1. Try to break at paragraph boundaries (double newline).
      2. If a single paragraph still overflows, break at the last sentence
         boundary ('. ') before the limit.
      3. As a last resort, break at the last space before the limit.
    """
    # Normalise: collapse runs of spaces but keep paragraph separators
    paragraphs = [p.strip() for p in raw.split('\n\n') if p.strip()]

    pages: List[str] = []
    current = ""

    for para in paragraphs:
        separator = "\n\n" if current else ""
        candidate = current + separator + para

        if len(candidate) <= max_len:
            current = candidate
            continue

        # Paragraph doesn't fit in the current page — flush what we have
        if current:
            pages.append(current)
            current = ""

        # Does the paragraph itself fit on a fresh page?
        if len(para) <= max_len:
            current = para
            continue

        # Paragraph is too long on its own — sentence-split it
        sentences = para.split('. ')
        for i, sentence in enumerate(sentences):
            # Restore the '. ' that split() consumed (except for the last fragment)
            piece = sentence if i == len(sentences) - 1 else sentence + '. '
            sep   = " " if current else ""
            candidate = current + sep + piece

            if len(candidate) <= max_len:
                current = candidate
            else:
                if current:
                    pages.append(current)
                # If even a single sentence overflows, hard-cut at last space
                if len(piece) > max_len:
                    while piece:
                        cut = piece[:max_len]
                        cut_pos = cut.rfind(' ')
                        if cut_pos > 0:
                            pages.append(cut[:cut_pos])
                            piece = piece[cut_pos + 1:]
                        else:
                            pages.append(cut)
                            piece = piece[max_len:]
                    current = ""
                else:
                    current = piece

    if current:
        pages.append(current)

    return pages or ["No purport available."]

# ╔═══╦═════════════════════════════════════════════════════╦════╗
# ╠═══╣ Helper: generic text splitter used for embed fields ╠════╣
# ╚═══╩═════════════════════════════════════════════════════╩════╝

def _split_long_text(text: str, max_len: int = FIELD_MAX_CHARS) -> List[str]:
    """Split text at natural newline breaks; sentence-split as fallback."""
    if len(text) <= max_len:
        return [text]

    lines = text.split('\n')
    chunks: List[str] = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            if current:
                chunks.append(current)
                current = line
            else:
                split_pos = line.rfind(' ', 0, max_len - 3)
                if split_pos > 0:
                    chunks.append(line[:split_pos] + '...')
                    current = line[split_pos + 1:]
                else:
                    chunks.append(line[:max_len - 3] + '...')
                    current = line[max_len - 3:]
        else:
            current = (current + '\n' + line) if current else line

    if current:
        chunks.append(current)
    return chunks


# ╔═══╦═════════════════════════════════════════════════════╦════╗
# ╠═══╣ Data helpers (pure functions — no cog state needed) ╠════╣
# ╚═══╩═════════════════════════════════════════════════════╩════╝

def load_chapter_data(data_path: Path, cache: dict, chapter: int) -> dict:
    """Load and cache a chapter JSON file."""
    if chapter in cache:
        return cache[chapter]
    file_path = data_path / f"bg_ch{chapter:02d}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Chapter {chapter} data file not found")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cache[chapter] = data
            return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in **bg_ch{chapter}.json**: {e}")


def validate_verse(chapter: int, verse: str) -> Tuple[bool, str]:
    """Return (is_valid, verse_ref_or_error_message)."""
    if chapter not in BG_CHAPTER_INFO:
        return False, (
            f"Invalid chapter entry. The Bhagavad Gītā As It Is only has 18 chapters "
            f"and you requested **{chapter}**."
        )
    chapter_info = BG_CHAPTER_INFO[chapter]

    if '-' in verse:
        try:
            start, end = sorted(map(int, verse.split('-')))
            if start >= end:
                return False, "Start verse must be less than end verse."
            for r_start, r_end in chapter_info['grouped_ranges']:
                if start == r_start and end == r_end:
                    return True, f"{start}-{end}"
            if end > chapter_info['total_verses']:
                return False, f"Chapter {chapter} only has {chapter_info['total_verses']} verses."
            if start < 1:
                return False, "Verse numbers start at 1, there is no verse 0."
            return True, f"{start}-{end}"
        except ValueError:
            return False, "Invalid verse range format. Use like **17-18** or just the single verse to find the group."

    try:
        verse_num = int(verse)
        if verse_num < 1 or verse_num > chapter_info['total_verses']:
            return False, (
                f"Chapter {chapter} only has {chapter_info['total_verses']} verses, "
                f"double check and try again."
            )
        for r_start, r_end in chapter_info['grouped_ranges']:
            if r_start <= verse_num <= r_end:
                return True, f"{r_start}-{r_end}"
        return True, verse
    except ValueError:
        return False, f"**{verse}** is an invalid verse number, double check and try again."


def find_verse_data(chapter_data: dict, verse_ref: str) -> dict:
    """Locate a verse entry in chapter data by TEXT / TEXTS label."""
    verse_ref  = str(verse_ref)
    base_ref   = verse_ref  # already normalised

    # Exact match first
    for vd in chapter_data.get("Verses", []):
        tn = vd.get("Text-num", "")
        if f"TEXT {base_ref}" == tn or f"TEXTS {base_ref}" == tn:
            return vd

    # Partial match (handles grouped-range labels like "TEXT 8-10")
    for vd in chapter_data.get("Verses", []):
        if base_ref in vd.get("Text-num", ""):
            return vd

    # Fall back to starting verse number
    start_verse = base_ref.split('-')[0]
    for vd in chapter_data.get("Verses", []):
        if start_verse in vd.get("Text-num", ""):
            return vd

    raise ValueError(f"Verse {verse_ref} not found in chapter data.")


def format_verse_text(verse_data: dict) -> str:
    """Format Sanskrit verse text, preserving line breaks and bold markers."""
    verse_text = verse_data.get('Verse-Text', '')
    lines: List[str] = []
    current_line = ""
    in_bold = False

    for char in verse_text:
        if char == ';' and not in_bold:
            if current_line:
                lines.append(current_line.strip())
                current_line = ""
            continue
        current_line += char
        if char == '*':
            in_bold = not in_bold
        if char == '\n':
            if current_line.strip():
                lines.append(current_line.strip())
            current_line = ""

    if current_line.strip():
        lines.append(current_line.strip())

    formatted = '\n'.join(lines)
    if 'Uvaca-line' in verse_data:
        uvaca = verse_data['Uvaca-line'].strip()
        if not uvaca.endswith((':', '-', '—')):
            uvaca += ':'
        return f"{uvaca}\n{formatted}"
    return formatted


def format_synonyms(synonyms: str) -> List[str]:
    """Format Word-for-Word synonyms with italic bold markup; split if needed."""
    if not synonyms.strip():
        return ["No synonyms available."]

    synonyms = ' '.join(synonyms.replace('\n', ' ').split())
    formatted_items: List[str] = []

    for item in synonyms.split(';'):
        item = item.strip()
        if not item:
            continue
        if '—' in item:
            word, meaning = item.split('—', 1)
            formatted_items.append(f"_**{word.strip()}**_ — {meaning.strip()}")
        elif '-' in item and not any(c in item for c in ['ā', 'ī', 'ū', 'ṁ', 'ṣ', 'ṭ', 'ḥ', 'ś', 'ḍ']):
            parts = item.split('-', 1)
            formatted_items.append(f"_**{parts[0].strip()}**_ - {parts[1].strip()}")
        else:
            formatted_items.append(item)

    formatted_text = '; '.join(formatted_items)

    if len(formatted_text) <= FIELD_MAX_CHARS:
        return [formatted_text]

    chunks: List[str] = []
    current = ""
    for item in formatted_items:
        if len(current) + len(item) + 2 > FIELD_MAX_CHARS:
            chunks.append(current)
            current = item
        else:
            current = (current + "; " + item) if current else item
    if current:
        chunks.append(current)
    return chunks


def safe_add_field(embed: discord.Embed, name: str, value, inline: bool = False):
    """Add a field to *embed*, auto-splitting if the value exceeds Discord limits."""
    if not value:
        return
    if isinstance(value, list):
        value = '\n'.join(value)
    chunks = _split_long_text(str(value))
    embed.add_field(name=name, value=chunks[0], inline=inline)
    for chunk in chunks[1:]:
        embed.add_field(name="\u200b", value=chunk, inline=inline)


def build_footer_text(chapter: int, verse_ref: str, latency_ms: Optional[float] = None) -> str:
    """Compose the standard footer string for verse embeds."""
    v_label   = f"𝗏𝖾𝗋𝗌𝖾𝗌 {verse_ref}" if '-' in str(verse_ref) else f"𝗏𝖾𝗋𝗌𝖾 {verse_ref}"
    total_v   = BG_CHAPTER_INFO[chapter]['total_verses']
    text      = f"𝖢𝗁𝖺𝗉𝗍𝖾𝗋 {chapter}, {v_label} 𝗈𝖿 {total_v}"
    if latency_ms is not None:
        text += f" ➜ 𝗇𝖺𝗏𝗂𝗀𝖺𝗍𝖾𝖽 𝗂𝗇 {latency_ms:.1f} 𝗆𝗌"
    return text


# ╔═══╦════════════════╦═════════════════════════════════════════╗
# ╠═══╣ Embed builders ╠═════════════════════════════════════════╣
# ╚═══╩════════════════╩═════════════════════════════════════════╝

def create_verse_embed(
    data_path: Path,
    cache: dict,
    chapter: int,
    verse_ref: str,
    latency_ms: Optional[float] = None,
    display_name: str = "",
) -> discord.Embed:
    """Build and return the full verse embed."""
    chapter_data = load_chapter_data(data_path, cache, chapter)
    verse_data   = find_verse_data(chapter_data, verse_ref)

    embed = discord.Embed(
        color=EMBED_COLOR,
        description=(
            f"{DEDICATORY}\nMy Dear {display_name},\nPlease accept my blessings.\n\n"
            f"📜 **𝖢𝗁𝖺𝗉𝗍𝖾𝗋 {chapter}. "
            f"{BG_CHAPTER_INFO[chapter]['chapter_title'].split('. ', 1)[-1]}**"
        ),
    )
    embed.set_author(name=AUTHOR_NAME, icon_url=AUTHOR_ICON)

    # Sanskrit verse text
    safe_add_field(embed, name=f"𝚃𝙴𝚇𝚃 {verse_ref}:", value=format_verse_text(verse_data))

    # Synonyms
    for i, chunk in enumerate(format_synonyms(verse_data.get('Word-for-Word', ''))):
        safe_add_field(embed, name="📖 𝚂𝚈𝙽𝙾𝙽𝚈𝙼𝚂:" if i == 0 else "\u200b", value=chunk)

    # Translation
    translation = ' '.join(verse_data.get('Translation-En', '').split())
    for i, chunk in enumerate(_split_long_text(translation) if translation else ["No translation available."]):
        safe_add_field(
            embed,
            name="🗒️ 𝚃𝚁𝙰𝙽𝚂𝙻𝙰𝚃𝙸𝙾𝙽:" if i == 0 else "\u200b",
            value=f"> **{chunk}**",
        )

    # Footer
    embed.set_footer(text=build_footer_text(chapter, verse_ref, latency_ms), icon_url=FOOTER_ICON)

    # End-of-chapter colophon
    verse_end = int(str(verse_ref).split('-')[-1])
    if verse_end == BG_CHAPTER_INFO[chapter]['total_verses']:
        ordinal, title = BG_CHAPTER_INFO[chapter]['chapter_title'].split('. ', 1)
        embed.add_field(
            name="\u200b",
            value=(
                f"Thus end the Bhaktivedānta Purports to the {ordinal} Chapter of the "
                f"Śrīmad Bhagavad-gītā in the matter of {title}."
            ),
            inline=False,
        )

    return embed


def create_purport_embed(
    chapter: int,
    verse_ref: str,
    page_text: str,
    page_num: int,
    total_pages: int,
) -> discord.Embed:
    """Build a single purport-page embed."""
    v_label      = f"𝗏𝖾𝗋𝗌𝖾𝗌 {verse_ref}" if '-' in str(verse_ref) else f"𝗏𝖾𝗋𝗌𝖾 {verse_ref}"
    total_v      = BG_CHAPTER_INFO[chapter]['total_verses']
    chapter_name = BG_CHAPTER_INFO[chapter]['chapter_title'].split('. ', 1)[-1]
    pagination   = "" if total_pages == 1 else f" · 𝖯𝖺𝗀𝖾 {page_num} 𝗈𝖿 {total_pages}"

    embed = discord.Embed(
        color=EMBED_COLOR,
        title=f"{chapter_name} · 𝖡𝖦 {chapter}.{verse_ref}",
        description=f"**🖊️ 𝐏𝐔𝐑𝐏𝐎𝐑𝐓**{pagination}\n\n{page_text}",
    )
    embed.set_author(name=AUTHOR_NAME, icon_url=AUTHOR_ICON)
    embed.set_footer(
        text=f"𝖢𝗁𝖺𝗉𝗍𝖾𝗋 {chapter}, {v_label} 𝗈𝖿 {total_v}  ·  𝖯𝖴𝖱𝖯𝖮𝖱𝖳",
        icon_url=FOOTER_ICON,
    )
    return embed


# ╔═══╦══════════════════════════════════════════════════════╦═══╗
# ╠═══╣ Navigation helpers (NavigationButtons & PurportView) ╠═══╣
# ╚═══╩══════════════════════════════════════════════════════╩═══╝

def parse_verse_ref(verse_ref) -> Tuple[int, int]:
    """Return (start, end) integers from a verse reference string or int."""
    if isinstance(verse_ref, int):
        return verse_ref, verse_ref
    s = str(verse_ref)
    if '-' in s:
        parts = s.split('-')
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
            (f"{rs}-{re}" for rs, re in BG_CHAPTER_INFO[chapter]['grouped_ranges'] if rs <= pv <= re),
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
            (f"{rs}-{re}" for rs, re in BG_CHAPTER_INFO[chapter]['grouped_ranges'] if rs <= nv <= re),
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
        timeout: float = 1800.0,
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
        return create_purport_embed(
            self.chapter,
            self.verse_ref,
            self.pages[self.current_page],
            self.current_page + 1,
            len(self.pages),
        )

    async def _go_to_verse(self, interaction: discord.Interaction, chapter: int, verse_ref: str):
        """Switch message back to a full verse view (NavigationButtons)."""
        start_time = time.time()
        await interaction.response.defer()
        latency_ms = (time.time() - start_time) * 1000
        try:
            embed = create_verse_embed(
                self.cog.data_path, self.cog._chapter_cache,
                self.chapter, self.verse_ref, latency_ms,
                display_name=self.author.display_name,
            )
            new_view = NavigationButtons(self.cog, chapter, verse_ref, self.ctx)
            new_view.message = interaction.message
            await interaction.message.edit(embed=embed, view=new_view)
        except Exception as e:
            await interaction.followup.send(f"Navigation error: {e}", ephemeral=True)

    # ╠═══ timeout ═══════════════════════════════════════════════════════╣

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
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
            await interaction.response.defer()
            self.current_page -= 1
            self._refresh_button_states()
            await interaction.message.edit(embed=self._build_embed(), view=self)

    @discord.ui.button(label="𝖵𝖾𝗋𝗌𝖾", style=discord.ButtonStyle.blurple, custom_id="purport_verse")
    async def verse_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to the verse embed (same verse, NavigationButtons view)."""
        start_time = time.time()
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
            await interaction.response.defer()
            self.current_page += 1
            self._refresh_button_states()
            await interaction.message.edit(embed=self._build_embed(), view=self)

    @discord.ui.button(label="𝖢𝗅𝗈𝗌𝖾", style=discord.ButtonStyle.red, custom_id="purport_close")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "Only the command author can close this.", ephemeral=True
            )
            return
        await interaction.message.delete()
        try:
            await self.ctx.message.delete()
        except (discord.NotFound, discord.Forbidden):
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
        timeout: float = 1800.0,
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
        if self._prev_ch is None:
            self.children[0].disabled = True
        if self._next_ch is None:
            self.children[2].disabled = True

    # ╠═══ helpers ═══════════════════════════════════════════════════════╣

    async def _navigate(self, interaction: discord.Interaction, chapter: int, verse_ref: str):
        """Replace embed with another verse (same NavigationButtons view)."""
        start_time = time.time()
        await interaction.response.defer()
        latency_ms = (time.time() - start_time) * 1000
        try:
            embed = create_verse_embed(
                self.cog.data_path, self.cog._chapter_cache,
                self.chapter, self.verse_ref, latency_ms,
                display_name=self.author.display_name,
            )
            new_view = NavigationButtons(self.cog, chapter, verse_ref, self.ctx)
            new_view.message = interaction.message
            await interaction.message.edit(embed=embed, view=new_view)
        except Exception as e:
            await interaction.followup.send(f"Error navigating: {e}", ephemeral=True)

    # ╠═══ timeout ═══════════════════════════════════════════════════════╣

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
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

            # ╠═══╣ 2. Embed edit for verses without Purport ╠═══════════════╣
            # if not raw_purport or raw_purport == "No purport for this śloka.":
            #    raw_purport = random.choice(NO_PURPORT)
            # ╚═══╩══════════════════════════════════════════╩═══════════════╝

            verse_end = int(str(self.verse_ref).split('-')[-1])
            if verse_end == BG_CHAPTER_INFO[self.chapter]['total_verses']:
                ordinal, title = BG_CHAPTER_INFO[self.chapter]['chapter_title'].split('. ', 1)
                raw_purport += (
                    f"\n\nThus end the Bhaktivedānta Purports to the {ordinal} Chapter "
                    f"of the Śrīmad Bhagavad-gītā in the matter of {title}."
                )

            pages = _split_purport(raw_purport)
            purport_view = PurportView(
                self.cog, self.chapter, self.verse_ref, self.ctx, pages
            )
            purport_view.message = interaction.message
            await interaction.message.edit(
                embed=purport_view._build_embed(), view=purport_view
            )
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

    @discord.ui.button(label="𝖢𝗅𝗈𝗌𝖾", style=discord.ButtonStyle.red, custom_id="nav_close")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "Only the command author can close this.", ephemeral=True
            )
            return
        await interaction.message.delete()
        try:
            await self.ctx.message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permissions to delete the command message.", ephemeral=True
            )
