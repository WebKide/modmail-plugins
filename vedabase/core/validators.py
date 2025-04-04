from typing import Tuple, Union, Dict, Any
from .info_dict import BG_CHAPTER_INFO, CC_BOOK_INFO, SB_CANTO_INFO

class VedabaseValidator:
    def __init__(self, bg_info: Dict, cc_info: Dict, sb_info: Dict):
        self.bg_info = bg_info
        self.cc_info = cc_info
        self.sb_info = sb_info

    def validate_bg_input(self, chapter: Union[int, str], verse_input: str) -> Tuple[bool, str]:
        """Validate Bhagavad Gita chapter and verse input"""
        try:
            chapter = str(chapter)
            if chapter not in self.bg_info:
                return (False, f"Invalid chapter number. The Bhagavad Gītā has 18 chapters (requested {chapter}).")
            
            chapter_data = self.bg_info[chapter]
            total_verses = chapter_data['total_verses']

            if '-' in verse_input:
                start, end = sorted(map(int, verse_input.split('-')))
                if end > total_verses:
                    return (False, f"Chapter {chapter} only has {total_verses} verses.")
                
                for r_start, r_end in chapter_data.get('grouped_ranges', []):
                    if start >= r_start and end <= r_end:
                        return (True, f"{r_start}-{r_end}")
                    if (start <= r_end and end >= r_start):
                        return (False, f"Requested verses {start}-{end} overlap with predefined grouped range {r_start}-{r_end}.")
                
                return (True, f"{start}-{end}")
            
            verse_num = int(verse_input)
            if verse_num < 1 or verse_num > total_verses:
                return (False, f"Chapter {chapter} has only {total_verses} verses.")
            
            for r_start, r_end in chapter_data.get('grouped_ranges', []):
                if r_start <= verse_num <= r_end:
                    return (True, f"{r_start}-{r_end}")
            
            return (True, str(verse_num))
            
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")

    def validate_cc_input(self, book: str, chapter: Union[int, str], verse_input: str) -> Tuple[bool, str]:
        """Validate Caitanya Caritamrita book, chapter and verse input"""
        book = book.lower()
        if book not in self.cc_info and book not in {'1', '2', '3'}:
            return (False, "Invalid book. Use 'adi' or '1', 'madhya' or '2', 'antya' or '3'.")
        
        try:
            chapter = int(chapter)
            if chapter < 1:
                return (False, "Chapter numbers must be positive.")
            
            if '-' in verse_input:
                start, end = sorted(map(int, verse_input.split('-')))
                if start < 1:
                    return (False, "Verse numbers must be positive.")
                return (True, f"{start}-{end}")
            
            verse_num = int(verse_input)
            if verse_num < 1:
                return (False, "Verse numbers must be positive.")
            return (True, str(verse_num))
            
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")

    def validate_sb_input(self, canto: Union[int, str], chapter: Union[int, str], verse_input: str) -> Tuple[bool, str]:
        """Validate Srimad Bhagavatam canto, chapter and verse input"""
        canto = str(canto)
        if canto not in self.sb_info and not (canto.isdigit() and 1 <= int(canto) <= 12):
            return (False, "Invalid canto. Śrīmad Bhāgavatam has 12 cantos (1-12).")
        
        try:
            chapter = int(chapter)
            if chapter < 1:
                return (False, "Chapter numbers must be positive.")
            
            if '-' in verse_input:
                start, end = sorted(map(int, verse_input.split('-')))
                if start < 1:
                    return (False, "Verse numbers must be positive.")
                return (True, f"{start}-{end}")
            
            verse_num = int(verse_input)
            if verse_num < 1:
                return (False, "Verse numbers must be positive.")
            return (True, str(verse_num))
            
        except ValueError:
            return (False, f"Invalid verse number: {verse_input}")

    def validate_search_input(self, word: str, search_type: str) -> Tuple[bool, str]:
        """Validate search parameters"""
        if not word.strip():
            return (False, "Search term cannot be empty.")
        
        valid_search_types = {'exact-word', 'exact', 'contains', 'starts'}
        if search_type not in valid_search_types:
            return (False, f"Invalid search type. Must be one of: {', '.join(valid_search_types)}")
        
        return (True, "")
        
