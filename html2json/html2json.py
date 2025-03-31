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

    def html_to_json_converter(self, html_content):  # Moved inside class
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = {
            "Chapter-Desc": "",
            "Verses": []
        }
        
        # Get chapter description
        chapter_desc = soup.find('div', class_='Chapter-Desc')
        if chapter_desc:
            result["Chapter-Desc"] = chapter_desc.get_text(strip=True)
        
        # Process each verse block
        current_verse = {}
        for element in soup.find_all(['div', 'span']):
            if not element.get('class'):
                continue
                
            class_name = element['class'][0]
            text = element.get_text(strip=True)
            
            if not text:
                continue
                
            if class_name == 'Textnum':
                if current_verse:  # Save previous verse before starting new one
                    result["Verses"].append(current_verse)
                    current_verse = {}
                current_verse["Textnum"] = text
            elif class_name == 'Uvaca-line':
                current_verse["Uvaca-line"] = text
            elif class_name == 'Verse-Text':
                if "Verse-Text" not in current_verse:
                    current_verse["Verse-Text"] = []
                current_verse["Verse-Text"].append(text)
            elif class_name == 'Synonyms-Section':
                current_verse["Synonyms-Section"] = text
            elif class_name == 'Synonyms-SA':
                # Clean up synonyms text
                synonyms = re.sub(r'\s+', ' ', text).strip()
                synonyms = re.sub(r'\s*-\s*', ' — ', synonyms)
                current_verse["Synonyms-SA"] = synonyms
            elif class_name == 'Titles':
                current_verse["Titles"] = text
            elif class_name == 'Translation':
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
