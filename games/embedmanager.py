import time
from datetime import date, datetime
import discord
from .config import GameConfig, Emoji

class EmbedManager:
    def __init__(self, bot):
        self.bot = bot
        self.colors = {
            name: discord.Colour(value) 
            for name, value in GameConfig.EMBED_COLORS.items()
        }
    
    async def create_command_embed(self, ctx, **kwargs):
        """Standardized embed creation for commands with footer handling"""
        start_time = kwargs.pop('start_time', None)
        additional_footer = kwargs.pop('footer_text', GameConfig.ADVICE_FOOTER)
        
        embed = self.create_base_embed(ctx, **kwargs)
        
        if 'footer' not in kwargs:
            embed.set_footer(**await self.create_command_footer(
                ctx,
                start_time,
                additional_text=additional_footer
            ))
            
        return embed
    
    def create_base_embed(self, ctx, **kwargs):
        """Create basic embed structure without footer"""
        embed = discord.Embed(
            color=kwargs.get('color', self.colors['user']),
            description=kwargs.get('description'),
            timestamp=kwargs.get('timestamp', discord.utils.utcnow())
        )
        
        if title := kwargs.get('title'):
            embed.title = title
        
        if author := kwargs.get('author'):
            embed.set_author(
                name=author.get('name', ctx.author.display_name),
                icon_url=author.get('icon_url', ctx.author.display_avatar.url)
            )
        
        if thumbnail := kwargs.get('thumbnail'):
            embed.set_thumbnail(url=thumbnail)
        
        if image := kwargs.get('image'):
            embed.set_image(url=image)
        
        if fields := kwargs.get('fields'):
            for field in fields:
                embed.add_field(
                    name=field.get('name'),
                    value=field.get('value'),
                    inline=field.get('inline', False)
                )
        
        return embed
    
    async def create_command_footer(self, ctx, start_time=None, additional_text=""):
        """Standardized footer for commands"""
        footer_text = additional_text
        now = datetime.utcnow()
        unix_timestamp = int(now.timestamp())
        short_time = f"<t:{unix_timestamp}:t>"  # 't' = short time
        short_t = now.strftime("%H:%M")
        if start_time:
            duration = time.time() - start_time
            footer_text += f" 𝗉𝗋𝗈𝖼𝖾𝗌𝗌𝖾𝖽 𝗂𝗇 {duration*1000:.2f}𝗆𝗌"
        footer_text += f" | {short_t}"
        footer_text += f" | 𝗉𝗂𝗇𝗀: {self.bot.latency*1000:.2f}𝗆𝗌"
        
        return {
            'text': footer_text.strip(" | "),
            'icon_url': ctx.author.display_avatar.url
        }
    
    async def create_oracle_embed(self, ctx, *, title, description, image_url, color_name='user', start_time=None):
        """Standardized embed for oracle-type commands (tarot, iching, runes)"""
        return await self.create_command_embed(
            ctx,
            title=title,
            description=description,
            color=self.colors.get(color_name, self.colors['user']),
            thumbnail=image_url,
            start_time=start_time
        )
    
    async def create_game_result_embed(self, ctx, *, result, player_choice, bot_choice, start_time=None):
        """Standardized embed for game results (RPSLS, guess, etc.)"""
        if result == 1:  # Win
            color = self.colors['success']
            result_text = "You win!"
            icon = Emoji.DIAMOND
        elif result == 0:  # Lose
            color = self.colors['error']
            result_text = "You lose..."
            icon = Emoji.NO_ENTRY
        else:  # Draw
            color = self.colors['mod']
            result_text = "We're square"
            icon = Emoji.BEGINNER
        
        return await self.create_command_embed(
            ctx,
            color=color,
            fields=[
                {
                    'name': f'{self.bot.user.display_name} chose:',
                    'value': bot_choice,
                    'inline': True
                },
                {
                    'name': f'{ctx.author.display_name} chose:',
                    'value': player_choice,
                    'inline': True
                }
            ],
            footer_text=f"{icon} {result_text}",
            start_time=start_time
        )
