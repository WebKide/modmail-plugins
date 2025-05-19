<div align="center">
   <img src="https://i.imgur.com/JxtxCuU.png" alt="ani logo" width="720" />
</div>

------

<div align="center">
   <img src="https://img.shields.io/badge/Modmail%20Plugin-by%20WebKide-black.svg?style=popout&logo=github&logoColor=white" alt="WebKide" />
   <img src="https://img.shields.io/badge/Made%20with-Python%203.10-blue.svg?style=popout&logo=python&logoColor=yellow" alt="Python3" />
   <img src="https://img.shields.io/badge/Library-discord%2Epy%202%2Ex-ffbb10?style=popout&logo=discord">
   <img src="https://img.shields.io/badge/Database-MongoDB-%234ea94b.svg?style=popout&logo=mongodb&logoColor=white" alt="MongoDB" />
</div>

<div align="center">
   <img src="http://forthebadge.com/images/badges/built-with-love.svg?style=for-the-badge" alt="built with love" />
   <img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons">
</div>

<div align="center">
   <h1>「plugins to expand Modmail 2025's functionality 🚀🌟✨」</h1>
</div>

# 🎌 AniList Search Plugin

A powerful **AniList.co** integration for Discord that fetches anime, manga, and character info with rich embeds. Search directly from Discord with paginated results and detailed metadata.

## ✨ Features

- **Multi-type search** - Anime, manga, and characters  
- **Rich embeds** - Cover images, banners, scores, and more  
- **Smart pagination** - Navigate results with buttons  
- **Spoiler-safe** - Automatically cleans HTML/formatting  
- **Cross-linking** - Includes AniList + MAL links  

## 🚀 Commands

### 🎬 Anime Search  
`[p]ani anime <title>`  
- Shows: **Score** ⭐, **Episodes** 📺, **Duration** ⏳, **Genres** 🎭, **Studios** 🏢  
- Example: `?ani anime Attack on Titan`

### 📖 Manga Search  
`[p]ani manga <title>`  
- Shows: **Score** ⭐, **Chapters** 📖, **Genres** 🎭, **Status** 📡  
- Example: `?ani manga Berserk`

### 🎎 Character Search  
`[p]ani character <name>`  
- Shows: **Appears in** 🎞️ (anime/manga), **Description** 📝  
- Example: `?ani character Guts`

## 📦 Installation

```py
[p]plugin add WebKide/modmail-plugins/ani@master
```

> Replace `[p]` with your server's prefix (default: `?`)

## 🔍 Example Output

**`[p]ani anime attack on titan`**

_____________________________________________________________________
### Attack on Titan
> Several hundred years ago, humans were nearly exterminated by titans. Titans are typically several stories tall, seem to have no intelligence, devour human beings and, worst of all, seem to do it for the pleasure rather than as a food source. A small percentage of humanity survived by walling themselves in a city protected by extremely high walls, even taller than the biggest of titans.
Flash forward to the present and the city has not seen a titan in over 100 years. Teenage boy Eren and his foster sister Mikasa witness something horrific as the city walls are destroyed by a colossal titan that appears out of thin air. As the smaller titans flood the city, the two kids watch in horror as their mother is eaten alive. Eren vows that he will murder every single titan and take revenge for all of mankind.

(Source: MangaHelpers)

⭐ **Score:** 84 | 📺 Episodes: 25 | ⏳ Duration: 24m

🏷️ **Genres:** Action, Drama, Fantasy, Mystery

🎥 **Studios:** WIT STUDIO

🔍 **Streaming/Info:** 🔗 Crunchyroll, 🔗 Official Site, 🔗 Hulu, 🔗 Tubi TV, 🔗 Adult Swim

🔍 **More Info:** 🌐 AniList, 🌐 MAL

> Status: Finished, Next episode: Never (ﾉ^ヮ^)ﾉ Powered by AniList.co
_____________________________________________________________________

## ⚙️ Technical Notes

- **Rate Limits**: Respects AniList's GraphQL API limits (90 req/min)  
- **Pagination**: Buttons auto-timeout after 60s  
- **Safety**: All text fields are truncated to respect Discord's limits  

## ❓ FAQ

**Q: Why can't I find a specific anime?**  
A: Try the Japanese/romaji title (e.g., "Shingeki no Kyojin" instead of "Attack on Titan")

**Q: How accurate are the scores?**  
A: Pulls directly from AniList's weighted average system

**Q: Can I search light novels?**  
A: Currently only anime/manga (use manga search for LN adaptations)

## 🐞 Troubleshooting

If searches fail:
1. Check your spelling
2. Verify bot has `Embed Links` permission
3. Try a more specific query

For API issues:  
[Open an Issue](https://github.com/WebKide/modmail-plugins/issues)

---

<div align="center">
<b>Weeb-approved! 🌸 Consider starring if you love it!</b>
</div>
