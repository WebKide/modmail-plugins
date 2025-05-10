<div align="center">
<h1><b>💬 DmOnJoin</b><br>「modmail-plugins」</h1>
<p><b><i>plugins to expand Modmail's functionality 🍆💦🍑</i></b> 「2020-2025」</p>

<img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons"><br>
<img src="https://img.shields.io/badge/python-v3.7+-12a4ff?style=for-the-badge&logo=python&logoColor=12a4ff">
<img src="https://img.shields.io/badge/library-discord%2Epy%202%2Ex-ffbb10?style=for-the-badge&logo=discord">
</div>

# Auto-Dm_On_Join Plugin for Modmail

Automatically send customizable welcome DMs to new server members with rich formatting.

## ✨ Features

- **Customizable Welcome Messages** with Markdown support
- **Dynamic Placeholders** for personalized content
- **Automatically DM Members on_join** with important info

## 📋 Commands

### 🛠 Configuration
| Command         | Description                  | Permission |
|-----------------|------------------------------|------------|
| `?setdmmessage` | Set the DM message content   | Admin      |
| `?toggledm`     | Enable/disable automatic DMs | Admin      |

### 🚀 Utilities
| Command          | Description             | Permission |
|------------------|-------------------------|------------|
| `?testdm`        | Send yourself a test DM | Admin      |
| `?help DmOnJoin` | View plugin info        | Admin      |

## 📝 Placeholders

Use these in your DM message:
```
{guild.name} - Server name
{user.display_name} - User's display name
{user.id} - User's Discord ID
{guild.owner} - Server owner mention
```

## 🎨 Formatting Guide
```
# Header 1
## Header 2
### Header 3
-# subheader
**Bold**, *Italic*, ~~Strikethrough~~, `Inline code`, :emoji: 🎉
```css
Code block```
```

## ⚙️ Installation
1. Use the following command:
```bash
?plugin add WebKide/modmail-plugins/dm_on_join@master
```
2. Configure with `?setdmmessage`

> Your prefix is `?` unless you changed it.

## ⚠️ Important Notes
- Always test with `?testdm` first to make sure the formatting looks good
- Only Admins can set the DM message, toggle on/off, test auto DM

## 🌈 Example
```python
?setdmmessage
# Welcome to {guild.name}, {user.display_name}!
We're glad to have you here 🎉

**Server Owner:** {guild.owner}
Need help? *Just ask!*
```

<div align="center">
<img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square">
<img src="https://img.shields.io/badge/Maintained-Yes-green?style=flat-square">
</div>
