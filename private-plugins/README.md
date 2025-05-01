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

# 🔒 Private Plugin Manager

A secure system for installing and managing private GitHub plugins in your Modmail bot. Safely handle proprietary plugins with granular control and interactive updates.

## ✨ Key Features

- **Token Security**: Encrypted GitHub TOKEN storage with verification
- **Private Repo Support**: Install plugins from **private repositories**
- **Interactive UI**: Paginated embeds with reaction controls

## 🚀 Installation

```json
?plugin add WebKide/modmail-plugins/private-plugins@master
```

> Replace `?` with your bot's prefix if different

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

4. **Expiration** `(recommended: 90 days)`
5. <div>
     <p>Scroll down and <b>Click:</b></p>
     <img src="https://img.shields.io/badge/-Generate_Token-Teal?style=for-the-badge" alt="Generate Token">
   </div>
6. ⚠️ **`Make sure to copy your personal access token now. You won’t be able to see it again!`**

### Security Notes
- 🔐 Token grants read access to ALL private repos
- 🚫 Never commit tokens to code
- 🔄 Rotate tokens periodically

## 🛠️ Command Reference

### 🔐 Token Management
| Command | Description | Example |
|---------|-------------|---------|
| `?private token <token>` | Store/verify GitHub token | `?private token ghp_abc123` |
| `?private token` | Show token setup instructions | `?private token` |

### 📦 Plugin Management
| Command | Description | Example |
|---------|-------------|---------|
| `?private load <user/repo/name@branch>` | Install | `?private load user/repo/private-plugin-name@master` |
| `?private unload <user/repo/name@branch>` | Remove | `?private unload user/repo/private-plugin-name@master` |

### 🔄 Interactive Controls
| Command | Description | UI Features |
|---------|-------------|------------|
| `?private update` | Updater | 1️⃣-8️⃣: Update plugins<br>⬅️➡️: Pagination |
| `?private loaded` | View plugins | Paginated display |

## 🖼️ Interface Preview

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

### Installation Flow
```python
1. User: ?private load repo/private-plugin-name@master
2. Bot: » Verifying GitHub access...
3. Bot: ✅ Downloaded repo/private-plugin-name@master
4. Bot: » Installing requirements... (if any)
5. Bot: ✅ Plugin loaded successfully!
```

## ❓ FAQ

**Q: Can I use organization-owned private repos?**  
A: Yes! The token owner needs read access to the repo.

**Q: How are updates handled?**  
A: The `?private update` interface shows update status per-plugin with ✅/❌ indicators.

**Q: Where is the GitHub token stored?**  
A: Tokens are encrypted in Modmail’s database (plugin_db partition).

**Q: Can plugins access my token?**  
A: No, tokens are only accessible to the manager cog.

## 🐛 Troubleshooting

**Issue: "Repository not found"**
1. Verify token has `repo` scope
2. Check repo exists and is accessible
3. Ensure correct casing in repo name (CaseSensitive)

**Issue: "Requirements install failed"**
1. Check `requirements.txt` exists in plugin
2. Verify package names are correct
3. Check bot’s Python environment

**Issue: "Permission denied"**
1. Run `?private token` to verify active token
2. Check token hasn’t expired
3. Regenerate token if needed

---

<div align="center">
<b>Need help? Open an issue with reproduction steps and error logs!</b>
</div>
