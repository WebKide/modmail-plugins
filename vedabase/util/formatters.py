# core/formatters.py
import discord
from typing import List, Dict
from enum import Enum
from .info_dict import BG_CHAPTER_INFO, CC_BOOK_INFO, SB_CANTO_INFO

class VedabaseFormatter:
    def __init__(self):
        self.embed_colors = {
            'bg': 0x50e3c2,  # Bhagavad Gita
            'cc': 0x3b88c3,  # Caitanya Caritamrita
            'sb': 0x9b59b6,  # Srimad Bhagavatam
            'search': 0x3498db  # Search results
        }

    def _split_content(self, text: str, max_len: int = 1020) -> List[str]:
        """Smart content splitting at natural breaks"""
        if len(text) <= max_len:
            return [text]
        
        chunks = []
        while text:
            split_pos = max(
                text.rfind(';', 0, max_len),
                text.rfind(',', 0, max_len),
                text.rfind(' ', 0, max_len),
                max_len if len(text) > max_len else len(text)
            )
            
            chunk = text[:split_pos].strip()
            chunks.append(chunk)
            text = text[split_pos:].strip()
        
        return chunks

    async def add_field_safe(self, embed: discord.Embed, name: str, value: str, inline: bool = False) -> None:
        """Add field with automatic splitting if needed"""
        if not value:
            return
        
        chunks = self._split_content(str(value))
        embed.add_field(name=name, value=chunks[0], inline=inline)
        for chunk in chunks[1:]:
            embed.add_field(name="↳", value=chunk, inline=inline)

    def get_chapter_title(self, scripture: str, chapter_ref: Union[int, str]) -> str:
        """Retrieve the formatted chapter title based on scripture type"""
        if scripture == 'bg':
            if str(chapter_ref) not in BG_CHAPTER_INFO:
                return f"Chapter {chapter_ref}"
            return BG_CHAPTER_INFO[str(chapter_ref)].get('chapter_title', f"Chapter {chapter_ref}")
        elif scripture == 'cc':
            book = str(chapter_ref).lower()
            return CC_BOOK_INFO.get(book, {}).get('title', f"Book {book}")
        elif scripture == 'sb':
            canto = str(chapter_ref)
            return f"Canto {canto} - {SB_CANTO_INFO.get(canto, {}).get('title', 'Unknown')}"
        return f"Chapter {chapter_ref}"

    def format_bg_embed(self, chapter: int, verse: str, content: Dict[str, str], url: str) -> discord.Embed:
        """Format Bhagavad Gita verse into Discord embed"""
        chapter_title = self.get_chapter_title('bg', chapter)
        
        embed = discord.Embed(
            colour=discord.Colour(self.embed_colors['bg']),
            url=url,
            description=f"**{chapter_title}**"
        )
        
        embed.set_author(
            name=f"Bhagavad Gītā — Śloka [ {chapter}.{verse} ]",
            url=url,
            icon_url="https://imgur.com/Yx661rW.png"
        )
        
        return embed

    def format_cc_embed(self, book: str, chapter: int, verse: str, content: Dict[str, str], url: str) -> discord.Embed:
        """Format Caitanya Caritamrita verse into Discord embed"""
        book_title = self.get_chapter_title('cc', book)
        
        embed = discord.Embed(
            colour=discord.Colour(self.embed_colors['cc']),
            url=url,
            description=f"**{book_title} - Chapter {chapter}**"
        )
        
        embed.set_author(
            name=f"Caitanya-caritāmṛta — Śloka [ {book}.{chapter}.{verse} ]",
            url=url,
            icon_url="https://imgur.com/Yx661rW.png"
        )
        
        return embed

    def format_sb_embed(self, canto: str, chapter: int, verse: str, content: Dict[str, str], url: str) -> discord.Embed:
        """Format Srimad Bhagavatam verse into Discord embed"""
        canto_title = self.get_chapter_title('sb', canto)
        
        embed = discord.Embed(
            colour=discord.Colour(self.embed_colors['sb']),
            url=url,
            description=f"**{canto_title} - Chapter {chapter}**"
        )
        
        embed.set_author(
            name=f"Śrīmad Bhāgavatam — Śloka [ {canto}.{chapter}.{verse} ]",
            url=url,
            icon_url="https://imgur.com/Yx661rW.png"
        )
        
        return embed

    def format_search_results(self, word: str, results: List[Dict], search_type: str) -> discord.Embed:
        """Format search results into a Discord embed"""
        search_type_name = search_type.replace("-", " ").title()
        
        embed = discord.Embed(
            title=f"Search Results for: {word}",
            color=discord.Colour(self.embed_colors['search']),
            description=f"**Search Type:** {search_type_name}\nShowing top {len(results)} meanings"
        )
        
        for result in results:
            # Format references
            ref_lines = []
            for ref_text, ref_url in result['references']:
                ref_lines.append(f"[{ref_text}]({ref_url})")
            
            references = "\n".join(ref_lines) or "No references found"
            
            embed.add_field(
                name=f"**{result['term']}** - {result['meaning']}",
                value=references,
                inline=False
            )
        
        embed.set_footer(text="Click the button below to view full results on Vedabase")
        return embed

    def format_error(self, error_msg: str, scripture_type: str = None) -> discord.Embed:
        """Format error message into Discord embed"""
        color = self.embed_colors.get(scripture_type.lower() if scripture_type else 'search', 0xe74c3c)
        
        embed = discord.Embed(
            title="🚫 Error",
            description=error_msg,
            color=discord.Colour(color)
        )
        
        if scripture_type:
            embed.set_footer(text=f"{scripture_type} command failed")
        
        return embed
        
