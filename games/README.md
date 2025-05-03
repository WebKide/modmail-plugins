<div align="center">
<h1>「modmail-plugins」</h1>
<p><b><i>plugins to expand Modmail 2025's functionality 🚀🌟✨</i></b></p>
</div>

<div align="center">
<img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons"><br>
<img src="https://img.shields.io/badge/python-v3.7+-12a4ff?style=for-the-badge&logo=python&logoColor=12a4ff">
<img src="https://img.shields.io/badge/library-discord%2Epy%202%2Ex-ffbb10?style=for-the-badge&logo=discord">
<br><br>
</div>

# 🎲 GAMES Plugin

A fun and interactive Modmail plugin that brings a wide variety of text-based games and fortune-telling features to your server. Includes classics like hangman, tarot, dice rolls, I Ching oracle, and more!

## ✨ Features

- 🔮 Text-based oracles: **Tarot**, **I Ching**, **Runes**, **Magic 8-ball**
- 🎮 Mini-games: **Hangman**, **Unscramble**, **Guess the Number**
- 🎲 Randomisers: **Dice**, **Coin Flip**, **Option Chooser**
- 🏆 Game stats and leaderboard system

Perfect for boosting engagement and having fun without needing additional bots.

## 🚀 Commands

| Command | Description |
|--------|-------------|
| `?choose` | Choose between multiple options ✂️ |
| `?cookie` / `?fortune` | Get a random fortune cookie message 🍪 |
| `?eightball` / `?8ball` | Ask the magic 8-ball a question 🎱 |
| `?flip` / `?toss` | Flip a coin or some text 🪙 |
| `?guess` | Guess a number between 1–11 1️⃣ |
| `?hangman` | Start a game of hangman 🪢 |
| `?iching` / `?oracle` | Consult the I Ching oracle 📜 |
| `?roll` / `?dice` | Roll dice in NdN format (e.g. 2d20) 🎲 |
| `?rune` / `?futhark` | Draw a Viking rune 🧿 |
| `?settle` / `?rpsls` | Play Rock-Paper-Scissors-Lizard-Spock 🖖 |
| `?tarot` | Start a tarot reading session 🃏 |
| `?unscramble` | Solve a scrambled word challenge 🔤 |

---

### 📊 Game Stats

| Command | Description |
|---------|-------------|
| `?gamesstats` | View your stats or another user's |
| `?gamesstats outcomes` | Win/Loss stats by game |
| `?gamesleaderboard` | View top players (default: top 10) |

---

## ⚙️ Installation

```py
?plugin add WebKide/modmail-plugins/games@master
```

> Replace `?` with your server's current prefix if it has been changed using `?prefix [new_prefix]`

---

## 🔮 How It Works

Each command is standalone and stateless (unless stats are queried), making this plugin simple and lightweight. No external APIs or setup required.

- Commands are accessible in any server channel
- Media thumbnails are embedded for richer output
- Win/loss tracking is automatic for supported games

---

## 📝 Game Configuration

This plugin comes pre-configured and requires no setup. To change the command prefix:

```
?prefix !
```

---

## 🧾 Permissions Required

Ensure your bot has the following permissions where you expect users to play games:

- `Send Messages`
- `Embed Links`
- `Attach Files`
- `Read Message History`
- `Add Reactions` (for some games)

---

## 🖼️ Media Thumbnails

| Feature | Thumbnail |
|--------|-----------|
| Coin Flip | <img src="https://i.imgur.com/4oKCFyM.png" width="100"> |
| 8-ball | <img src="https://i.imgur.com/GVFY7ry.png" width="100"> |
| Tarot | <img src="https://i.imgur.com/rUAjxYx.png" width="100"> |
| I Ching | <img src="http://i.imgur.com/biEvXBN.png" width="100"> |
| Dice | <img src="https://i.imgur.com/N4d4X3h.png" width="100"> |
| Cookie | <img src="https://i.imgur.com/MHkzgHU.png" width="100"> |
| Hangman | <img src="https://i.imgur.com/EksOlTe.png" width="100"> |
| Unscramble | <img src="https://i.imgur.com/wydPdrN.png" width="100"> |

---

## ❓ FAQ

**Q: Can these games be played in DMs?**  
A: No, since DMs are reserved for contacting Admin/Mods in guild.

**Q: Do any commands require setup?**  
A: No setup or API keys needed. Install **modmail-plugin** and start playing.

**Q: Are stats stored long-term?**  
A: Yes, stats persist using internal storage.

**Q: Is this plugin compatible with other Modmail plugins?**  
A: Yes, it is fully modular and independent.

---

<div align="center">
<b>Enjoy the plugin? Consider starring the repository! ⭐</b>
</div>
