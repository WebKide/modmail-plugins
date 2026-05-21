<div align="center">
   <img src="https://i.imgur.com/yqrtyFu.png" alt="quote logo" width="80%" />
</div>

------

<div align="center">
   <img src="https://img.shields.io/badge/Modmail%20Plugin-Reminder%20System-black.svg?style=popout&logo=github&logoColor=white" alt="Reminder Plugin" />
   <img src="https://img.shields.io/badge/Made%20with-Python%203.10-blue.svg?style=popout&logo=python&logoColor=yellow" alt="Python3" />
   <img src="https://img.shields.io/badge/Library-discord%2Epy%202%2Ex-ffbb10?style=popout&logo=discord">
   <img src="https://img.shields.io/badge/Database-MongoDB-%234ea94b.svg?style=popout&logo=mongodb&logoColor=white" alt="MongoDB" />
</div>

<div align="center">
   <img src="http://forthebadge.com/images/badges/built-with-love.svg?style=for-the-badge" alt="built with love" />
   <img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons">
</div>

<div align="center">
   <h1>「Advanced Reminder System for Modmail 2026 🕐✨」</h1>
</div>

A Discord.py **modmail-plugin** by [WebKide](https://github.com/WebKide/modmail-plugins/tree/master/reminder) that provides a comprehensive reminder system with timezone support, recurring reminders, snooze functionality, and paginated reminder management through an intuitive button-based interface.

## 🗃️ Features

- **Timezone-aware reminders** - Set reminders in your own timezone (UTC±HH or named zones like `America/New_York`)
- **Flexible time parsing** - Natural language input: "in 2 hours", "tomorrow at 3pm", "next monday"
- **Recurring reminders** - Set daily, weekly, or monthly reminders that reschedule automatically
- **Smart delivery** - Sends to DM first, falls back to original channel, then guild fallback
- **Snooze functionality** - Dismiss reminders and reschedule for 30m, 1h, or 1d later
- **Paginated reminder management** - View all active reminders with intuitive navigation buttons
- **Reaction-based dismissal** - React with ☑️ to dismiss delivered reminders
- **Auto-cleanup** - Separate active, completed, and failed reminder states
- **Admin controls** - View/manage user reminders and purge database records
- **Robust error handling** - Retry logic and graceful fallbacks for delivery failures

## 📦 Installation

1. Add the cog to your bot:
```bash
?plugin add WebKide/modmail-plugins/reminder@master
```

2. The plugin will automatically:
   - Create database indexes for performance
   - Initialize the timezone manager
   - Start the background reminder loop

---

### 📖 Core Commands

#### User Commands

**`!remind [time] SEPARATOR [reminder text]`** - Set a new reminder
- Aliases: `!remindme`, `!reminder`
- Separators: `|`, `-`, `/`, `>`, `[`, `—`

**`!reminders`** - List all your active reminders
- Aliases: `!myreminders`, `!mr`
- Display: Paginated embeds with delete/off buttons

**`!mytimezone [timezone]`** - Set your timezone
- Aliases: `!settimezone`, `!settz`
- Formats: `UTC±HH` (e.g., `UTC+5:30`, `UTC-8`) or named zones (e.g., `America/New_York`)

**`!mytime`** - Show your current time in your set timezone

**`!clearreminders`** - Delete all completed reminders
- Aliases: `!clearcompleted`, `!dropreminders`

#### Admin Commands

**`!remindadm view @user`** - View and manage a specific user's reminders
- Requires: Administrator permission
- Shows all active reminders for the target user with full management controls

**`!remindadm purge`** - Purge all reminder records from database
- Requires: Administrator permission
- Confirmation required; clears active/completed/failed reminders, preserves timezones
- Aliases: `--drop` flag wipes everything including timezone configs for factory reset

---

### 🔰 Usage Examples

#### Setting a Reminder

```
!remind in 2 hours | take out the trash
!remind tomorrow at 3pm - buy groceries
!remind in 3 days / finish the report
!remind next monday at 9am > attend meeting
!remind in 30 minutes [ check email
```

#### Setting Timezone

```
!mytimezone UTC+5
!mytimezone UTC-8
!mytimezone America/New_York
!settimezone Europe/London
```

#### Viewing & Managing Reminders

```
!reminders
!myreminders
!mr
```

Then use the buttons:
- **◀ ▶** - Navigate between pages
- **🗑️ Delete** - Remove the current reminder
- **🔇 OFF** - Hide the reminder display

#### Delivered Reminder Interactions

When a reminder is delivered, you can:
- **Click 30m, 1h, 1d** - Snooze the reminder
- **Click OFF** - Dismiss the reminder message
- **React ☑️** - Dismiss the message (alternative)

---

### ⚙️ Behavior & Features

**Time Parsing**
- Accepts natural language input with flexible formatting
- Requires a minimum 10-second buffer (prevents accidental past times)
- Supports relative times ("in X hours/days/weeks") and absolute times ("tomorrow at 3pm", "next monday")

**Reminder Delivery**
1. Attempts to send as DM to the user
2. Falls back to the original channel where the reminder was set
3. If both fail, searches the original guild for the first available text channel
4. Auto-deletes messages in guild channels after 60 seconds
5. Retries failed deliveries up to 3 times before marking as failed

**Recurring Reminders**
- Automatically reschedule after delivery
- Maintain original time-of-day across day/week/month boundaries
- Account for DST shifts in named timezones
- Can be deleted like any other reminder

**Timezone Handling**
- UTC offset timezones (e.g., `UTC+5:30`) are static — no DST
- Named timezones (e.g., `America/New_York`) resolve DST dynamically
- All internal times stored as UTC; displayed in user's timezone
- Default timezone is UTC if not set

**Pagination**
- Auto-deletes reminder display messages after 120 seconds (resets on interaction)
- Buttons disable automatically on timeout
- Supports unlimited reminders (displays 1 per page)

---

### 🤖 Bot Permissions Required

- [x] `Send Messages` - to deliver reminders
- [x] `Read Messages/View Channels` - to search and fetch messages
- [x] `Read Message History` - to retrieve reminder context
- [x] `Manage Messages` - to delete command invocations
- [x] `Add Reactions` - to add dismissal reactions (☑️)
- [x] `Use External Emojis` - if reactions use custom emojis

**No webhook permissions required** — this plugin uses pure message delivery.

---

### 📊 Database Schema

All documents stored in MongoDB with strict field naming:

**Reminder Document**
```json
{
  "_id": "uuid-string",
  "user_id": 123456789,
  "channel_id": 987654321,
  "guild_id": 555555555,
  "text": "Reminder text content",
  "due": "2025-05-21T15:30:00Z",
  "created": "2025-05-21T12:00:00Z",
  "status": "active|completed|failed",
  "recurring": "daily|weekly|monthly|null",
  "retry_count": 0,
  "delivered": "2025-05-21T15:30:15Z|null",
  "error": "error message if failed|null"
}
```

**Timezone Document**
```json
{
  "_id": "timezone_123456789",
  "offset_minutes": 330,
  "timezone_name": "America/New_York|null"
}
```

---

### 🐞 Troubleshooting

**Problem:** Reminders aren't firing  
**Solution:** Check that the background loop is running; verify bot is not in an error state. Ensure database indexes were created successfully.

**Problem:** Timezone not saving  
**Solution:** Use valid UTC offset format (`UTC±HH:MM`) or a named timezone from `pytz.all_timezones`. Example: `UTC+5:30` or `Asia/Kolkata`.

**Problem:** Reminders not delivered to DM  
**Solution:** User may have DMs disabled. The bot falls back to the original channel automatically. Check channel permissions if fallback fails.

**Problem:** Recurring reminder not rescheduling  
**Solution:** Verify the `recurring` field is set to `daily`, `weekly`, or `monthly` (case-insensitive). Check server logs for reschedule errors.

**Problem:** Reaction dismissal not working  
**Solution:** Ensure the bot has `Add Reactions` permission. The ☑️ emoji must be a standard emoji (not custom).

**Problem:** Buttons not responding  
**Solution:** Buttons automatically disable after 120 seconds (or 300 seconds for setup views). If timed out, use `!reminders` to re-display the list. Buttons only respond to the command initiator.

---

### 🔍 Version Info

**Current Version:** Reminder v4.01 
**Last Updated:** May 2026  
**Compatibility:** discord.py 2.0+, Modmail v4.2

**Critical Fixes in v4.01:**
- Fixed database deserialization crash on named timezones
- Unified schema field naming (`due` instead of mixed `target_time`)
- Fixed pytz localization crash on pre-aware datetimes
- Resolved multi-view instance collisions in message delivery
- Fixed Motor sort() type errors and cursor iteration deadlocks
- Corrected reaction dismissal title mismatch
- Improved timeout/cleanup attribute handling

---

### 📝 Configuration

No special configuration required. The plugin:

1. ✅ Auto-creates database indexes on startup
2. ✅ Initializes timezone cache automatically
3. ✅ Starts background reminder loop on load
4. ✅ Manages view timeouts and cleanup internally

---

### 🛠️ Support & Contributing

**Report Issues:**
- Include the full error traceback from bot logs
- Specify: Python version, discord.py version, Modmail version
- Include: example reminder command that failed, timezone if applicable
- Check existing issues before reporting duplicates

**Contributing:**
- All timezone parsing uses `pytz` and `dateutil`
- Database operations use Motor (async MongoDB driver)
- Views use discord.py 2.0+ components (`discord.ui`)
- Follow PEP 8 style; add type hints to new functions

---

### 📜 License

This plugin is maintained as part of the Modmail ecosystem and follows the parent project's license terms.

---

<div align="center">
   <strong>Made with ❤️ for the Modmail community</strong>
</div>
