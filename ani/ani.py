"""
MIT License
Copyright (c) 2020 WebKide [d.id @323578534763298816]
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
__version__ = "v0.09 — MyAnimeList, inline=False"

import discord, traceback, asyncio, datetime, json, re, aiohttp, html
from discord.ext import commands
from discord.ui import Button, View

SEARCH_ANIME_MANGA_QUERY = """
query ($id: Int, $page: Int, $search: String, $type: MediaType) {
    Page (page: $page, perPage: 10) {
        media (id: $id, search: $search, type: $type) {
            id
            idMal
            description(asHtml: false)
            title {
                english
                romaji
            }
            coverImage {
                    medium
            }
            bannerImage
            averageScore
            meanScore
            status
            episodes
            chapters
            duration
            genres
            studios(isMain: true) {
                nodes {
                    name
                }
            }
            season
            seasonYear
            externalLinks {
                url
                site
            }
            nextAiringEpisode {
                timeUntilAiring
            }
        }
    }
}
"""

SEARCH_CHARACTER_QUERY = """
query ($id: Int, $page: Int, $search: String) {
  Page(page: $page, perPage: 10) {
    characters(id: $id, search: $search) {
      id
      description (asHtml: true),
      name {
        first
        last
        native
      }
      image {
        large
      }
      media {
        nodes {
          id
          type
          title {
            romaji
            english
            native
            userPreferred
          }
        }
      }
    }
  }
}
"""

SEARCH_USER_QUERY = """
query ($id: Int, $page: Int, $search: String) {
    Page (page: $page, perPage: 10) {
        users (id: $id, search: $search) {
            id
            name
            siteUrl
            avatar {
                    large
            }
            about (asHtml: true),
            stats {
                watchedTime
                chaptersRead
            }
            favourites {
            manga {
              nodes {
                id
                title {
                  romaji
                  english
                  native
                  userPreferred
                }
              }
            }
            characters {
              nodes {
                id
                name {
                  first
                  last
                  native
                }
              }
            }
            anime {
              nodes {
                id
                title {
                  romaji
                  english
                  native
                  userPreferred
                }
              }
            }
            }
        }
    }
}
"""

class PaginatorView(View):
    def __init__(self, embeds):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.current_page = 0
        self.message = None
        
    async def update_embed(self, interaction):
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_embed(interaction)
        
    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await self.update_embed(interaction)
            
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        self.stop()

class Ani(commands.Cog):
    """(∩｀-´)⊃━☆ﾟ.*･｡ﾟ Kawaii Anirisuto (AniList) sagashi komando, uwu """
    def __init__(self, bot):
        self.bot = bot
        self.url = "https://graphql.anilist.co"

    def format_name(self, first_name, last_name):
        if first_name and last_name:
            return first_name + " " + last_name
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return "No name"

    def clean_html_entities(self, text):
        """Converts all HTML entities (&quot; &amp; etc) to their characters"""
        return html.unescape(text) if text else text

    def clean_html(self, description):
        if not description:
            return ""
        cleanr = re.compile("<.*?>")
        cleantext = re.sub(cleanr, "", description)
        return cleantext

    def clean_spoilers(self, description):
        if not description:
            return ""
        cleanr = re.compile("/<span[^>]*>.*</span>/g")
        cleantext = re.sub(cleanr, "", description)
        return cleantext

    def description_parser(self, description):
        description = self.clean_html_entities(description)
        description = self.clean_spoilers(description)
        description = self.clean_html(description)
        description = "\n".join(description.split("\n")[:5])
        if len(description) > 1080:
            return description[:1080] + "..."
        else:
            return description

    def list_maximum(self, items):
        if len(items) > 5:
            return items[:5] + ["+ " + str(len(items) - 5) + " more"]
        else:
            return items

    async def _request(self, query, variables=None):
        if variables is None:
            variables = {}

        request_json = {"query": query, "variables": variables}
        headers = {"content-type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, data=json.dumps(request_json), headers=headers) as response:
                return await response.json()

    async def _search_anime_manga(self, ctx, cmd, entered_title):
        MediaStatusToString = {
            "FINISHED": "Finished",
            "RELEASING": "Releasing",
            "NOT_YET_RELEASED": "Not yet released",
            "CANCELLED": "Cancelled",
        }

        SeasonToString = {
            "WINTER": "Winter",
            "SPRING": "Spring",
            "SUMMER": "Summer",
            "FALL": "Fall"
        }

        variables = {"search": entered_title, "page": 1, "type": cmd}
        data = (await self._request(SEARCH_ANIME_MANGA_QUERY, variables))["data"]["Page"]["media"]

        if data is not None and len(data) > 0:
            embeds = []

            for anime_manga in data:
                link = f"https://anilist.co/{cmd.lower()}/{anime_manga['id']}"
                description = anime_manga["description"]
                title = anime_manga["title"]["english"] or anime_manga["title"]["romaji"]
                
                if anime_manga.get("nextAiringEpisode"):
                    seconds = anime_manga["nextAiringEpisode"]["timeUntilAiring"]
                    time_left = str(datetime.timedelta(seconds=seconds))
                else:
                    time_left = "Never"

                # Format genres
                genres = ", ".join(anime_manga.get("genres", [])) or "N/A"
                
                # Format studios (only main studios)
                studios = ", ".join([studio["name"] for studio in anime_manga.get("studios", {}).get("nodes", [])]) or "N/A"
                
                # Format season info
                season_info = ""
                if anime_manga.get("season") and anime_manga.get("seasonYear"):
                    season_info = f"{SeasonToString.get(anime_manga['season'], anime_manga['season'])} {anime_manga['seasonYear']}"
                elif anime_manga.get("seasonYear"):
                    season_info = str(anime_manga["seasonYear"])
                
                external_links = ""
                for i in range(0, len(anime_manga["externalLinks"])):
                    ext_link = anime_manga["externalLinks"][i]
                    external_links += f"🔗 [{ext_link['site']}]({ext_link['url']}), "
                    if i + 1 == len(anime_manga["externalLinks"]):
                        external_links = external_links[:-2]

                embed = discord.Embed(title=title)
                embed.url = link
                embed.color = 3447003
                embed.description = self.description_parser(description)
                embed.set_thumbnail(url=anime_manga["coverImage"]["medium"])
                
                if cmd == "ANIME":
                    embed.add_field(name="⭐ Score:", value=f'`{anime_manga.get("averageScore", "N/A")}`', inline=False)
                    embed.add_field(name="🎬 Episodes:", value=f'`{anime_manga.get("episodes", "N/A")}`', inline=False)
                    embed.add_field(name="⏳ Duration:", value=f"`{anime_manga.get('duration', 'N/A')} mins`", inline=False)
                    embed.add_field(name="🏷️ Genres:", value=f"```fix\n{genres}```", inline=False)
                    embed.add_field(name="🎥 Studios:", value=studios, inline=False)
                    if season_info:
                        embed.add_field(name="📅 Season:", value=season_info, inline=False)
                    
                    embed.set_footer(text="Status: " + MediaStatusToString[anime_manga["status"]] + 
                                    ", Next episode: " + time_left + 
                                    " (ﾉ^ヮ^)ﾉ Powered by AniList.co")
                else:
                    embed.add_field(name="⭐ Score:", value=f'`{anime_manga.get("averageScore", "N/A")}`', inline=False)
                    embed.add_field(name="📖 Chapters:", value=f'`{anime_manga.get("chapters", "N/A")}`', inline=False)
                    embed.add_field(name="🏷️ Genres:", value=f"```fix\n{genres}```", inline=False)
                    if season_info:
                        embed.add_field(name="🎞️ Published:", value=season_info, inline=False)
                    
                    embed.set_footer(text="Status: " + MediaStatusToString.get(anime_manga.get("status"), "N/A") + 
                                    " (ﾉ^ヮ^)ﾉ Powered by AniList.co")
                
                if external_links:
                    embed.add_field(name="🔍 Streaming/Info", value=external_links, inline=False)
                
                if anime_manga["bannerImage"]:
                    embed.set_image(url=anime_manga["bannerImage"])
                
                embed.add_field(name="🔍 More Info", 
                               value=f"🌐 [AniList]({link}), 🌐 [MyAnimeList](https://myanimelist.net/{cmd.lower()}/{anime_manga['idMal']})", 
                               inline=False)
                
                embeds.append(embed)

            return embeds, data
        else:
            return None

    async def _search_character(self, ctx, entered_title):
        variables = {"search": entered_title, "page": 1}
        data = (await self._request(SEARCH_CHARACTER_QUERY, variables))["data"]["Page"]["characters"]

        if data is not None and len(data) > 0:
            embeds = []

            for character in data:
                link = f"https://anilist.co/character/{character['id']}"
                character_anime = [f'[{anime["title"]["userPreferred"]}]({"https://anilist.co/anime/" + str(anime["id"])})' for anime in character["media"]["nodes"] if anime["type"] == "ANIME"]
                character_manga = [f'[{manga["title"]["userPreferred"]}]({"https://anilist.co/manga/" + str(manga["id"])})' for manga in character["media"]["nodes"] if manga["type"] == "MANGA"]
                embed = discord.Embed(title=self.format_name(character["name"]["first"], character["name"]["last"]))
                embed.url = link
                embed.color = 3447003
                embed.description = self.description_parser(character["description"])
                embed.set_thumbnail(url=character["image"]["large"])
                if len(character_anime) > 0:
                    embed.add_field(name="🎦 Anime", value="\n".join(self.list_maximum(character_anime)))
                if len(character_manga) > 0:
                    embed.add_field(name="📚 Manga", value="\n".join(self.list_maximum(character_manga)))
                embed.set_footer(text="Powered by AniList.co")
                embeds.append(embed)

            return embeds, data
        else:
            return None

    async def _search_user(self, ctx, entered_title):
        variables = {"search": entered_title, "page": 1}
        data = (await self._request(SEARCH_USER_QUERY, variables))["data"]["Page"]["users"]

        if data is not None and len(data) > 0:
            embeds = []

            for user in data:
                link = f"https://anilist.co/user/{user['id']}"
                title = user["name"]

                embed = discord.Embed(title=title)
                embed.url = link
                embed.color = 3447003
                embed.description = self.description_parser(user["about"])
                embed.set_thumbnail(url=user["avatar"]["large"])
                embed.add_field(name="📺 Watched time", value=datetime.timedelta(minutes=int(user["stats"]["watchedTime"])))
                embed.add_field(name="📒 Chapters read", value=user["stats"].get("chaptersRead", "N/A"), inline=False)
                for category in "anime", "manga", "characters":
                    fav = []
                    for node in user["favourites"][category]["nodes"]:
                        url_path = category
                        if category == "characters":
                            name = node["name"]
                            title = self.format_name(name["first"], name["last"])
                            url_path = "character"
                        else:
                            title = node["title"]["userPreferred"]

                        fav.append(f'🌐 [{title}](https://anilist.co/{url_path}/{node["id"]})')

                    if fav:
                        embed.add_field(name=f"🎯 Favorite {category}", value="\n".join(self.list_maximum(fav)), inline=False)
                embed.set_footer(text="Powered by Anilist")
                embeds.append(embed)

            return embeds, data
        else:
            return None

    @commands.group(invoke_without_command=True)
    async def ani(self, ctx):
        """Group command"""
        await ctx.send("Search for Anime, Manga, or Character:\n**Sub-commands**\n├─ anime - Search anime using Anilist├─ character - Search characters using Anilist\n└─ manga - Search manga using Anilist", delete_after=69)

    @ani.command()
    async def anime(self, ctx, *, entered_title):
        """Search anime using Anilist"""
        try:
            await ctx.channel.typing()
            cmd = "ANIME"
            embeds, data = await self._search_anime_manga(ctx, cmd, entered_title)

            if embeds is not None:
                view = PaginatorView(embeds)
                view.message = await ctx.send(embed=embeds[0], view=view)
            else:
                await ctx.send("No anime was found or there was an error in the process")
        except TypeError:
            await ctx.send("No anime was found or there was an error in the process")

    @ani.command()
    async def manga(self, ctx, *, entered_title):
        """Search manga using Anilist"""
        try:
            await ctx.channel.typing()
            cmd = "MANGA"
            embeds, data = await self._search_anime_manga(ctx, cmd, entered_title)

            if embeds is not None:
                view = PaginatorView(embeds)
                view.message = await ctx.send(embed=embeds[0], view=view)
            else:
                await ctx.send("No mangas were found or there was an error in the process")
        except TypeError:
            await ctx.send("No mangas were found or there was an error in the process")

    @ani.command()
    async def character(self, ctx, *, entered_title):
        """Search characters using Anilist"""
        try:
            await ctx.channel.typing()
            embeds, data = await self._search_character(ctx, entered_title)

            if embeds is not None:
                view = PaginatorView(embeds)
                view.message = await ctx.send(embed=embeds[0], view=view)
            else:
                await ctx.send("No characters were found or there was an error in the process")
        except TypeError:
            await ctx.send("No characters were found or there was an error in the process")

async def setup(bot):
    await bot.add_cog(Ani(bot))
