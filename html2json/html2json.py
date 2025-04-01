import discord
import json
import re
import io

from discord.ext import commands
from bs4 import BeautifulSoup


class Html2Json(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='html2json')
    async def html_to_json(self, ctx):  # Missing self parameter
        """Convert attached HTML file to JSON"""
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
