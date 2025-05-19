<div align="center">
   <img src="https://i.imgur.com/tQzb7B2.png" alt="transform logo" width="720" />
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

# 🪄 Transform

This Discord.py Plugin provides various **text transformation utilities** to ✨ have fun ✨ in your Guild — from Unicode decoding to banner shouting.

## 💫 Key Features

* 🤖 **AI-powered word generation** using Markov chains
* 🅰️ **ASCII Banner Generator** (`!banner` group):

  * `2linesthick`, `3linethick`, `3linethin`, `3lineingle`, `3linedouble`
* 🔡 **Stylish Text Transformers**:

  * ᵗⁱⁿʸ, 𝒸𝓊𝓇𝓈𝒾𝓋ℯ, 𝕕𝕠𝕦𝕓𝕝𝕖-𝕤𝕥𝕣𝕦𝕔𝕜
  * 𝐁𝐨𝐥𝐝, 𝘽𝙤𝙡𝙙𝙄𝙩𝙖𝙡𝙞𝙘, 𝕲𝖔𝖙𝖍𝖎𝖈, 𝓘𝓽𝓪𝓵𝓲𝓬
  * sᴍᴀʟʟ ᴄᴀᴘs, 1337 5P34K, MoCkInG CaSe
  * ＶＡＰＯＲ, 𝖲𝖺𝗇𝗌-𝗌𝖾𝗋𝗂𝖿, Z͌͆a͠l̓g͊ő
* 🔠 **Unicode ↔ Character Info**:

  * View Unicode name and codepoint (`!charinfo @`)
  * Convert escapes to actual characters (`!charinfo \N{WHITE HEAVY CHECK MARK}`)
* 🏛️ **Caesar Cipher** with optional rotation `(default: 13)`
* 💾 **Binary Encoder/Decoder**
* 🕺 **Fun Modifiers** (👏, 🙏)

---


## 🧪 Commands List:
- [x] **`!ainame`** - Generate fantasy names that sound authentic
- [x] **`!caesar`** - Apply Caesar cipher with optional rot `(default: 13)`
- [x] **`!charinfo`** - Transform 𝐔𝐧𝐢𝐜𝐨𝐝𝐞 <--> 𝐂𝐡𝐚𝐫𝐚𝐜𝐭𝐞𝐫
- [x] **`!binary`** - Smart binary 8-16-32-bit converter with format detection
- [x] **`!banner`** - Convert text to 3-line ASCII banners
  - [x] ├─ **`2linesthick`** - Convert text to 2-line ASCII banners
  - [x] ├─ **`3linedouble`** - Convert text to 3-double-line ASCII banners
  - [x] ├─ **`3linesingle`** - Convert text to 3-single-line ASCII banners
  - [x] ├─ **`3linethick`** - Convert text to 3-double-line ASCII banners
  - [x] └─ **`3linethin`** - Convert text to 3-single-line ASCII banners
- [x] **`!bold`** - Convert text to 𝐁𝐨𝐥𝐝
- [x] **`!bolditalic`** - Convert text to 𝘽𝙤𝙡𝙙𝙄𝙩𝙖𝙡𝙞𝙘
- [x] **`!cursive`** - Convert text to 𝒸𝓊𝓇𝓈𝒾𝓋ℯ
- [x] **`!double`** - Convert text to 𝕕𝕠𝕦𝕓𝕝𝕖-𝕤𝕥𝕣𝕦𝕔𝕜
- [x] **`!gothic`** - Convert text to 𝕲𝖔𝖙𝖍𝖎𝖈
- [x] **`!italic`** - Convert text to 𝓘𝓽𝓪𝓵𝓲𝓬
- [x] **`!leet`** - Convert text to 1337 5P34K
- [x] **`!mock`** - Convert text to MoCkInG CaSe (alternating case)
- [x] **`!sans`** - Convert text to 𝖲𝖺𝗇𝗌-𝗌𝖾𝗋𝗂𝖿
- [x] **`!smallcaps`** - Convert text to sᴍᴀʟʟ ᴄᴀᴘs
- [x] **`!tiny`** - Convert text to ᵗⁱⁿʸ ᶜʰᵃʳᵃᶜᵗᵉʳˢ
- [x] **`!vapor`** - Convert text to ＶＡＰＯＲＷＡＶＥ ＡＥＳＴＨＥＴＩＣ
- [x] **`!zalgo`** - Convert your text to z̧a͠l̜ͭg̑̃o̯ͪ͢ 
- [x] **`!pray`** - Add 🙏 between 🙏 words 🙏
- [x] **`!clap`** - Add 👏 between 👏 words 👏

---

## 🔧 Installation

```diff
!plugin add WebKide/modmail-plugins/transform@master
```

> Replace `!` with your server's prefix (by dafault: `?`)

---

# EXAMPLES:

## 🤖 AI Fantasy Name Generator

### `!ainame 23`

```bf
Adreis, Thea, Aphai, Ibryok, Oquoshor, Ivegas,
Uchomicha, Unoep, Aviush, Idrai, Oqud, Ufien,
Ish, Amama, Oziu, Amay, Amohith, Ymueach, Awayen,
Ehit, Iyoueu, Uric, Ewapan
```

---

## 🔐 Caesar Cipher

#### `!caesar` encode or decode messages

Caesar cipher applied with `rot=13`

**Input:** `Hello World`

**Result:** `Uryyb Jbeyq`

---

## 8️⃣ Binary [8-16-32] bit

#### `!binary 8 hello`

**Input:** `hello`

**Result:** `01101000 01100101 01101100 01101100 01101111`

---

#### `!binary 16 0000000001101000 0000000001100101 0000000001101100 0000000001101100 0000000001101111`

**Input:** `0000000001101000 0000000001100101 0000000001101100 0000000001101100 0000000001101111`

**Result:** `hello`

---

#### `!binary 32 hello`

**Input:** `hello`

**Result:** `00000000000000000000000001101000 00000000000000000000000001100101 00000000000000000000000001101100 00000000000000000000000001101100 00000000000000000000000001101111`

---

## 

####

---

## 🔡 Example Banners

#### `!banner 2linesthick holly cow`

```
█░█ █▀█ █░░ █░░ █▄█   █▀▀ █▀█ █░█░█ 
█▀█ █▄█ █▄▄ █▄▄ ░█░   █▄▄ █▄█ ▀▄▀▄▀ 
```

#### `!banner 3lineingle world cup`

```
┬ ┬┌─┐┬─╮┬  ┌─╮   ┌─┐┬ ┬┌─┐
││││ │├┬┘│  │ │   │  │ │├─┘
└┴┘└─┘┴╰─┴─┘┴─┘   └─┘╰─╯┴  
```

#### `!banner 3linethin modmail`

```
┌┬┐┌─┐┌─╮┌┬┐╭─╮┬┬  
╽╽╽╽ ╽╽ ╽╽╽╽┟─┧╽╽  
┻ ┻┗━┛┻━┛┻ ┻┻ ┻┻┻━┛
```

#### `!banner 3linedouble love 69`

```
╦  ╔═╗╦ ╦╔═╗   ╔══╔═╗
║  ║ ║╚╗║╠═    ╠═╗╚═╣
╩═╝╚═╝ ╚╝╚═╝   ╚═╝══╝
```

#### `!banner 3linethick supreme`

```
█▀▀░█░░█░█▀▀█░█▀▀█░█▀▀▀░█▀▄▀█░█▀▀▀░
▀▀█░█░░█░█░░█░█▄▄▀░█▀▀░░█░▀░█░█▀▀░░
▀▀▀░░▀▀▀░█▀▀▀░▀░▀▀░▀▀▀▀░▀░░░▀░▀▀▀▀░
```
---
