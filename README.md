# Claude Session Keeper v2.0

**Automatically optimize your Claude Code session timing with intelligent scheduling, web dashboard, and multi-channel notifications.**

[![Python 3.7+](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## One-Line Installation

### Linux / macOS
```bash
curl -fsSL https://raw.githubusercontent.com/nomadictuba2005/claude-session-keeper/main/install.sh | bash
```

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/nomadictuba2005/claude-session-keeper/main/install.ps1 | iex
```

### pip Install
```bash
pip install git+https://github.com/nomadictuba2005/claude-session-keeper.git
```

**That's it!** After installation, use `csk` or `claude-session-keeper` from anywhere.

---

## Quick Start

```bash
# Launch interactive menu (easiest way to start)
csk --interactive

# Or start the web dashboard
csk --web

# Run a single health check
csk --once

# View statistics
csk --stats
```

---

## What's New in v2.0

| Feature | Description |
|---------|-------------|
| **Web Dashboard** | Beautiful dark-themed UI with live status |
| **Interactive CLI** | Menu-driven terminal interface |
| **Statistics Tracking** | SQLite-powered session history and analytics |
| **Multi-Channel Notifications** | Discord, Slack, webhooks, desktop alerts |
| **Schedule Profiles** | Pre-built & custom profiles (morning, evening, etc.) |
| **REST API** | Programmatic control and monitoring |
| **One-Line Install** | Auto path setup, works immediately |

---

## Features

### Web Dashboard (`csk --web`)

Access at `http://localhost:5000`:
- Real-time status cards (today's checks, uptime, streaks)
- Recent session history
- Quick action buttons
- Profile management
- Auto-refresh every 30 seconds

![Web Dashboard Preview](https://via.placeholder.com/800x400?text=Web+Dashboard)

### Interactive Menu (`csk --interactive`)

Full-featured terminal UI:
- Run health checks
- Start/stop scheduler
- View detailed statistics
- Manage profiles
- Configure notifications
- Export data

### Schedule Profiles

Pre-built profiles for common use cases:

| Profile | Daily Reset | Description |
|---------|-------------|-------------|
| `morning` | 08:00 | Fresh sessions each morning |
| `afternoon` | - | Default 4:01 PM start |
| `evening` | 18:00 | Evening schedule |
| `night-owl` | 22:00 | Late night workers |
| `always-on` | - | Continuous 5-hour cycles |

```bash
# Use a profile
csk --profile morning

# List all profiles
csk --list-profiles
```

### Multi-Channel Notifications

Get alerts via:
- **Discord** - Rich embeds with colors
- **Slack** - Formatted block messages
- **Generic Webhooks** - JSON payloads
- **Desktop** - Native OS notifications

Configure in the interactive menu or edit `notifications_config.json`.

### REST API

```bash
GET  /api/status          # Current status
GET  /api/stats           # All statistics
GET  /api/sessions        # Recent sessions
GET  /api/profiles        # List profiles
POST /api/check           # Run health check
POST /api/scheduler/start # Start scheduler
POST /api/scheduler/stop  # Stop scheduler
```

---

## All Commands

```bash
# Modes
csk --interactive        # Interactive terminal menu
csk --web               # Web dashboard (default port 5000)
csk --web --port 8080   # Web on custom port
csk --once              # Single health check
csk --resume            # Resume from last run

# Scheduling
csk --profile morning           # Use schedule profile
csk --daily-reset 08:00         # Daily reset at 8 AM
csk --unix-timestamp 1755316870 # Start at exact time

# Information
csk --stats             # View statistics
csk --list-profiles     # List available profiles
csk --help              # Full help
```

---

## Installation Options

### Option 1: One-Line Install (Recommended)

**Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/nomadictuba2005/claude-session-keeper/main/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://raw.githubusercontent.com/nomadictuba2005/claude-session-keeper/main/install.ps1 | iex
```

This will:
- Download all files to `~/.claude-session-keeper`
- Install Python dependencies
- Add `csk` and `claude-session-keeper` to your PATH
- Create default configuration

### Option 2: pip Install

```bash
# Basic install
pip install git+https://github.com/nomadictuba2005/claude-session-keeper.git

# With web dashboard support
pip install "claude-session-keeper[web] @ git+https://github.com/nomadictuba2005/claude-session-keeper.git"
```

### Option 3: Manual Install

```bash
# Clone repository
git clone https://github.com/nomadictuba2005/claude-session-keeper.git
cd claude-session-keeper

# Install with make
make install

# Or manually
pip install -r requirements.txt
python claude_health_check_cli.py --help
```

### Option 4: Docker (Coming Soon)

```bash
docker run -d --name csk nomadictuba2005/claude-session-keeper
```

---

## Prerequisites

Before using Claude Session Keeper, you need:

### 1. Claude Code CLI
```bash
# Install Node.js 18+ if needed
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Login (one-time)
claude login
```

### 2. Python 3.7+
Most systems have this pre-installed. Check with:
```bash
python3 --version
```

---

## Configuration

### Webhook Alerts

Edit `config.json`:
```json
{
  "webhook_url": "https://webhook.site/your-unique-id"
}
```

### Notification Channels

Edit `notifications_config.json` or use the interactive menu:
```json
{
  "channels": [
    {
      "name": "Discord",
      "channel_type": "discord",
      "webhook_url": "https://discord.com/api/webhooks/...",
      "enabled": true,
      "notify_on_failure": true,
      "notify_on_success": false
    }
  ]
}
```

### Custom Profiles

Edit `profiles.json` or use the interactive menu to create custom schedules.

---

## 24/7 Operation

### Run in Background

```bash
# Using nohup
nohup csk --profile morning > ~/csk.log 2>&1 &

# Using screen
screen -S csk
csk --profile morning
# Ctrl+A, D to detach
```

### Auto-start on Boot (Linux)

```bash
# Add to crontab
crontab -e

# Add this line:
@reboot /home/user/.local/bin/csk --resume >> /home/user/csk.log 2>&1
```

### Systemd Service

Create `/etc/systemd/system/claude-session-keeper.service`:
```ini
[Unit]
Description=Claude Session Keeper
After=network.target

[Service]
Type=simple
User=your-username
ExecStart=/home/your-username/.local/bin/csk --profile morning
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable claude-session-keeper
sudo systemctl start claude-session-keeper
```

---

## How It Works

Claude Code uses **fixed 5-hour session windows**:
1. Window starts with your **first message**
2. You have 10-800 messages per window
3. Window expires **5 hours after the first message**
4. **This tool controls when that first message happens**

**Without this tool:** Random session timing
**With this tool:** Predictable sessions aligned with your schedule

---

## Raspberry Pi Optimization

The script includes optimizations for low-power devices:
- **Node.js memory limit:** 256MB max
- **Reduced thread pool:** Minimizes CPU usage
- **Disabled telemetry:** Saves bandwidth
- **Lower process priority:** Won't interfere with other tasks

**Power consumption:** ~$0.26/month on Raspberry Pi 3B

---

## FAQ

**Is this allowed by Anthropic?**
Yes! Uses Claude Code's official CLI as intended. Doesn't circumvent any restrictions.

**Will this use up my quota?**
Minimal impact - uses 1 message per 5-hour window (~4-5 messages/day).

**Can I run on multiple devices?**
Not recommended - would create overlapping sessions. Run on one device.

**What if my system crashes?**
Use `csk --resume` to continue from where you left off.

---

## Troubleshooting

### Command Not Found After Install

```bash
# Reload your shell config
source ~/.bashrc  # or ~/.zshrc

# Or restart your terminal
```

### Claude Code Issues

```bash
# Verify Claude Code works
claude --version
claude Hi

# Re-login if needed
claude login
```

### Web Dashboard Won't Start

```bash
# Install Flask
pip install flask

# Try different port
csk --web --port 8080
```

---

## Development

```bash
# Clone and setup
git clone https://github.com/nomadictuba2005/claude-session-keeper.git
cd claude-session-keeper

# Install in dev mode
make install-dev

# Run tests
make test

# Clean generated files
make clean
```

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## License

MIT License - Use it however you want!

---

## Support

- **Issues:** [GitHub Issues](https://github.com/nomadictuba2005/claude-session-keeper/issues)
- **Discussions:** [GitHub Discussions](https://github.com/nomadictuba2005/claude-session-keeper/discussions)

---

**Claude Session Keeper v2.0** - Intelligent session management for Claude Code

*Star this repo if it helps optimize your Claude Code workflow!*
