<div align="center">
<h1>「BhagavadGita Cog」</h1>
<p><b><i>Access the wisdom of the Bhagavad Gītā directly using this Discord.py plugin</i></b></p>
</div>

<div align="center">
<img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons"><br>
<img src="https://img.shields.io/badge/python-v3.7+-12a4ff?style=for-the-badge&logo=python&logoColor=12a4ff">
<img src="https://img.shields.io/badge/library-discord%2Epy-ffbb10?style=for-the-badge">

<p>🛠️ If you experience any issues with this plugin, please open an issue or submit a pull-request</p>
<br><br>
</div>

# Bhagavad Gītā Sloka Finder

This plugin provides instant access to verses from the Bhagavad Gītā with complete Sanskrit (Devanagari), transliteration, synonyms, and English translation. Data is sourced from [Vedabase.io](https://vedabase.io) and intelligently cached for performance.

# Installation

🔸 <b>Installation</b>: `{p}plugin add WebKide/modmail-plugins/bhagavadgita@master`

> `{p}` will be your guild's prefix, by default it is **`?`** unless you changed it

- - - -

This powerful plugin supports both single verses and verse ranges, with automatic handling of Vedabase.io's grouped verses.

#### Usage and Examples ####
|    **Command**  	 	|    **Description**  	 	|    **Example Output**    |
|:-----------------------:	|:-----------------------:	|:----------------------:	|
|  Single Verse  |  `{p}bg 2.13`  |    Returns BG 2.13 with Devanagari, transliteration, synonyms and translation  |
|  Verse Range  |  `{p}bg 6.20-23`  |    Returns all verses in the range with condensed information  |
|  Grouped Verses  |  `{p}bg 1.16`  |    Automatically returns full grouped range (16-18)  |
|  Chapter Info  |  `{p}bg 18.1`  |    Shows total verses available in each chapter  |

## Features

- **Complete Verse Information**:
  - Original Devanagari text
  - Roman transliteration
  - Word-by-word synonyms
  - English translation

- **Intelligent Caching**:
  - Automatically caches verses for faster access
  - Smart grouping of verses according to Vedabase.io's structure
  - Cache expiration after 30 days of inactivity

- **Error Handling**:
  - Validates chapter and verse numbers
  - Handles invalid ranges gracefully
  - Provides helpful error messages

## Technical Details

- **Data Source**: [Vedabase.io](https://vedabase.io/en/library/bg)
- **Cache**: MongoDB with automatic updates
- **Performance**: Async HTTP requests with connection pooling
- **Pagination**: Automatic splitting of long verse ranges into multiple embeds

## Example Output

```markdown
[Embed] Bhagavad Gītā 2.13
────────────────────────────
**Devanagari**: देहिनोऽस्मिन्यथा देहे...
**Transliteration**: dehino 'smin yathā dehe...
**Synonyms**: dehinaḥ—of the embodied; asmin—in this; yathā—as; dehe—in the body...
**Translation**: As the embodied soul continuously passes, in this body, from boyhood to youth to old age...
────────────────────────────
From Vedabase.io | [View Online](https://vedabase.io/en/library/bg/2/13/)
