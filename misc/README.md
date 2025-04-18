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

<div align="center">
  <h1>Miscellaneous Utility Commands</h1>
  <p><b>Useful commands to make your life easier (∩｀-´)⊃━☆ﾟ.*･｡ﾟ</b></p>
</div>

## Overview

This cog contains a collection of utility commands designed to help server administrators and moderators manage their Discord servers more effectively. The commands range from moderation tools to utility functions.

## Features

### Moderation Commands
- **Hackban**: Ban users by ID even if they're not in the server
- **Role Management**: Add/remove roles from members
- **Purge**: Bulk delete messages from a channel

### Bot Management
- **Name**: Change the bot's username
- **Logo**: Change the bot's avatar

### Utility Commands
- **Sauce**: View source code of any command
- **Say/Sayd**: Make the bot send messages (with optional deletion)
- **General (g)**: Send messages to other channels

## Installation

🔸 <b>Installation</b>: `[p]plugin add WebKide/modmail-plugins/misc@master`

> `[p]` will be your guild's prefix, by default it is **`?`** unless you changed it

## Command Details

### 🔨 Moderation

#### `hackban <userid> [reason]`
- **Description**: Ban a user by ID (works even if they left the server)
- **Permissions**: Administrator + Dev List
- **Usage**: `[p]hackban 1234567890 Spamming`

#### `guildrole add/remove <member> <rolename>`
- **Description**: Add or remove roles from members
- **Permissions**: Admin/Mod/Moderator roles
- **Usage**: 
  - `[p]guildrole add @User Member`
  - `[p]guildrole remove @User Member`

#### `purge <amount>`
- **Description**: Delete multiple messages (max 99)
- **Permissions**: Administrator
- **Usage**: `[p]purge 50`

### 🤖 Bot Management

#### `name <new_name>`
- **Description**: Change the bot's username
- **Permissions**: Administrator + Dev List
- **Usage**: `[p]name NewBotName`

#### `logo <image_url>`
- **Description**: Change the bot's avatar
- **Permissions**: Administrator + Dev List
- **Usage**: `[p]logo https://imgur.com/image.png`

### 🛠️ Utilities

#### `sauce <command>`
- **Description**: View source code of any command
- **Permissions**: Administrator
- **Usage**: `[p]sauce purge`

#### `say/sayd <message>`
- **Description**: Make the bot repeat your message (sayd deletes your command)
- **Permissions**: Administrator
- **Usage**: 
  - `[p]say Hello world!`
  - `[p]sayd This will be deleted`

#### `g <channel> <message>`
- **Description**: Send a message to another channel
- **Permissions**: Administrator
- **Usage**: `[p]g #announcements Server maintenance in 10 minutes!`

## Permission Requirements

Most commands require:
- Administrator permissions (`@commands.has_permissions(administrator=True)`)
- Or specific roles: Admin, Mod, Moderator (`@commands.has_any_role()`)
- Some commands are restricted to developers only (hardcoded ID check)

## Notes

- This cog was designed to keep useful but less-frequently-used commands
- Some commands include automatic message deletion for cleaner operation
- Error handling is included for common permission issues

<div align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/discord.py-2.0+-7289DA?style=for-the-badge&logo=discord">
</div>
