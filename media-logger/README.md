<div align="center">
   <img src="https://i.imgur.com/FvjmfXC.png" alt="media-logger logo" width="720" />
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

# 📁 MediaLogger - Advanced Media Tracking for Modmail

![Banner](https://i.imgur.com/l9yCq6n.png)  
*The ultimate media logging solution for Discord communities of all sizes*

## ✨ Features

- **Smart file filtering** (images, videos, documents, etc.)
- **Adaptive performance** (auto-adjusts for server size)
- **User upload statistics** (small servers only)
- **Channel-specific tracking**
- **Bot media exclusion**
- **Beautiful embed logging**

## ⚙️ Installation

```bash
?plugin add WebKide/modmail-plugins/media-logger@master
```

## 🎚️ Command Reference

| Command | Description | Permission Level |
|---------|-------------|------------------|
| **⚙️ Setup Commands for Admins** | | |
| `?setmedialogchannel` | Set media logging channel | Admin |
| `?medialogtracking` | Set opt-in/global channel mode | Admin |
| `?medialogaddchannel` | Whitelist specific channel | Admin |
| `?medialogignore` | Blacklist a channel | Admin |
| **🎛️ Configuration for Admins** | | |
| `?medialogtypes` | Toggle monitored file extensions | Admin |
| `?medialogtogglebots` | Enable/disable bot media logging | Admin |
| `?medialogconfig enable` | Enable advanced tracking | Admin |
| `?medialogconfig disable` | Disable advanced tracking | Admin |
| `?medialogconfig force_enable` | Bypass server size limits | Owner |
| `?medialogconfig force_disable` | Enforce safety limits | Owner |
| **📊 Statistics for Mods** | | |
| `?medialog` | Show current settings overview | Mod |
| `?medialoggerstats` | Server-wide upload analytics | Mod |
| `?medialoggerstats @user` | Individual user statistics | Mod |
| **🗃️ Information** | | |
| `?medialogabout` | Display plugin info/disclaimer | All Users |

## 🛠️ Configuration Guide

---
### 🔹 For Small Servers (<1000 members)

1. **Set your log channel**  
   ```
   ?setmedialogchannel #media-logs
   ```

2. **Configure file types** (interactive menu)  
   ```
   ?medialogtypes
   ```
   *Use buttons to enable/disable file types*

3. **(Optional) Track user statistics**  
   ```
   ?medialogconfig enable
   ```
   *Gives access to user-specific upload stats*

4. **Recommended for small servers**:  
   - Enable all features
   - Use `?medialogstats @user` to view individual activity
   - Keep advanced tracking enabled

---
### 🔹 For Large Servers (>1000 members)

1. **Set your log channel**  
   ```
   ?setmedialogchannel #media-logs
   ```

2. **Optimize performance**:  
   ```
   ?medialogtracking opt-in
   ```
   ```
   ?medialogignore #very-active-channel
   ```

3. **Recommended for large servers**:  
   - Use opt-in channel tracking
   - Ignore high-traffic channels
   - Disable advanced statistics:
     ```
     ?medialogconfig disable
     ```

---
## 💡 Pro Tips

1. **For art servers**: Enable all image types but disable archives
2. **For document-heavy servers**: Focus on PDF/DOC files
3. **Use `?medialog`** to check your current configuration
4. **Large servers**: Set tracking to "opt-in" mode for best performance

## ⚠️ Troubleshooting

**Problem**: Bot isn't logging files  
✅ Fix:  
1. Check channel permissions
2. Verify file types are enabled (`?medialogtypes`)
3. Ensure channel isn't ignored (`?medialog`)

**Problem**: High memory usage  
✅ Fix:  
1. Disable statistics (`?medialogconfig disable`)
2. Set to opt-in mode (`?medialogtracking opt-in`)
3. Ignore busy channels

---

📊 *Adapts automatically to your server's needs*  
🛡️ *Built for Modmail stability*  
🎨 *Beautiful, organized media logging*

---

- __original__ = "code inspired by @fourjr media-logger"
- __source__ = "https://github.com/fourjr/modmail-plugins/blob/v4/media-logger/media-logger.py"
- __author__ = "WebKide"
- __version__ = "0.2.11"
- __codename__ = "media-logger"
- __copyright__ = "MIT License 2020-2025"
- __description__ = "Enhanced Modmail plugin for media logging with smart user tracking"
- __installation__ = "!plugin add WebKide/modmail-plugins/media-logger@master"

