<div align="center">
<h1>「modmail-private-plugins」</h1>
<p><b><i>Secure management for private Modmail plugins 🔒🚀</i></b></p>
</div>

<div align="center">
<img src="http://forthebadge.com/images/badges/made-with-crayons.svg?style=for-the-badge" alt="made with crayons"><br>
<img src="https://img.shields.io/badge/python-v3.7+-12a4ff?style=for-the-badge&logo=python&logoColor=12a4ff">
<img src="https://img.shields.io/badge/library-discord%2Epy%202%2Ex-ffbb10?style=for-the-badge&logo=discord">
<br><br>
</div>

# 🔒 Private Plugin Manager (v2.0)

A secure system for installing and managing private GitHub plugins in your Modmail bot with enhanced features and better reliability.

## ⚠️ Disclaimer

> You can achieve the same by placing your `GITHUB_TOKEN` inside the `.env` of your bot. Remember that you shouldn't install any plugins in your bot, since they have full control and can hack your guild and NUKE it. If you install any plugin, it must be from a dev you trust!

## ✨ Key Features

- **Private Repo Support**: Install plugins from **private repositories** without using `.env`
- **Interactive UI**: Paginated embeds with reaction controls
- **Auto-Detection**: Smart cog name detection for better compatibility
- **Progress Tracking**: Real-time loading status updates
- **Help Integration**: Automatic command help display after successful install

## 🚀 Installation

```bash
?plugin add WebKide/modmail-plugins/private-plugins@main
```

> Replace `?` with your bot's prefix if you changed it

## 🔑 GitHub Token Guide

### Required Permissions
1. Go to [GitHub Token Settings](https://github.com/settings/tokens/new)
2. **Select scopes** `Scopes define the access for personal tokens.`

- ✅ **repo** `(Full control of private repositories)`
  
  - [x] repo:status `(Access commit status)`

  - [x] repo_deployment `(Access deployment status)`

  - [x] public_repo `(Access public repositories)`

  - [x] repo:invite `(Access repository invitations)`

  - [x] security_events `(Read and write security events)`

- [ ] No other scopes needed

3. **Expiration** `(recommended: 90 days)`
4. <div>
     <p>Scroll down and <b>Click:</b></p>
     <img src="https://img.shields.io/badge/-Generate_Token-Teal?style=for-the-badge" alt="Generate Token">
   </div>
5. ⚠️ **`Make sure to copy your personal access token now. You won’t be able to see it again!`**


### Security Notes
- 🔐 Token grants read access to ALL private repos
- 🚫 Never commit tokens to code
- 🔄 Rotate tokens periodically

## 🛠️ Command Reference (Updated)

### 🔐 Token Management
| Command | Description | Example |
|---------|-------------|---------|
| `?private token <token>` | Store/verify GitHub token | `?private token ghp_abc123` |
| `?private testtoken` | Verify token validity | `?private testtoken` |
| `?private testrepo` | Test repository access | `?private testrepo user repo` |

### 📦 Plugin Management (Enhanced)
| Command | Description | Example |
|---------|-------------|---------|
| `?private load <user/repo/name@branch>` | Install with progress tracking | `?private load user/repo/plugin-name@branch` |
| `?private unload <user/repo/name@branch>` | Remove plugin completely | `?private unload user/repo/plugin-name@main` |
| `?private validate <name>` | Check plugin structure | `?private validate plugin-name` |
| `?private guide` | Show plugin structure guide | `?private guide` |

### 🔄 Interactive Controls
| Command | Description | UI Features |
|---------|-------------|------------|
| `?private update` | Updater interface | 1️⃣-8️⃣: Update plugins<br>⬅️➡️: Pagination |
| `?private loaded` | View installed plugins | Shows branch info |
| `?private debug` | Repository debug tool | Checks access and structure |

## 🆕 New Features

### Smart Loading Process
```python
1. User: ?private load user/repo/plugin-name@main
2. Bot: » Downloading plugin-name@main...
3. Bot: ✅ Downloaded! Now loading...
4. Bot: ✅ Successfully loaded plugin-name!
5. Bot: Shows available commands automatically
```

### Automatic Help Integration
After loading any plugin:
- Automatically displays available commands
- Shows correct help command (`?help YourPrivateCogName`)
- Handles nested plugin structures

### Enhanced Error Handling
- Detailed error messages with trace information
- Directory structure validation
- Requirements.txt installation feedback

## 🖼️ Interface Previews

### Interactive Update Panel
```diff
+ PRIVATE PLUGINS (PAGE 1/2) +
1️⃣ /private-plugin-name@master
  user/repo | User analytics system
2️⃣ /private-plugin-name@master
  user/repo | Automated DB backups
...
⬅️ ➡️ (Navigate)
React with number to update private-plugin
```

## ❓ FAQ (Updated)

**Q: How are cog names detected?**  
A: The system automatically scans for `class YourPrivateCogName(commands.Cog)` in plugin files.

**Q: What if my plugin has a different structure?**  
A: Use `?private guide` to see the recommended structure and addapt accordingly.

**Q: Can I see plugin loading progress?**  
A: Yes! The bot now shows real-time download and load status, with clear error messages.

**Q: How do I troubleshoot installation issues?**  
A: Use `?private debug user repo branch` to diagnose problems.

## 🐛 Troubleshooting

**Issue: "Could not find plugin directory"**
1. Check repository structure matches `?private guide`
2. Verify branch exists, usually `@main`
3. Use `?private debug` to test access

**Issue: "Missing setup function"**
1. Ensure `__init__.py` contains `setup(bot)`
2. Validate with `?private validate plugin-name`

**Issue: "Commands not showing in help"**
1. Check cog class inherits from `commands.Cog`
2. Verify command decorators are properly used
3. Use `?private guide` to compare your implementation

## 🏗️ Plugin Structure Guide

Run `?private guide` to see:
1. Required repository structure
2. Example cog implementation
3. Installation command format
4. Best practices for plugin development

---

<div align="center">
<b>Need help? Open an issue with reproduction steps and error logs!</b>
</div>
