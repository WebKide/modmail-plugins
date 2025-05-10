<div align="center">
<h1><b>💬 Quote</b><br>「modmail-plugins」</h1>
<p><b><i>plugins to expand Modmail's functionality 🍆💦🍑</i></b> 「2020-2025」</p>

<img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons"><br>
<img src="https://img.shields.io/badge/python-v3.7+-12a4ff?style=for-the-badge&logo=python&logoColor=12a4ff">
<img src="https://img.shields.io/badge/library-discord%2Epy%202%2Ex-ffbb10?style=for-the-badge&logo=discord">
</div>

A Discord.py **modmail-plugin** that allows users to quote messages using webhooks, preserving the original author's appearance and message content.

![Example](https://i.imgur.com/hJYGFRC.png)

## 🗃️ Features

- Quotes messages by ID, URL, or content search
- Preserves original author's name and avatar via webhooks
- Maintains all original message content, attachments, and embeds
- Adds a link back to the original message
- Automatically manages webhooks (reuses existing ones when possible)
- Clean command invocation (deletes the command message)

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

### 📑 Examples

1. Quote by message ID:
```
?quote 123456789012345678
```

2. Quote by message link: (first right click the desired message and choose **Copy Message Link**)
```
?quote https://discord.com/channels/123/456/789
```

3. Quote by searching message content:
```
?quote hello world
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

**Problem:** Webhook messages doen't appear  
**Solution:** Ensure the bot has "Manage Webhooks" permission

**Problem:** Can't find messages  
**Solution:** The bot can only search the last 100 messages in a channel

**Problem:** Attachments missing  
**Solution:** The bot may not have permissions to access the attachments

## 🛠️ Support

For issues or feature requests, please open an issue on GitHub.
