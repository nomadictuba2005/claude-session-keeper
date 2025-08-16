# Claude Session Keeper

🤖 **Automatically optimize your Claude Code session timing by sending periodic health checks.**

## What It Does

Claude Code uses 5-hour session windows that start with your first message. This script:

- ✅ Sends a simple "Hi" message to Claude Code every 5 hours
- ✅ Optimizes session timing by controlling when your 5-hour windows begin  
- ✅ Ensures maximum availability during your actual work hours
- ✅ Uses minimal quota (1 message per 5-hour window vs 10-800 limit)

## How Claude Code Sessions Work

Claude Code limits work with **fixed 5-hour windows**:
1. Window starts with your **first message**
2. Once you hit your limit, you're locked out until **5 hours after that first message**
3. This script starts each new window **immediately** when the previous expires

**Instead of random session timing → Predictable, optimized scheduling** 🎯

## Requirements

- **Claude Code CLI** installed and logged in
- **Python 3.7+**
- **Linux/macOS/Windows** (tested on Raspberry Pi 3B+)

## Installation

### 1. Install Claude Code
```bash
# Install Node.js first
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Claude Code  
npm install -g @anthropic-ai/claude-code

# Login
claude login
```

### 2. Install Python Dependencies
```bash
# Clone this repository
git clone https://github.com/awesomecoolraj/claude-session-keeper.git
cd claude-session-keeper

# Install Python packages
pip install -r requirements.txt
```

## Usage

### Quick Test
```bash
# Test that everything works
python claude_health_check_cli.py --once
```

### Start at Specific Time  
```bash
# Start first health check at exact unix timestamp
python claude_health_check_cli.py --unix-timestamp=1755316870

# The script will:
# 1. Wait until that exact time
# 2. Send "Hi" to Claude Code  
# 3. Repeat every 5 hours forever
```

### Resume from Previous Run
```bash
# Resume from last saved timestamp
python claude_health_check_cli.py --resume
```

### Run in Background (Raspberry Pi/Linux)
```bash
# Start in background
nohup python claude_health_check_cli.py --unix-timestamp=1755316870 > health_check.out 2>&1 &

# Auto-start on boot (add to crontab)
crontab -e
# Add: @reboot cd /path/to/claude-session-keeper && nohup python claude_health_check_cli.py --resume > health_check.out 2>&1 &
```

## Optional: Webhook Alerts

Create `config.json` for failure notifications:
```json
{
  "webhook_url": "https://webhook.site/your-unique-id"
}
```

Get a free webhook URL at [webhook.site](https://webhook.site) - no signup required!

## Command Options

```bash
python claude_health_check_cli.py [OPTIONS]

# Options:
--once                          # Run single test
--unix-timestamp=<timestamp>    # Start at specific time  
--resume                        # Resume from last run
```

## Example: Perfect Timing

**Without this script:**
- You start Claude at 2:47 PM → window expires at 7:47 PM
- Need Claude at 8:00 PM → have to wait until 7:47 PM for reset
- Your window randomly starts whenever you first use Claude

**With this script:**  
- Health check at 4:01 PM → window always expires at 9:01 PM
- Need Claude at 9:30 PM → window starts exactly at 9:01 PM
- Predictable, optimized session timing

## Power Consumption

**Raspberry Pi 3B:** ~26 cents per month electricity cost
- Script runs for ~5 seconds every 5 hours
- Extremely lightweight and efficient

## Is This Allowed?

✅ **Absolutely!** This script:
- Uses Claude Code's official CLI as intended
- Doesn't exceed any rate limits (uses 1 of 10-800 message quota)
- Simply optimizes **timing** of when sessions start
- Is not circumventing limits, just scheduling efficiently

Claude Code even has headless mode designed for automation and CI pipelines.

## Contributing

Found a bug or want to improve something? Pull requests welcome!

## License

MIT License - Use it however you want!

---

**Made by [@awesomecoolraj](https://github.com/awesomecoolraj)** 

*Keeping Claude Code sessions perfectly timed since 2025* ⏰