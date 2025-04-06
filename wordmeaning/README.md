<div align="center">
<h1>「modmail-plugins」</h1>
<p><b><i>plugins to expand Modmail2025's functionality 🍆💦🍑</i></b></p>
</div>

<div align="center">
<img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons"><br>
<img src="https://img.shields.io/badge/python-v3.7-12a4ff?style=for-the-badge&logo=python&logoColor=12a4ff">
<img src="https://img.shields.io/badge/library-discord%2Epy-ffbb10?style=for-the-badge">

<p>🛠️ if you experience a problem with any <b>modmail-plugin</b> in this repo, please open an issue or submit a pull-request</p>
<br><br>
</div>

# WordMeaning

Enhanced dictionary plugin with interactive searching capabilities for Wikipedia, UrbanDictionary, and Oxford English Dictionary

## Features

- [x] **`dict`** - Oxford Dictionary search with:
  - Multi-word query support (auto-converts spaces to hyphens)
  - Grammar information display (e.g. `[uncountable]`)
  - Related matches section
  - Supports `examples`, `synonyms`, and `proverbs` as arguments

- [x] **`urban`** - Urban Dictionary with:
  - Interactive pagination through definitions
  - Thumbs up/down counts
  - Clean example formatting

- [x] **`wiki`** - Wikipedia search with:
  - Numbered disambiguation pages (1️⃣-9️⃣)
  - Automatic summary extraction
  - Image thumbnails when available
  - Handles ambiguous searches gracefully

## Installation

🔸 <b>Installation</b>: 
```py
[p]plugin add webkide/modmail-plugins/wordmeaning@master
```

> `[p]` will be your guild's prefix, by default it is **`?`** unless you changed it

## Usage Examples

`?dict love examples` # Shows definitions with usage examples

`?urban yeet` # Urban Dictionary search with pagination

`?wiki pandemonium` # Wikipedia search with disambiguation handling

`?dict music-box` # Multi-word dictionary lookup


## Recent Improvements

✨ **v2.05 Updates**:
- Complete rewrite of dictionary parsing engine
- Added interactive elements for better navigation
- Improved error handling and user feedback
- Enhanced formatting for clearer results
- Multi-word query support in dictionary
- Numbered disambiguation for Wikipedia

