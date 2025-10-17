# 🔄 gh2gl

<div align="center">

## ✨ GitHub to GitLab Mirroring CLI ✨

### Seamlessly mirror your GitHub repositories to GitLab with style and ease

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Rich](https://img.shields.io/badge/UI-Rich-green.svg)](https://github.com/Textualize/rich)
[![CLI](https://img.shields.io/badge/Interface-Typer-purple.svg)](https://typer.tiangolo.com/)

</div>

---

## 🌟 Features

- 🔐 **Secure Authentication** - Store GitHub & GitLab tokens safely with keyring
- 🚀 **Bulk Mirroring** - Mirror all your repositories at once
- 🎨 **Beautiful UI** - Rich terminal interface with progress bars and panels
- 🔒 **Private Repos** - Full support for private repositories
- ⚡ **Smart Sync** - Skip existing repos or force overwrite with `--force`
- 🧹 **Clean Names** - Automatic project name sanitization for GitLab compatibility
- 📊 **Progress Tracking** - Real-time statistics and detailed reporting
- 🏃 **Dry Run** - Preview operations without making changes
- 🛠️ **Self-Hosted** - Works with custom GitLab instances

## 📦 Installation

### For Users

```bash
# Install with pipx (recommended)
pipx install gh2gl

# Or install with pip
pip install gh2gl
```

### For Development

```bash
# Clone the repository
git clone https://github.com/viniciusccosta/gh2gl.git
cd gh2gl

# Install in development mode
pip install -e .
```

## 🚀 Quick Start

### 1️⃣ **Setup Authentication**

```bash
# Login to GitHub
gh2gl login github

# Login to GitLab
gh2gl login gitlab
```

### 2️⃣ **Test Connections**

```bash
# Verify API connectivity
gh2gl test
```

### 3️⃣ **Mirror Repositories**

```bash
# Preview what will be mirrored (dry run)
gh2gl mirror --dry-run

# Mirror all repositories
gh2gl mirror

# Force sync existing repositories
gh2gl mirror --force
```

## 📋 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `status` | 📊 Check credential configuration | `gh2gl status` |
| `test` | 🧪 Test API connectivity | `gh2gl test` |
| `login github` | 🔑 Setup GitHub authentication | `gh2gl login github` |
| `login gitlab` | 🔑 Setup GitLab authentication | `gh2gl login gitlab` |
| `mirror` | 🔄 Mirror repositories | `gh2gl mirror` |

## ⚙️ Command Options

### Mirror Command Flags

- `--dry-run` 👀 - Preview operations without making changes
- `--skip-existing` ⏭️ - Skip repositories that already exist on GitLab
- `--force` 💪 - Overwrite existing GitLab repositories

```bash
# Examples
gh2gl mirror --dry-run          # Preview only
gh2gl mirror --skip-existing    # Skip existing repos
gh2gl mirror --force            # Force overwrite all
```

## 🔧 Configuration

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Create a token with `repo` and `user` permissions
3. Run `gh2gl login github` and enter your token

### GitLab Token Setup

1. Go to GitLab User Settings → Access Tokens
2. Create a token with `api`, `read_repository`, and `write_repository` scopes
3. Run `gh2gl login gitlab` and enter your details

### Custom GitLab Instance

```bash
# For self-hosted GitLab
gh2gl login gitlab
# Enter your custom GitLab URL when prompted
```

## 📸 Screenshots

### Beautiful Status Display

```text
┌─ Credential Status ─┐
│ ✨ All credentials  │
│ configured!         │
└─────────────────────┘
```

### Rich Progress Tracking

```text
🔄 Mirroring GitHub → GitLab
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 23/23 repos

┌─ Summary ─┐
│ ✅ 21 Created    │
│ ⏭️  2 Skipped    │
│ ❌ 0 Errors      │
└──────────────────┘
```

## 🏗️ How It Works

1. **🔍 Discovery** - Fetches all your GitHub repositories (public + private)
2. **🧹 Sanitization** - Cleans repository names for GitLab compatibility
3. **🔄 Mirroring** - Uses `git clone --mirror` for complete repository copies
4. **📤 Upload** - Pushes to GitLab with proper authentication
5. **📊 Reporting** - Provides detailed success/error statistics

## 🛡️ Security

- 🔐 **Secure Storage** - Tokens stored safely using system keyring
- 🚫 **No Plaintext** - Credentials never stored in configuration files
- 🔒 **OAuth2** - Uses secure OAuth2 authentication for GitLab
- 👤 **User Scoped** - Only accesses repositories you have permission to

## 🐛 Troubleshooting

### Common Issues

#### 404 Errors

- Ensure your tokens have the correct permissions
- Verify GitLab URL is correct for self-hosted instances

#### Authentication Failed

- Re-run the login commands to refresh tokens
- Check token expiration dates

#### Repository Name Conflicts

- The tool automatically sanitizes names for GitLab compatibility
- Use `--force` to overwrite existing repositories

### Debug Mode

```bash
# Run with verbose output
gh2gl mirror --dry-run  # See what would happen first
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ and ☕

Happy mirroring! 🚀

</div>
