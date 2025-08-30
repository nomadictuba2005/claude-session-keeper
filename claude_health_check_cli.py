#!/usr/bin/env python3
"""
Claude Code CLI Health Check
Simple health check using Claude Code CLI commands
"""
import subprocess
import time
import json
import threading
import logging
import requests
import sys
import os
from datetime import datetime, timezone, timedelta
import pytz

# Fix Windows console encoding for Unicode support
if sys.platform == 'win32':
    try:
        # Set console to UTF-8 mode
        os.system('chcp 65001 > nul')
        # Enable virtual terminal processing for ANSI escape codes
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass  # Fallback if console setup fails

# Force UTF-8 encoding for stdout and stderr to handle redirection properly
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

class ClaudeCodeHealthCheck:
    def __init__(self, webhook_url=None, daily_reset_time=None):
        self.webhook_url = webhook_url
        self.failure_count = 0
        self.daily_reset_time = daily_reset_time  # Format: "HH:MM" in local time
        
        # Check if terminal supports Unicode
        self.unicode_supported = self._check_unicode_support()

        # Setup logging with Unicode awareness
        # Create a custom formatter that handles Unicode properly
        class UnicodeFormatter(logging.Formatter):
            def format(self, record):
                # Ensure the message is properly encoded
                if isinstance(record.msg, str):
                    # Convert any embedded Unicode escape sequences back to characters
                    import re
                    record.msg = re.sub(r'\\U([0-9a-fA-F]{8})', lambda m: chr(int(m.group(1), 16)), record.msg)
                    record.msg = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), record.msg)
                return super().format(record)

        # Configure file handler with UTF-8 and proper formatting
        import codecs
        file_handler = logging.FileHandler('claude_health_check.log', encoding='utf-8')
        # Ensure the file handler uses UTF-8 encoding properly
        if hasattr(file_handler.stream, 'reconfigure'):
            try:
                file_handler.stream.reconfigure(encoding='utf-8')
            except Exception:
                pass  # Fallback if reconfigure is not available
        file_handler.setFormatter(UnicodeFormatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Configure stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, stream_handler]
        )
        self.logger = logging.getLogger(__name__)

        # Test Unicode logging to ensure it works properly
        self._test_unicode_logging()

    def _test_unicode_logging(self):
        """Test that Unicode characters log correctly"""
        try:
            # Create a test message with Unicode
            test_msg = f"Unicode test: {self._get_icon('reset')} {self._get_icon('new_day')}"
            self._safe_log('debug', f"Unicode logging test: {test_msg}")
        except Exception as e:
            self._safe_log('warning', f"Unicode logging test failed: {e}")

    def _check_unicode_support(self):
        """Check if terminal supports Unicode characters"""
        try:
            # Test multiple methods to ensure robust detection

            # Method 1: Check stdout encoding
            if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
                try:
                    '🔄'.encode(sys.stdout.encoding)
                    stdout_supports_unicode = True
                except UnicodeEncodeError:
                    stdout_supports_unicode = False
            else:
                stdout_supports_unicode = False

            # Method 2: Check stderr encoding (for logging)
            if hasattr(sys.stderr, 'encoding') and sys.stderr.encoding:
                try:
                    '🔄'.encode(sys.stderr.encoding)
                    stderr_supports_unicode = True
                except UnicodeEncodeError:
                    stderr_supports_unicode = False
            else:
                stderr_supports_unicode = False

            # Method 3: Check environment variables
            env_supports_unicode = (
                os.environ.get('LANG', '').endswith('UTF-8') or
                os.environ.get('LC_ALL', '').endswith('UTF-8') or
                os.environ.get('LC_CTYPE', '').endswith('UTF-8') or
                sys.platform == 'win32'  # Windows consoles generally support Unicode now
            )

            # Method 4: Try to write to a temporary file (fallback)
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
                    f.write('🔄')
                    f.flush()
                file_supports_unicode = True
                os.unlink(f.name)
            except (UnicodeEncodeError, OSError):
                file_supports_unicode = False

            # Return True if any method indicates Unicode support
            # Prioritize stdout/stderr support for immediate output
            if stdout_supports_unicode or stderr_supports_unicode:
                return True
            elif env_supports_unicode and file_supports_unicode:
                return True
            else:
                return False

        except Exception:
            # Conservative fallback - assume no Unicode support if anything fails
            return False
    def _recheck_unicode_support(self):
        """Re-check Unicode support at runtime (useful when output is redirected)"""
        try:
            # Allow user to force Unicode via environment variable
            force_unicode = os.environ.get('CLAUDE_FORCE_UNICODE', '').lower() in ('1', 'true', 'yes')

            if force_unicode:
                return True

            # Check if we're writing to a file vs terminal
            is_redirected = not sys.stdout.isatty() or not sys.stderr.isatty()

            if is_redirected:
                # When output is redirected, prioritize environment settings and platform
                # This is more reliable than file encoding tests
                env_supports_unicode = (
                    os.environ.get('LANG', '').endswith('UTF-8') or
                    os.environ.get('LC_ALL', '').endswith('UTF-8') or
                    os.environ.get('LC_CTYPE', '').endswith('UTF-8') or
                    sys.platform == 'win32'  # Windows consoles generally support Unicode
                )

                # On modern systems, UTF-8 is widely supported
                # Be more permissive when output is redirected
                return env_supports_unicode or sys.platform in ['win32', 'darwin'] or True  # Default to True for modern systems
            else:
                # For terminal output, use the original detection
                return self.unicode_supported

        except Exception:
            return False

    def _get_icon(self, icon_name):
        """Get appropriate icon based on Unicode support"""
        # Use runtime check for better accuracy
        use_unicode = self._recheck_unicode_support()

        if use_unicode:
            icons = {
                'reset': '🔄',
                'new_day': '📅',
                'alert': '🚨',
                'check': '✓',
                'cross': '✗'
            }
        else:
            icons = {
                'reset': '[RESET]',
                'new_day': '[NEW DAY]',
                'alert': '[ALERT]',
                'check': '[OK]',
                'cross': '[FAIL]'
            }
        return icons.get(icon_name, '')

    def _safe_log(self, level, message, *args, **kwargs):
        """Safely log a message ensuring Unicode characters are preserved"""
        try:
            # Ensure the message is a proper Unicode string
            if isinstance(message, str):
                # Convert any escape sequences back to Unicode characters
                import re
                message = re.sub(r'\\U([0-9a-fA-F]{8})', lambda m: chr(int(m.group(1), 16)), message)
                message = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), message)

            # Log the message
            getattr(self.logger, level)(message, *args, **kwargs)
        except Exception as e:
            # Fallback to basic logging if Unicode processing fails
            # Use direct logging to avoid recursion
            self.logger.warning(f"Unicode logging failed, using fallback: {str(e)}")
            getattr(self.logger, level)(str(message), *args, **kwargs)

    def send_webhook_alert(self, subject, message):
        """Send webhook notification"""
        if not self.webhook_url:
            return False
            
        try:
            payload = {
                "text": f"{self._get_icon('alert')} {subject}",
                "alert": "Claude Code Health Check Alert",
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"Webhook alert sent: {subject}")
                return True
            else:
                self.logger.error(f"Webhook failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
            return False
    
    def run_claude_command(self, message="Hi"):
        """Run a simple Claude Code CLI command"""
        try:
            # Use Claude Code CLI to send a simple message
            self.logger.info("Executing: npx claude --dangerously-skip-permissions Hi")
            
            # RAM optimizations for Pi 3B
            import os
            env = os.environ.copy()
            env['NODE_ENV'] = 'production'
            env['NODE_OPTIONS'] = '--max-old-space-size=256 --max-semi-space-size=2'  # Limit Node.js to 256MB
            env['UV_THREADPOOL_SIZE'] = '2'  # Reduce thread pool
            env['CLAUDE_DISABLE_TELEMETRY'] = '1'  # Disable telemetry
            env['CLAUDE_DISABLE_ANALYTICS'] = '1'  # Disable analytics
            
            # Use Popen for real-time output
            self.logger.info("Starting Claude Code process...")
            self.logger.info(f"RAM optimization: Node.js limited to 256MB")
            
            # Cross-platform process creation with priority handling
            popen_kwargs = {
                'shell': True,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True,
                'env': env,
                'cwd': os.path.expanduser('~'),
                'universal_newlines': True,
                'bufsize': 1,
            }

            # Add platform-specific priority control
            import platform
            if platform.system() == 'Windows':
                popen_kwargs['creationflags'] = subprocess.BELOW_NORMAL_PRIORITY_CLASS
            else:
                popen_kwargs['preexec_fn'] = lambda: os.nice(10) if hasattr(os, 'nice') else None

            process = subprocess.Popen('npx claude --dangerously-skip-permissions Hi', **popen_kwargs)
            # Log output in real-time
            stdout_lines = []
            stderr_lines = []
            
            try:
                # Wait for completion with timeout
                stdout, stderr = process.communicate(timeout=480)
                
                # Log all output
                if stdout:
                    self.logger.info(f"Claude STDOUT:\n{stdout}")
                    stdout_lines.append(stdout)
                if stderr:
                    self.logger.info(f"Claude STDERR:\n{stderr}")
                    stderr_lines.append(stderr)
                
                return_code = process.returncode
                self.logger.info(f"Command completed with return code: {return_code}")
                
                if return_code == 0:
                    response = stdout.strip() if stdout else ""
                    self.logger.info(f"Claude responded successfully")
                    return True, response
                else:
                    error_msg = stderr.strip() if stderr else f"Exit code {return_code}"
                    self.logger.error(f"Claude command failed: {error_msg}")
                    return False, error_msg
                    
            except subprocess.TimeoutExpired:
                self.logger.error("Claude command timed out - killing process")
                process.kill()
                stdout, stderr = process.communicate()
                if stdout:
                    self.logger.info(f"Partial STDOUT before timeout:\n{stdout}")
                if stderr:
                    self.logger.info(f"Partial STDERR before timeout:\n{stderr}")
                return False, "Timeout"
                
        except subprocess.TimeoutExpired:
            self.logger.error("Claude command timed out")
            return False, "Timeout"
        except FileNotFoundError:
            self.logger.error("Claude CLI not found - install Claude Code first")
            return False, "CLI not found"
        except Exception as e:
            self.logger.error(f"Error running Claude command: {e}")
            return False, str(e)
    
    def run_health_check(self):
        """Run complete health check"""
        self.logger.info("Starting Claude Code CLI health check...")
        
        success, response = self.run_claude_command("Hi")
        
        if success:
            self.failure_count = 0
            self.logger.info(f"Health check completed successfully. Response: {response}")
            return True
        else:
            self.failure_count += 1
            
            # Alert after 3 consecutive failures
            if self.failure_count >= 3:
                alert_msg = f"""
Claude Code CLI Health Check Alert

Claude Code appears to be having issues after {self.failure_count} consecutive failures.

Last error: {response}

Please check:
1. Claude Code CLI installation
2. Internet connection
3. Claude.ai service status
4. Authentication/login status

Time: {datetime.now()}
"""
                self.send_webhook_alert("Claude Code CLI Issues", alert_msg)
            
            self.logger.error(f"Health check failed: {response}")
            return False
    
    def calculate_next_run_time(self, first_run_timestamp=None, resume_from_timestamp=None):
        """Calculate when to run next"""
        # Use system's local timezone
        local_tz = datetime.now().astimezone().tzinfo
        now = datetime.now(local_tz)
        
        if first_run_timestamp:
            # Start at specific unix timestamp
            first_run = datetime.fromtimestamp(first_run_timestamp, tz=local_tz)
            self.logger.info(f"First run scheduled at specified time: {first_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            return first_run
            
        elif resume_from_timestamp:
            # Resume from a specific timestamp (when script was stopped)
            last_run = datetime.fromtimestamp(resume_from_timestamp, tz=local_tz)
            self.logger.info(f"Resuming from last run: {last_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Calculate next run (5 hours from last run)
            next_run = last_run + timedelta(hours=5)
            
            # If next run is in the past, schedule it now
            if next_run <= now:
                self.logger.info("Next scheduled time is in the past, running immediately")
                return now
            
            return next_run
        else:
            # First run: Today at 4:01:10 PM local time
            today = now.date()
            first_run = now.replace(hour=16, minute=1, second=10, microsecond=0)
            first_run = first_run.replace(day=today.day, month=today.month, year=today.year)
            
            # If it's already past 4:01:10 PM today, schedule for tomorrow
            if now > first_run:
                first_run = first_run + timedelta(days=1)
            
            return first_run
    
    def calculate_next_daily_reset(self):
        """Calculate next daily reset time"""
        if not self.daily_reset_time:
            return None
            
        # Use system's local timezone
        local_tz = datetime.now().astimezone().tzinfo
        
        now = datetime.now(local_tz)
        
        # Parse reset time
        reset_hour, reset_minute = map(int, self.daily_reset_time.split(':'))
        
        # Calculate today's reset time
        today_reset = now.replace(hour=reset_hour, minute=reset_minute, second=10, microsecond=0)
        
        # If today's reset time has passed, schedule for tomorrow
        if now >= today_reset:
            from datetime import timedelta
            today_reset = today_reset + timedelta(days=1)
            
        return today_reset
    
    def start_scheduler(self, first_run_timestamp=None, resume_from_timestamp=None):
        """Start 5-hour scheduled health checks with optional daily resets"""
        # Get system's local timezone - works on all systems
        import time
        
        # Use system timezone - this works reliably on Linux/Windows/Mac
        local_tz = datetime.now().astimezone().tzinfo
        
        self.logger.info(f"Detected system timezone: {local_tz}")
        self.logger.info(f"Current local time: {datetime.now(local_tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Use local timezone for all calculations
        pst = local_tz  # Keep variable name for compatibility
        
        # Calculate next daily reset if enabled
        next_daily_reset = self.calculate_next_daily_reset()
        
        # If daily reset exists and comes before default schedule, use daily reset as starting point
        if next_daily_reset and not first_run_timestamp and not resume_from_timestamp:
            default_next_run = self.calculate_next_run_time(first_run_timestamp, resume_from_timestamp)
            
            if (next_daily_reset - datetime.now(pst)).total_seconds() <= (default_next_run - datetime.now(pst)).total_seconds():
                # Daily reset comes first, so use it as the starting point
                next_run = next_daily_reset
                self.logger.info("Daily reset detected - starting schedule from daily reset time")
            else:
                next_run = default_next_run
        else:
            # Use original calculation
            next_run = self.calculate_next_run_time(first_run_timestamp, resume_from_timestamp)
        
        # Show the actual schedule that will run
        now = datetime.now(pst)
        time_until_first = next_run - now
        hours = int(time_until_first.total_seconds() // 3600)
        minutes = int((time_until_first.total_seconds() % 3600) // 60)
        seconds = int(time_until_first.total_seconds() % 60)
        
        if next_daily_reset and next_run == next_daily_reset:
            # Started with daily reset
            self._safe_log('info', f"{self._get_icon('reset')} First run: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')} (daily reset)")
            self._safe_log('info', f"Time until first run: {hours}h {minutes}m {seconds}s")

            # Show 5-hour schedule from daily reset
            from datetime import timedelta
            check_times = []
            for i in range(1, 5):  # Show next 4 times
                check_time = next_daily_reset + timedelta(hours=5*i)
                check_times.append(check_time.strftime('%H:%M'))
            self._safe_log('info', f"Then 5-hour checks: {', '.join(check_times)}")
            
            # Show next daily reset
            next_daily_after = self.calculate_next_daily_reset()
            if next_daily_after != next_daily_reset:
                self.logger.info(f"Next daily reset: {next_daily_after.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                
        elif next_daily_reset:
            # Regular first run, but daily reset is scheduled
            self.logger.info(f"First health check: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            self.logger.info(f"Time until first check: {hours}h {minutes}m {seconds}s")
            self.logger.info(f"Daily reset enabled at: {self.daily_reset_time} local time")
            self.logger.info(f"Next daily reset: {next_daily_reset.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
        else:
            # No daily reset
            self.logger.info(f"First health check: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            self.logger.info(f"Time until first check: {hours}h {minutes}m {seconds}s")
            self.logger.info("Then every 5 hours after that")
        
        last_logged_date = None
        
        while True:
            now = datetime.now(pst)
            
            # Check if we've crossed midnight and log today's schedule
            current_date = now.date()
            if last_logged_date != current_date:
                self._safe_log('info', f"{self._get_icon('new_day')} NEW DAY: {current_date.strftime('%A, %B %d, %Y')}")
                
                if next_daily_reset:
                    # Show today's schedule with daily reset
                    from datetime import timedelta
                    today_reset = now.replace(hour=int(self.daily_reset_time.split(':')[0]), 
                                            minute=int(self.daily_reset_time.split(':')[1]), 
                                            second=10, microsecond=0)
                    
                    if now > today_reset:
                        # Reset already happened today, show remaining checks
                        self.logger.info(f"Today's daily reset ({self.daily_reset_time}) already completed")
                        remaining_checks = []
                        check_time = today_reset
                        while check_time.date() == current_date:
                            check_time += timedelta(hours=5)
                            if check_time.date() == current_date and check_time > now:
                                remaining_checks.append(check_time.strftime('%H:%M'))
                        
                        if remaining_checks:
                            self.logger.info(f"Remaining today: {', '.join(remaining_checks)}")
                        else:
                            self.logger.info("No more checks today")
                    else:
                        # Reset coming today - calculate 5-hour intervals from daily reset time
                        reset_hour, reset_minute = map(int, self.daily_reset_time.split(':'))
                        schedule_times = [self.daily_reset_time]
                        for i in range(1, 4):  # Add next 3 5-hour intervals
                            next_time = today_reset + timedelta(hours=5*i)
                            if next_time.date() == current_date:
                                schedule_times.append(next_time.strftime('%H:%M'))
                        schedule_str = ', '.join(schedule_times)
                        self.logger.info(f"Today's schedule: {schedule_str}")
                else:
                    self.logger.info("Today's schedule: 5-hour intervals continuing from previous cycle")
                
                last_logged_date = current_date
            
            # Determine which event comes next: 5-hour check or daily reset
            time_to_next_run = (next_run - now).total_seconds()
            time_to_daily_reset = (next_daily_reset - now).total_seconds() if next_daily_reset else float('inf')
            
            # If daily reset is closer than 5-hour check, wait for daily reset
            if next_daily_reset and time_to_daily_reset <= time_to_next_run and now >= next_daily_reset:
                self._safe_log('info', f"{self._get_icon('reset')} DAILY RESET at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                self.logger.info("Daily reset overriding 5-hour schedule - starting fresh session")
                
                # Save timestamp for resume feature
                with open('last_run_timestamp.txt', 'w') as f:
                    f.write(str(int(now.timestamp())))
                
                # Run health check
                thread = threading.Thread(target=self.run_health_check)
                thread.start()
                
                # Reset both timers - next 5-hour cycle starts from daily reset
                from datetime import timedelta
                next_run = now + timedelta(hours=5)
                next_daily_reset = self.calculate_next_daily_reset()
                
                # Log new schedule
                time_until_next = next_run - now
                hours = int(time_until_next.total_seconds() // 3600)
                minutes = int((time_until_next.total_seconds() % 3600) // 60)
                seconds = int(time_until_next.total_seconds() % 60)
                
                self.logger.info(f"5-hour schedule reset - Next check: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                self.logger.info(f"Next daily reset: {next_daily_reset.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                self.logger.info(f"Time until next check: {hours}h {minutes}m {seconds}s")
                
            # Check if it's time for regular 5-hour run (only if no daily reset is pending)
            elif now >= next_run:
                self.logger.info(f"Running scheduled health check at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                
                # Save timestamp for resume feature
                with open('last_run_timestamp.txt', 'w') as f:
                    f.write(str(int(now.timestamp())))
                
                # Run in a separate thread so timing is precise
                thread = threading.Thread(target=self.run_health_check)
                thread.start()
                
                # Schedule next run exactly 5 hours from NOW (when this run BEGAN)
                from datetime import timedelta
                next_run = now + timedelta(hours=5)
                
                # Calculate time until next run
                time_until_next = next_run - now
                hours = int(time_until_next.total_seconds() // 3600)
                minutes = int((time_until_next.total_seconds() % 3600) // 60)
                seconds = int(time_until_next.total_seconds() % 60)
                
                self.logger.info(f"Next health check scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                self.logger.info(f"Time until next check: {hours}h {minutes}m {seconds}s")
            
            # Show live countdown every 60 seconds
            time_until_next = next_run - now
            if time_until_next.total_seconds() > 0:
                hours = int(time_until_next.total_seconds() // 3600)
                minutes = int((time_until_next.total_seconds() % 3600) // 60)
                seconds = int(time_until_next.total_seconds() % 60)
                
                # Log countdown every minute
                if seconds == 0 or time_until_next.total_seconds() <= 60:
                    self.logger.info(f"Next health check in: {hours}h {minutes}m {seconds}s")
            
            # Check every 10 seconds for precise timing
            time.sleep(10)

if __name__ == "__main__":
    import sys

    # Load config
    config_file = "config.json"
    config = {}

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Config file {config_file} not found. Creating simple config...")

        # Create simple config
        sample_config = {
            "webhook_url": "https://webhook.site/cd441013-0fe4-493a-b83e-980bc8c8b1e5"
        }
        with open(config_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        print(f"Created {config_file} - update webhook_url if needed")

    # Test Unicode support before initializing
    if len(sys.argv) > 1 and sys.argv[1] == "--test-unicode":
        test_checker = ClaudeCodeHealthCheck()
        runtime_unicode = test_checker._recheck_unicode_support()
        print(f"Constructor Unicode support: {test_checker.unicode_supported}")
        print(f"Runtime Unicode support: {runtime_unicode}")
        print(f"Output redirected: {not sys.stdout.isatty() or not sys.stderr.isatty()}")
        print(f"stdout encoding: {getattr(sys.stdout, 'encoding', 'None')}")
        print(f"stderr encoding: {getattr(sys.stderr, 'encoding', 'None')}")
        print()
        print("Icons with current settings:")
        print(f"Reset icon: '{test_checker._get_icon('reset')}'")
        print(f"New day icon: '{test_checker._get_icon('new_day')}'")
        print(f"Alert icon: '{test_checker._get_icon('alert')}'")
        print(f"Check icon: '{test_checker._get_icon('check')}'")
        print(f"Cross icon: '{test_checker._get_icon('cross')}'")
        sys.exit(0)
    
    # Parse daily reset time from args if provided
    daily_reset_time = None
    for arg in sys.argv:
        if arg.startswith("--daily-reset="):
            daily_reset_time = arg.split("=")[1]
            break
    
    # Initialize health checker
    health_checker = ClaudeCodeHealthCheck(
        webhook_url=config.get('webhook_url'),
        daily_reset_time=daily_reset_time
    )
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            print("Running single health check...")
            success = health_checker.run_health_check()
            if success:
                print(f"{health_checker._get_icon('check')} Health check completed successfully!")
            else:
                print(f"{health_checker._get_icon('cross')} Health check failed. Check claude_health_check.log")
            sys.exit(0)
        
        elif sys.argv[1] == "--resume":
            # Resume from last saved timestamp
            try:
                with open('last_run_timestamp.txt', 'r') as f:
                    timestamp = int(f.read().strip())
                print(f"Resuming from timestamp: {timestamp}")
                print("Starting 24/7 Claude Code health check scheduler...")
                print("Press Ctrl+C to stop")
                try:
                    health_checker.start_scheduler(resume_from_timestamp=timestamp)
                except KeyboardInterrupt:
                    print("\nHealth check scheduler stopped")
            except FileNotFoundError:
                print("No previous run found. Starting fresh.")
                print("Starting 24/7 Claude Code health check scheduler...")
                print("Press Ctrl+C to stop")
                try:
                    health_checker.start_scheduler()
                except KeyboardInterrupt:
                    print("\nHealth check scheduler stopped")
        
        elif sys.argv[1].startswith("--unix-timestamp="):
            # Start first run at specific timestamp
            timestamp = int(sys.argv[1].split("=")[1])
            pst = pytz.timezone('US/Pacific')
            scheduled_time = datetime.fromtimestamp(timestamp, tz=pst)
            print(f"Starting first run at unix timestamp: {timestamp}")
            print(f"That's: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            if daily_reset_time:
                print(f"With daily reset at: {daily_reset_time}")
            print("Starting 24/7 Claude Code health check scheduler...")
            print("Press Ctrl+C to stop")
            try:
                health_checker.start_scheduler(first_run_timestamp=timestamp)
            except KeyboardInterrupt:
                print("\nHealth check scheduler stopped")
        
        elif sys.argv[1].startswith("--daily-reset="):
            # Just daily reset, start immediately with default schedule
            print(f"Starting with daily reset at: {daily_reset_time}")
            print("Starting 24/7 Claude Code health check scheduler...")
            print("Press Ctrl+C to stop")
            try:
                health_checker.start_scheduler()
            except KeyboardInterrupt:
                print("\nHealth check scheduler stopped")
        
        else:
            print("Usage:")
            print("  python claude_health_check_cli.py                    # Start fresh (4:01:10 PM PST)")
            print("  python claude_health_check_cli.py --once             # Run once")
            print("  python claude_health_check_cli.py --resume           # Resume from last run")
            print("  python claude_health_check_cli.py --test-unicode     # Test Unicode support")
            print("  python claude_health_check_cli.py --unix-timestamp=<timestamp>  # Start first run at exact time")
            print("  python claude_health_check_cli.py --daily-reset=HH:MM # Add daily reset at specific time")
            print("  python claude_health_check_cli.py --unix-timestamp=<timestamp> --daily-reset=09:00  # Combined")
    else:
        print("Starting 24/7 Claude Code health check scheduler...")
        print("Press Ctrl+C to stop")
        try:
            health_checker.start_scheduler()
        except KeyboardInterrupt:
            print("\nHealth check scheduler stopped")