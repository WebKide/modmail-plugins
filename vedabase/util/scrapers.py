import aiohttp
import random
import asyncio
import time

from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

class VedabaseScraper:
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://vedabase.io/en/library/"
        self.search_url = "https://vedabase.io/en/search/synonyms/"
        # self.ua = UserAgent(use_cache_server=False)
        # 10 Modern User Agents for Rotation
        self.user_agents = [
            # Chrome (Windows/Mac/Linux)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Firefox (Windows/Mac/Linux)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/115.0",
            
            # Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            
            # Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            
            # Mobile (Android/iPhone)
            "Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.43 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
        ]
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.request_delay = 5  # seconds between requests
        self.timeout = aiohttp.ClientTimeout(total=10)

    def get_random_user_agent(self) -> str:
        """Return a random user agent from the list"""
        return random.choice(self.user_agents)

    async def ensure_session(self) -> None:
        """Initialize session with rotating user agent"""
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://vedabase.io/',
            'DNT': '1',
            'Connection': 'keep-alive'
        }
        
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(headers=headers, timeout=self.timeout)

    async def scrape_with_retry(self, url: str, max_retries: int = 3) -> str:
        """Robust scraping with retry logic and rate limiting"""
        await self.ensure_session()
        
        for attempt in range(max_retries):
            try:
                # Respect crawl delay
                elapsed = time.time() - self.last_request_time
                if elapsed < self.request_delay:
                    await asyncio.sleep(self.request_delay - elapsed)
                
                self.last_request_time = time.time()
                # Rotate user agent for each attempt
                self.session.headers.update({'User-Agent': self.get_random_user_agent()})
                
                async with self.session.get(url) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 5))
                        await asyncio.sleep(retry_after)
                        continue
                        
                    if response.status == 403:
                        raise ValueError("Access forbidden - potentially blocked")
                        
                    if response.status != 200:
                        continue
                        
                    return await response.text()
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1 + random.random())
                
        raise ValueError(f"Failed after {max_retries} attempts")

    async def get_verse_content(self, scripture: str, *path_parts: str) -> Dict[str, str]:
        """Get verse content from Vedabase"""
        url = f"{self.base_url}{scripture}/{'/'.join(str(p) for p in path_parts)}/"
        html = await self.scrape_with_retry(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        def get_section(class_name: str) -> str:
            section = soup.find('div', class_=class_name)
            if not section:
                return "Not available"
            
            if class_name in ('av-devanagari', 'av-bengali'):
                text_div = section.find('div', class_='text-center')
                if text_div:
                    for br in text_div.find_all('br'):
                        br.replace_with('\n')
                    return text_div.get_text(strip=False)
            
            elif class_name == 'av-verse_text':
                verse_parts = []
                for italic_div in section.find_all('div', class_='italic'):
                    for br in italic_div.find_all('br'):
                        br.replace_with('\n')
                    verse_parts.append(italic_div.get_text(strip=False))
                return '\n'.join(verse_parts)
            
            elif class_name == 'av-synonyms':
                text_div = section.find('div', class_='text-justify')
                if text_div:
                    for a in text_div.find_all('a'):
                        if '-' in a.text:
                            parent_span = a.find_parent('span', class_='inline')
                            if parent_span:
                                hyphenated_term = '_' + a.text + '_'
                                parent_span.replace_with(hyphenated_term)
                    
                    for em in text_div.find_all('em'):
                        em.replace_with(f"_**{em.get_text(strip=True)}**_")
                    
                    text = text_div.get_text(' ', strip=True)
                    text = text.replace(' - ', '-')
                    text = text.replace(' ;', ';')
                    text = text.replace(' .', '.')
                    return text
            
            elif class_name == 'av-translation':
                text_div = section.find('div', class_='s-justify')
                if text_div:
                    return text_div.get_text(strip=True)
            
            return "Not found: 404"
        
        return {
            'devanagari': get_section('av-devanagari'),
            'bengali': get_section('av-bengali'),
            'verse_text': get_section('av-verse_text'),
            'synonyms': get_section('av-synonyms'),
            'translation': get_section('av-translation'),
            'url': url
        }

    async def search_synonyms(self, word: str, search_type: str = "contains") -> List[Dict[str, any]]:
        """Search Vedabase for word synonyms"""
        url = f"{self.search_url}?original={word}&search={search_type}"
        html = await self.scrape_with_retry(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        search_results = soup.find_all('div', class_='search-result')
        
        for result in search_results[:10]:  # Limit to top 10 meanings
            term = result.find('dt').get_text(strip=True)
            meaning_div = result.find('div', class_='em:text-base')
            meaning = meaning_div.get_text(strip=True) if meaning_div else "No meaning found"
            
            references = []
            for link in result.find_all('a', class_='text-vb-link'):
                ref_text = link.get_text(strip=True)
                ref_url = "https://vedabase.io" + link['href']
                references.append((ref_text, ref_url))
            
            results.append({
                'term': term,
                'meaning': meaning,
                'references': references[:15]  # Limit to top 15 references
            })
            
        return results

    async def close(self) -> None:
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()
        if hasattr(self.ua, 'close'):
            self.ua.close()
