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
import json
import re
import io

from discord.ext import commands
from bs4 import BeautifulSoup


class Html2Json(commands.Cog):
    """Convert attached HTML chapter from https://prabhupadabooks.com/bg to JSON file"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='html2json')
    async def html_to_json(self, ctx):
        """Convert attached HTML chapter from https://prabhupadabooks.com/bg to JSON file"""
        if not ctx.message.attachments:
            return await ctx.send("Please attach an HTML file")
        
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith('.html'):
            return await ctx.send("Please attach an HTML file")
        
        try:
            # Download and process the file
            html_content = (await attachment.read()).decode('utf-8')
            json_data = self.html_to_json_converter(html_content)  # Renamed to avoid conflict
            
            # Send as file
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
            await ctx.send(file=discord.File(
                io.StringIO(json_str), 
                filename=f'{attachment.filename[:-5]}.json'
            ))
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    def html_to_json_converter(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = {
            "Chapter-Desc": "",
            "Verses": []
        }
        
        # Get chapter description
        chapter_desc = soup.find('div', class_='Chapter-Desc')
        if chapter_desc:
            result["Chapter-Desc"] = ' '.join(chapter_desc.get_text().split())
        
        # Process each verse block
        current_verse = {}
        for element in soup.find_all(['div', 'span']):
            if not element.get('class'):
                continue
                
            class_name = element['class'][0]
            raw_text = element.get_text()
            
            if not raw_text.strip():
                continue
                
            # Custom text processing per field type
            if class_name == 'Textnum':
                text = ' '.join(raw_text.split())
                if current_verse:
                    result["Verses"].append(current_verse)
                    current_verse = {}
                current_verse["Textnum"] = text
            elif class_name == 'Uvaca-line':
                current_verse["Uvaca-line"] = ' '.join(raw_text.split())
            elif class_name == 'Verse-Text':
                if "Verse-Text" not in current_verse:
                    current_verse["Verse-Text"] = []
                current_verse["Verse-Text"].append(' '.join(raw_text.split()))
            elif class_name == 'Synonyms-Section':
                current_verse["Synonyms-Section"] = raw_text.strip()
            elif class_name == 'Synonyms-SA':
                # Special handling for synonyms
                text = ' '.join(raw_text.split())
                # Fix hyphen spacing cases like "dharma - kṣetre"
                text = re.sub(r'(\w)\s*-\s*(\w)', r'\1-\2', text)
                # Standardize em-dash spacing
                text = re.sub(r'\s*—\s*', ' — ', text)
                # Fix spacing around punctuation
                text = re.sub(r'\s*([,.;])\s*', r'\1 ', text)
                current_verse["Synonyms-SA"] = text
            elif class_name == 'Titles':
                current_verse["Titles"] = raw_text.strip()
            elif class_name == 'Translation':
                # Conservative spacing for translation
                text = ' '.join(raw_text.split())
                # Fix common Sanskrit word boundaries
                text = re.sub(r'([a-zA-Zā-ṣ])\s+([A-Z][a-zā-ṣ])', r'\1 \2', text)
                current_verse["Translation"] = text
        
        # Add the last verse
        if current_verse:
            result["Verses"].append(current_verse)
        
        # Combine multi-line verses
        for verse in result["Verses"]:
            if "Verse-Text" in verse:
                verse["Verse-Text"] = "\n".join(verse["Verse-Text"])
        
        return result

async def setup(bot):
    await bot.add_cog(Html2Json(bot))
