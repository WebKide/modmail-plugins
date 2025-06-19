# 📊 StatsBoard Plugin

**Version:** 2.06
**Compatible with:** discord.py v2.x  
**Plugin Type:** Modmail Bot Extension

An enhanced automatic server statistics display system that provides real-time server information in a dedicated channel with comprehensive monitoring capabilities.

## ✨ Features

- **🔄 Automatic Updates**: Real-time statistics with configurable update intervals
- **📈 Comprehensive Stats**: Member counts, channel info, voice activity, bot performance
- **🚀 Auto-Start**: Automatically resumes after bot restarts
- **💾 Persistent Configuration**: Maintains settings across restarts
- **🎯 Smart Updates**: Only updates when data changes to reduce API calls
- **🔧 Admin Controls**: Full command suite for management
- **📊 Performance Monitoring**: System resources, uptime, and restart tracking
- **🎨 Custom Styling**: Beautiful embed with server-specific theming

## 📋 Requirements

- Python 3.10
- discord.py v2.x
- psutil library (in the requirements.txt)
- Modmail bot official
- Bot permissions: `Manage Channels`, `Send Messages`, `Embed Links`, `Manage Messages`

## 🚀 Installation

1. **Run this command in your main guild:**
   ```bash
   ?plugin add WebKide/modmail-plugins/statsboard@master
   ```

## ⚙️ Setup & Configuration

### Initial Setup

1. **Run the setup command:**
   ```
   !statsboard setup
   ```
   - Creates a dedicated `#bot-stats` channel
   - Generates the initial statistics embed
   - Starts automatic updates
   - Configures all necessary settings

2. **Verify installation:**
   ```
   !statsboard config
   ```

### Auto-Start Configuration

The plugin will automatically start when the bot comes online **if previously enabled**. No manual intervention required after initial setup.

## 🎮 Commands

All commands require `Manage Server` permission.

### Main Commands

| Command | Description |
|---------|-------------|
| `!statsboard` | Show help and current status |
| `!statsboard setup` | Initialize the stats system |
| `!statsboard toggle` | Enable/disable updates |
| `!statsboard refresh` | Manually update stats |
| `!statsboard config` | View current settings |

### Advanced Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!statsboard interval <seconds>` | Set update frequency (15-3600s) | `!statsboard interval 60` |
| `!statsboard reset` | Complete system reset | `!statsboard reset` |

### Command Aliases

- `!stats` → `!statsboard`
- `!statsboard update` → `!statsboard refresh`
- `!statsboard settings` → `!statsboard config`

## 📊 Statistics Displayed

### Server Information
- **Creation Date**: When the server was created
- **Owner**: Current server owner
- **Verification Level**: Server verification setting
- **Boost Level & Count**: Nitro boost information

### Member Statistics
- **Total Members**: Complete member count
- **Humans vs Bots**: Breakdown of member types
- **Online Status**: Live status distribution (🟢🟡🔴⚫)

### Channel & Activity
- **Channel Counts**: Text, voice, categories, stages
- **Voice Activity**: Active channels and users
- **Role Information**: Total roles and hoisted roles

### Bot Performance
- **Uptime**: How long the bot has been running
- **Latency**: Current Discord API latency
- **Commands Used**: Total command usage statistics
- **Restart Tracking**: Number of restarts and last restart time

### System Resources
- **Memory Usage**: Current RAM consumption
- **CPU Usage**: Processor utilisation
- **Thread Count**: Active system threads

## 🔧 Configuration Options

### Settings File Location
```
data/stats_config.json
```

### Configurable Parameters

| Setting | Default | Description |
|---------|---------|-------------|
| `enabled` | `false` | Enable/disable automatic updates |
| `update_interval` | `30` | Update frequency in seconds (10-3600) |
| `channel_name` | `bot-stats` | Name for the stats channel |
| `guild_id` | `null` | Target server ID |
| `channel_id` | `null` | Stats channel ID |
| `message_id` | `null` | Stats message ID |

### Manual Configuration
```json
{
    "enabled": true,
    "update_interval": 30,
    "channel_name": "bot-stats",
    "guild_id": 123456789012345678,
    "channel_id": 987654321098765432,
    "message_id": 111222333444555666
}
```

## 🛠️ Troubleshooting

### Common Issues

**Stats not updating:**
1. Check if enabled: `!statsboard config`
2. Verify bot permissions in stats channel
3. Try manual refresh: `!statsboard refresh`

**Channel not found:**
1. Ensure bot has `Manage Channels` permission
2. Run setup again: `!statsboard setup`

**After bot restart:**
- Stats should resume automatically if previously enabled
- If not working, check configuration: `!statsboard config`

**Performance issues:**
- Increase update interval: `!statsboard interval 60`
- Check system resources in the stats display

### Reset Instructions

If you encounter persistent issues:
```
!statsboard reset
!statsboard setup
```

## 🔒 Permissions Required

### Bot Permissions
- `Manage Channels` - Create stats channel
- `Send Messages` - Post statistics
- `Embed Links` - Display formatted stats
- `Manage Messages` - Edit existing messages
- `Read Message History` - Fetch previous messages

### User Permissions
- `Manage Server` - Required for all statsboard commands

## 📈 Performance Notes

- **Update Frequency**: Default 30 seconds, adjustable 10-3600 seconds
- **API Efficiency**: Only updates when data changes
- **Resource Usage**: Minimal impact, ~5-15MB RAM
- **Rate Limiting**: Built-in protection against Discord limits

## 🔄 Maintenance

### Regular Tasks
- Monitor system resources in stats display
- Adjust update interval based on server activity
- Check logs for any error messages

### Updates
After plugin updates:
1. Reload the plugin: `!plugin reload WebKide/modmail-plugins/statsboard`
2. Verify functionality: `!statsboard config`
3. If issues occur: `!statsboard toggle` (off/on)

## 🆘 Support

### Debug Information
When reporting issues, include:
```
!statsboard config
```
Output and any error messages from bot logs.

### Log Information
The plugin logs important events:
- Setup and initialization
- Configuration changes
- Update failures
- Permission issues

Check your bot's log files for detailed error information.

## 📝 Version History

### v2.03 (Current)
- Enhanced auto-start functionality
- Improved restart tracking
- Better error handling and recovery
- Performance optimizations
- Configuration validation

---

*This plugin is designed for Modmail bots and requires proper setup for optimal functionality. For additional support, refer to your Modmail bot documentation.*
