<div align="center">
<h1><b>💬 Quote</b><br>「modmail-plugins」</h1>
<p><b><i>plugins to expand Modmail’s functionality 🍆💦🍑</i></b> 「2020-2025」</p>

<img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons"><br>
<img src="https://img.shields.io/badge/python-v3.7+-12a4ff?style=for-the-badge&logo=python&logoColor=12a4ff">
<img src="https://img.shields.io/badge/library-discord%2Epy%202%2Ex-ffbb10?style=for-the-badge&logo=discord">
</div>

A Discord.py **modmail-plugin** that allows users to quote messages across different servers and channels using webhooks, preserving the original author’s avatar and message content.

![Example](https://i.imgur.com/hJYGFRC.png)

## 🗃️ Features

- **Cross-server quoting** - Quote messages from any mutual server by message URL
- **Advanced search logic** - Quotes messages in channel by ID or content search
- **Enhanced URL parsing** - Supports all Discord URL formats (ptb/canary)
- **User presence verification** - Checks mutual servers before quoting
- **Maintains all original** - message content, attachments, and embeds
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

- `?quote [message ID]` - Quotes a message by its ID
- `?quote [message URL]` - Quotes a message by its link
- `?quote [text]` - Searches the last 100 messages for matching text

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
```mathematica
?quote Hello World
```

### 🔰 Behavior

- The bot will search up to 100 messages back in the same channel
- For content searches, it will quote the first matching message found
- The quoted message will appear identical to the original, including:
  - Author name and avatar
  - Message content
  - Attachments
  - Embeds
- A link to the original message is included at the bottom

## 🤖 Bot Permissions Required

- [x] Manage Webhooks
- [x] Manage Messages (to delete the command message)
- [x] Read Message History
- [x] Send Messages
- [x] Attach Files

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
