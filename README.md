# Claude Session Keeper

🤖 **Automatically optimize your Claude Code session timing with intelligent scheduling and daily resets.**

## What It Does

Claude Code uses **fixed 5-hour session windows** that start with your first message. This script gives you complete control over when those windows begin:

- ✅ **5-Hour Session Optimization** - Control exactly when your Claude Code sessions start
- ✅ **Daily Reset Feature** - Fresh sessions every day at your preferred time  
- ✅ **Smart Scheduling** - Never waste sessions on random timing
- ✅ **Minimal Resource Usage** - 1 message per window vs 10-800 limit
- ✅ **24/7 Operation** - Perfect for Raspberry Pi or always-on systems
- ✅ **Automatic Timezone Detection** - Works anywhere in the world

## How Claude Code Sessions Work

Claude Code limits work with **fixed 5-hour windows**:
1. Window starts with your **first message** 
2. Once you hit your limit (10-800 messages), you're locked out
3. Window expires exactly **5 hours after the first message**
4. **This script controls when that first message happens** 🎯

**Without this script:** Random session timing based on when you happen to use Claude  
**With this script:** Predictable, optimized sessions that align with your schedule

## 🚀 Features

### ⏰ Precise Timing Control
- **Unix timestamp scheduling** - Start at exact moments
- **Resume functionality** - Pick up where you left off after restarts
- **Smart conflict resolution** - Daily resets override 5-hour schedules

### 🌅 Daily Reset Feature  
- **Fresh sessions every day** at your chosen time (e.g., 8:00 AM)
- **Automatic schedule adjustment** - 5-hour cycles restart from daily reset
- **Work-day optimization** - Clean slate every morning

### 🔍 Comprehensive Monitoring
- **Real-time logging** - See exactly what Claude Code is doing
- **Daily schedule display** - Know today's planned check times
- **Countdown timers** - Track time until next session
- **Failure detection** - Optional webhook alerts when things break

### 🛠️ System Optimizations
- **RAM optimizations** - Limits Node.js memory usage (perfect for Pi 3B)
- **Process priority management** - Runs at lower priority to avoid system impact
- **Telemetry disabled** - No unnecessary data transmission

## Requirements

- **Claude Code CLI** installed and logged in
- **Python 3.7+** with pip
- **Node.js 18+** (for Claude Code)
- **Linux/macOS/Windows** (optimized for Raspberry Pi)

## Installation

### 1. Install Claude Code
```bash
# Install Node.js 20 (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# Login to your Anthropic account
claude login
```

### 2. Install Session Keeper
```bash
# Clone this repository
git clone https://github.com/awesomecoolraj/claude-session-keeper.git
cd claude-session-keeper

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Test Installation
```bash
# Quick test to verify everything works
python claude_health_check_cli.py --once
```

## 📖 Usage Guide

### Basic Commands

#### Single Test Run
```bash
python claude_health_check_cli.py --once
```
**Use case:** Test that Claude Code is working and accessible

#### Start with Default Schedule  
```bash
python claude_health_check_cli.py
```
**Use case:** Begin 5-hour cycles starting at 4:01:10 PM (in your timezone)

#### Start at Specific Time
```bash
python claude_health_check_cli.py --unix-timestamp=1755316870
```
**Use case:** Control exactly when your first session begins

### Advanced Features

#### Daily Reset (Recommended)
```bash
python claude_health_check_cli.py --daily-reset=08:00
```
**What happens:**
- 8:00 AM → Fresh session starts (daily reset)
- 1:00 PM → 5-hour check 
- 6:00 PM → 5-hour check
- 11:00 PM → 5-hour check  
- 4:00 AM → 5-hour check
- 8:00 AM → Daily reset (cycle repeats)

#### Combined Scheduling
```bash
python claude_health_check_cli.py --unix-timestamp=1755316870 --daily-reset=08:00
```
**Use case:** Start immediately at specific time, then daily resets at 8:00 AM

#### Resume After Restart
```bash
python claude_health_check_cli.py --resume
```
**Use case:** Continue from where you left off after system reboot

### 24/7 Operation

#### Run in Background
```bash
# Start in background with output logging
nohup python claude_health_check_cli.py --daily-reset=08:00 > health_check.out 2>&1 &
```

#### Auto-start on Boot
```bash
# Add to crontab for automatic startup
crontab -e

# Add this line:
@reboot cd /path/to/claude-session-keeper && source venv/bin/activate && nohup python claude_health_check_cli.py --resume > health_check.out 2>&1 &
```

## ⚙️ Configuration

### Optional Webhook Alerts
Create `config.json` for failure notifications:
```json
{
  "webhook_url": "https://webhook.site/your-unique-id"
}
```

**Setup webhook:**
1. Visit [webhook.site](https://webhook.site) (free, no signup)
2. Copy your unique URL
3. Add to config.json
4. Get notified when Claude Code has issues

### Timezone Handling
The script automatically detects your system timezone. Daily reset times are in **your local time**, not UTC or Pacific.

## 📊 Examples & Use Cases

### Example 1: Developer Workflow
```bash
python claude_health_check_cli.py --daily-reset=09:00
```
**Perfect for:** Starting each work day with a fresh Claude session at 9:00 AM

### Example 2: Always-On Monitoring  
```bash
python claude_health_check_cli.py --unix-timestamp=1755316870
```
**Perfect for:** Precise session timing without daily resets

### Example 3: Raspberry Pi 24/7
```bash
nohup python claude_health_check_cli.py --daily-reset=08:00 > logs.txt 2>&1 &
```
**Perfect for:** Set-and-forget operation on low-power devices

## 🔧 System Requirements & Optimization

### Minimum Hardware
- **RAM:** 512MB (1GB+ recommended)  
- **CPU:** Any ARM/x64 processor
- **Storage:** 100MB for installation
- **Network:** Stable internet connection

### Raspberry Pi Optimization
The script includes several optimizations for low-power devices:
- **Node.js memory limit:** 256MB (prevents crashes)
- **Reduced thread pool:** Minimizes CPU usage  
- **Disabled telemetry:** Saves bandwidth and processing
- **Lower process priority:** Won't interfere with other tasks

### Power Consumption
**Raspberry Pi 3B:** ~$0.26/month in electricity
- Active for ~5 seconds every 5 hours
- 99.97% idle time
- Extremely efficient operation

## 📋 Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `--once` | Run single test | `python claude_health_check_cli.py --once` |
| `--unix-timestamp=X` | Start at specific time | `--unix-timestamp=1755316870` |
| `--daily-reset=HH:MM` | Daily reset at time | `--daily-reset=08:00` |
| `--resume` | Resume from last run | `python claude_health_check_cli.py --resume` |
| (no args) | Default schedule | Starts at 4:01:10 PM |

### Combining Commands
You can combine most commands:
```bash
python claude_health_check_cli.py --unix-timestamp=1755316870 --daily-reset=09:00
```

## 🔍 Monitoring & Logs

### Log Output
The script provides detailed logging:
```
2025-08-16 08:00:10 - INFO - 🔄 DAILY RESET - starting fresh session
2025-08-16 08:00:15 - INFO - Claude responded: Hi! How can I help you today?
2025-08-16 08:00:15 - INFO - Health check completed successfully
2025-08-16 08:00:16 - INFO - Next check: 2025-08-16 13:00:10 
2025-08-16 08:00:16 - INFO - Time until next check: 5h 0m 0s
```

### Daily Schedule Display
```
📅 NEW DAY: Saturday, August 17, 2025
Today's schedule: 08:00 (reset), 13:00, 18:00, 23:00
```

### Failure Detection
When Claude Code has issues:
```
2025-08-16 08:00:10 - ERROR - Claude command timed out
2025-08-16 08:00:10 - ERROR - Health check failed: Timeout
```

## ❓ FAQ

### Is this allowed by Anthropic?
**Yes!** This script:
- Uses Claude Code's official CLI as intended
- Doesn't exceed rate limits (uses 1 of 10-800 messages)  
- Simply optimizes timing, not circumventing restrictions
- Claude Code has headless mode designed for automation

### Will this use up my Claude quota?
**Minimal impact!** 
- Uses 1 message per 5-hour window
- That's ~4-5 messages per day  
- Vs. your 10-800 message limit per window

### Can I run this on multiple devices?
**Not recommended.** Multiple devices would create overlapping sessions and waste quota. Run on one primary device.

### What if my Pi crashes?
Use `--resume` to continue from where you left off. The script saves timestamps for recovery.

### Does this work globally?
**Yes!** Automatic timezone detection works worldwide. Daily reset times are in your local timezone.

## 🐛 Troubleshooting

### Claude Code Not Found
```bash
# Verify Claude Code installation
claude --version
which claude

# If missing, reinstall:
npm install -g @anthropic-ai/claude-code
```

### Permission Errors  
```bash
# Use virtual environment to avoid system conflicts
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Timeout Issues (Raspberry Pi)
The script automatically increases timeouts for slow devices. If still timing out:
```bash
# Check available memory
free -h

# Increase swap if needed
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup && sudo dphys-swapfile swapon
```

### Claude Code Authentication  
```bash
# Re-login if sessions fail
claude login

# Verify login works
claude Hi
```

## 🤝 Contributing

Contributions welcome! Please:

1. **Fork** the repository
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open Pull Request**

### Development Setup
```bash
git clone https://github.com/awesomecoolraj/claude-session-keeper.git
cd claude-session-keeper
python3 -m venv dev-env
source dev-env/bin/activate
pip install -r requirements.txt
```

## 📄 License

MIT License - Use it however you want!

## 🎯 Real-World Impact

> *"Just saved 2 hours with the 5-hour block for the first time!"* - @awesomecoolraj

This script has helped users:
- **Maximize Claude Code usage** during work hours
- **Eliminate random session timing** frustrations  
- **Run 24/7 monitoring** on Raspberry Pi devices
- **Optimize development workflows** with predictable access

---

**Made by [@awesomecoolraj](https://github.com/awesomecoolraj)**

*Intelligent Claude Code session management since 2025* ⏰

**⭐ Star this repo if it helps optimize your Claude Code workflow!**