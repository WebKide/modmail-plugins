<div align="center">
   <img src="https://i.imgur.com/Qc6Ifsg.png" alt="quote logo" width="360" />
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

A Discord.py **modmail-plugin** that allows users to quote messages across different servers and channels using webhooks, preserving the original author’s avatar and message content.

![Example](https://i.imgur.com/hJYGFRC.png)

## 🗃️ Features

- **Cross-server quoting** - Quote messages from any mutual server by message URL
- **Advanced search logic** - Quotes messages in channel by ID or content search
- **Enhanced URL parsing** - Supports all Discord URL formats (ptb/canary)
- **User presence verification** - Checks mutual servers before quoting
- **Maintains all original** - message content, attachments, embeds, and reactions
- **↑ 𝖮𝗋𝗂𝗀𝗂𝗇𝖺𝗅 𝖬𝖾𝗌𝗌𝖺𝗀𝖾 | 𝖨𝖣: 1234567890** - Adds a link back to the original message
- **Automatically manages webhooks** - reuses existing ones when possible
- **Improved error handling** - Better feedback for inaccessible messages
- **Clean command invocation** - deletes the command message when possible

## 📦 Installation

1. Add the cog to your bot:
```bash
?plugin add WebKide/modmail-plugins/quote@master
```

---

### 📖 Basic Commands

- `?quote [message ID]` - Quotes a message in same channel by its ID
- `?quote [text]` - Searches the last 100 messages for matching text
- `?quote [message URL]` - Quotes a message by its link in shared guilds

🔸 Your prefix is `?` by default, unless you changed it.

### 🛠️ Usage

```mathematica
?quote [message_id/search_term/link]
```

1. Quote by message ID:
```mathematica
?quote 123456789012345678
```

2. Quote by message link: (first right click the desired message and choose **Copy Message Link**)
```mathematica
?quote https://discord.com/channels/123/456/789
```

3. Quote by searching message content:
```rb
?q Hello World
```

### 🔰 Behavior

- The bot will search up to 100 messages back in the same channel
- For content searches, it will quote the first matching message found
- The quoted message will appear identical to the original, including:
  - Author name and avatar
  - Message content
  - Attachments (files, images, and media)
  - Embeds
- A link to the original message is included at the bottom by default

## 🤖 Bot Permissions Required

- [x] `Manage Webhooks` - to create webhooks **!important**
- [x] `Manage Messages` - to delete the command message
- [x] `Read Message History` - To fetch reactions or search messages
- [x] `Send Messages` - to send the quoted message
- [x] `Attach Files` - to attach files of original message
- [x] `Add Reactions` - to recreate reaction emojis of original message
- [x] `Use External Emojis` - if quoting messages with custom emojis

## ⚙️ Configuration

No special configuration is needed. The cog will automatically:

1. Check for existing usable webhooks
2. Create new webhooks when needed
3. Clean up after itself

## 🐞 Troubleshooting

**Problem:** Webhook messages doen’t appear  
**Solution:** Ensure the bot has "Manage Webhooks" permission

**Problem:** Can’t find messages  
**Solution:** The bot can only search the last 100 messages in the same command channel, and channels and servers where user and bot are both members

**Problem:** Attachments missing  
**Solution:** The bot may not have permissions to access the attachments

## 🛠️ Support

For issues or feature requests, please open an issue on GitHub.
