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

## 🛠️ Configuration Guide

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

## 🎚️ Command Reference

| Command | Description | Permission Level |
|---------|-------------|------------------|
| `?setmedialogchannel #channel` | Set logging channel | Admin |
| `?medialogtypes` | Configure file types | Admin |
| `?medialogignore #channel` | Toggle channel ignore | Admin |
| `?medialogstats @user` | View user upload stats | Mod |
| `?medialogconfig enable/disable` | Toggle statistics | Admin |

## 💡 Pro Tips

1. **For art servers**: Enable all image types but disable archives
2. **For document-heavy servers**: Focus on PDF/TXT files
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
- __version__ = "0.0.6"
- __codename__ = "media-logger"
- __copyright__ = "MIT License 2020-2025"
- __description__ = "Enhanced Modmail plugin for media logging with smart user tracking"
- __installation__ = "!plugin add WebKide/modmail-plugins/media-logger@master"

