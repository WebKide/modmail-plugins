<div align="center">
<h1>「modmail-plugins」</h1>
<p><b><i>plugins to expand Modmail 2025's functionality 🚀🌟✨</i></b></p>
</div>

<div align="center">
<img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons"><br>
<img src="https://img.shields.io/badge/python-v3.7-12a4ff?style=for-the-badge&logo=python&logoColor=12a4ff">
<img src="https://img.shields.io/badge/library-discord%2Epy-ffbb10?style=for-the-badge&logo=discord">

<br><br>
</div>

# ⭐ Starboard

A fully automated, configurable starboard system that highlights popular messages in your Discord server. When messages receive enough star reactions (⭐), they're automatically posted to a dedicated **#starboard** channel.

## ✨ Key Features

- **Auto-channel creation** - Creates **#starboard** channel in guild if none exists
- **Multi-guild support** - Works in every server your bot is in
- **Smart updates** - Edits starboard posts when:
  - Original message is edited
  - Stars are added/removed
- **Self-cleaning** - Removes posts that fall below star threshold
- **Rich embeds** - Beautiful formatted posts with:
  - Original message content
  - Author info
  - Jump link
  - Star count
  - Supports Image attachments

## 📦 Installation

🔸 <b>Installation</b>: 

```py
{p}plugin add WebKide/modmail-plugins/starboard@master
```

> `{p}` will be your guild's prefix, by default it is **`?`** unless you changed it

## 🔑 How It Works

1. When a message gets ⭐ reactions:
   - Bot checks if it meets the star threshold `(default: 1)`
2. If qualified:
   - Creates embed in **#starboard** channel
   - Adds star reaction to the embed
3. Ongoing maintenance:
   - Updates star count when reactions change
   - Updates content if original message is edited
   - Removes if stars drop below threshold

- **Dynamic Configuration**:
  - Change star emoji and required count anytime
  - Settings stored in channel topic for persistence
  - `?starconfig` command for easy management

- **Auto-Setup**:
  - Creates #starboard channel if missing
  - Sets optimal permissions automatically
  - Welcome message on first creation

- **Smart Processing**:
  - Real-time updates when reactions change
  - Automatic cleanup of unqualified posts
  - Edits sync when original messages change

## ⚙️ Configuration

Configure through channel topic or commands:

### 🔸 Via Command:

> **`{p}starconfig ⭐ 5`**  — Set both emoji and star threshold
> 
> **`{p}starconfig 🌟`**    — Change the emoji used for reaction
>
> **`{p}starconfig reset`** —  Reset to default values (⭐ 1)

`{p}` will be your guild's prefix, by default it is `?starconfig` unless you changed it

### 🔖 Via Channel Topic:

Edit **#starboard's topic** to include:

> **default_emoji:🌟 default_count:3**

<p>🛠️ if you experience a problem with the <b>Starboard plugin</b>, please open an issue or submit a pull-request in this repo<br><br></p>

<br><br>
