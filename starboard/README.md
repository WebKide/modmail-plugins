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

# ⭐ Starboard Plugin

A fully automated, configurable starboard system that highlights popular messages in your Discord server. When messages receive enough star reactions, they're automatically posted to a dedicated **#starboard** channel with rich media support.

## ✨ Enhanced Features

- **Multi-media support** - Handles images, videos, and all file attachments
- **Batch file processing** - Supports multiple attachments per message (up to 5 files per batch)
- **Smart content preservation** - Maintains original message formatting and embeds
- **Auto-channel setup** - Creates **#starboard** with optimal permissions if missing
- **Cross-server ready** - Fully isolated configuration per guild
- **Self-maintaining** - Automatic updates and cleanup

## 🚀 New Functionality

✅ **Full file attachment support**  
- Images display in embed
- Videos show as clickable links  
- Other files appear as downloadable attachments  
- Handles multiple files per message  

✅ **Enhanced media handling**  
- Preserves original message embeds  
- Merges rich content seamlessly  
- Smart file size limits (8MB max)  

✅ **Improved reliability**  
- Better error handling for edge cases  
- More robust permission checks  
- Efficient message processing  

## 📦 Installation

```py
{p}plugin add WebKide/modmail-plugins/starboard@master
```

> Replace `{p}` with your server's prefix (default: `?`)

## 🔍 How It Works

1. **Reaction Detection**  
   - Monitors for configured star emoji (default: ⭐)
   - Ignores bot reactions and self-stars

2. **Qualification Check**  
   - Compares against star threshold (default: 1)
   - Verifies channel isn't ignored

3. **Starboard Posting**  
   - Creates rich embed with:  
     - Original content  
     - Author info  
     - Jump link  
     - Star count  
     - Attachments  
   - Adds star reaction to new post

4. **Dynamic Updates**  
   - Live star count updates  
   - Message edit synchronization  
   - Automatic removal if stars drop below threshold

## ⚙️ Configuration

### 🛠️ Command Options

| Command | Description | Example |
|---------|-------------|---------|
| `{p}starconfig <emoji> <count>` | Set both emoji and threshold | `?starconfig 🌟 5` |
| `{p}starconfig <emoji>` | Change just the reaction emoji | `?starconfig 💫` |
| `{p}starconfig reset` | Reset to defaults (⭐ 1) | `?starconfig reset` |

### 📝 Channel Topic Configuration

Edit **#starboard** channel topic with:

```
default_emoji:🌟 default_count:3
```

## 🔐 Permission Requirements

The bot requires these permissions in the starboard channel:

- `View Channel`
- `Send Messages`
- `Embed Links`
- `Attach Files`
- `Manage Messages`
- `Add Reactions`
- `Read Message History`

Verify permissions with:  
`{p}check_starboard_perms`

## 🖼️ Media Support

**Supported Content Types:**
- Images (PNG, JPG, GIF, etc.)
- Videos (MP4, MOV, etc.)
- Documents (PDF, TXT, etc.)
- Other files (ZIP, EXE, etc.)

**Handling Notes:**
- First image becomes embed thumbnail
- Videos show as clickable links
- Other files appear as attachments
- Maximum 8MB file size
- Up to 5 files per batch

## ❓ Frequently Asked Questions

**Q: Can I use custom emojis?**  
A: Yes! Any emoji (including server custom emojis) can be set as the reaction trigger.

**Q: What happens if a message is deleted?**  
A: The starboard post will remain but the jump link will stop working.

**Q: Can I exclude certain channels?**  
A: Yes, add channel IDs to `ignored_channels` in the cog code.

**Q: How many files can be attached?**  
A: The bot will process up to 5 files per message batch.

## 🐛 Troubleshooting

If you encounter issues:
1. Verify bot permissions with `{p}check_starboard_perms`
2. Check for console errors
3. Ensure files are under 8MB
4. Confirm the channel isn't in ignored_channels

For persistent issues, please [open an issue](https://github.com/WebKide/modmail-plugins/issues) with:
- Error messages
- Reproduction steps
- Screenshots if applicable

---

<div align="center">
<b>Enjoy the plugin? Consider starring the repository! ⭐</b>
</div>
