# **Role Reaction Modmail-plugin 2025**

## 📝 Description
This **RoleReact plugin** allows server administrators to set up reaction roles — a system where users can self-assign roles by clicking on reactions. It's perfect for:

- Creating opt-in role systems
- Letting users choose notification preferences
- Organizing community interests
- Managing game/server access roles


## 📦 Installation
```css
[p]plugin add WebKide/modmail-plugins/rolereact@master
```
Where `[p]` is your bot's prefix, by default `?` unless you changed it.


## ✨ Features
- 🛠️ Easy role-emoji pairing
- ⏸️ Pause/resume functionality
- ⚠️ User blacklisting
- 👥 Role-based exemptions
- 📜 Paginated lists
- 📝 Audit logging
- 🧹 Reaction cleanup tools

## 🛠️ Setup
1. Install the cog using the bot's plugin system
2. Set up your reaction roles with `!rr add`
3. Configure an audit channel (optional)

## 📋 Commands

### Core Commands
| Command | Example | Description |
|---------|---------|-------------|
| `!rr add` | `!rr add 🎮 Gaming` | Links an emoji to a role |
| `!rr remove` | `!rr remove 🎮` | Removes a reaction role |
| `!rr list` | `!rr list` | Shows all configured reaction roles |

### Utility Commands
| Command | Example | Description |
|---------|---------|-------------|
| `!rr pause` | `!rr pause` | Temporarily disables all reaction roles |
| `!rr blacklist` | `!rr blacklist @user` | Toggles blacklist for a user |
| `!rr ignore_role` | `!rr ignore_role @NoReacts` | Toggles role exemption |

### Setup Commands
| Command | Example | Description |
|---------|---------|-------------|
| `!rr set_channel` | `!rr set_channel #roles` | Sets the reaction role channel |
| `!rr set_audit_channel` | `!rr set_audit_channel #logs` | Sets the audit log channel |
| `!rr cleanup` | `!rr cleanup 123456789` | Cleans reactions from a message |

## 🎮 Usage Examples

### Basic Setup
1. Set up your channel:
   ```
   !rr set_channel #role-assignment
   ```
2. Add some reaction roles:
   ```
   !rr add 🎮 Gaming
   !rr add 📢 Announcements
   !rr add 🎨 Artist
   ```
3. Post a message and add reactions:
   ```
   !rr react 123456789012345678
   ```

### Advanced Setup
1. Create a message with instructions
2. Add all desired reactions manually or with `!rr react`
3. Blacklist troublemakers:
   ```
   !rr blacklist @ProblemUser
   ```
4. Exempt staff roles:
   ```
   !rr ignore_role @Staff
   ```

## ⚙️ Configuration
The bot automatically saves:
- All role-emoji pairs
- Blacklisted users
- Ignored roles
- Channel settings
- Pause state

## 🛡️ Permissions
- **Admin**: All commands
- **Moderator**: View commands only
- The bot requires:
  - `Manage Roles` permission
  - `Manage Messages` (for cleanup)
  - `Read Message History` (for reaction setup)

## ❓ FAQ

**Q: Can I use custom emojis?**  
A: Yes! Both Unicode and custom server emojis work.

**Q: What if a role gets deleted?**  
A: The bot will show "Deleted Role" in the list and ignore it.

**Q: Can I prevent certain emojis from being used?**  
A: Yes, [**Starboard**](https://github.com/WebKide/modmail-plugins/tree/master/starboard) emojis (⭐, 🌟, ✨) are automatically blocked.
```css
[p]plugin add WebKide/modmail-plugins/starboard@master
```

**Q: How do I mass remove reaction roles?**  
A: Use `!rr cleanup` on the message ID after removing configurations.

