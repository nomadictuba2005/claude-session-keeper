#!/usr/bin/env python3
"""
Interactive Terminal User Interface
Menu-driven interface for Claude Session Keeper
"""
import os
import sys
import time
import json
import threading
from datetime import datetime
from typing import Optional, Callable
from dataclasses import asdict

# Import our modules
from session_stats import SessionStats
from notifications import NotificationManager, NotificationConfig, NotificationLevel
from profiles import ProfileManager, ScheduleProfile


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str = "Claude Session Keeper"):
    """Print a styled header"""
    width = 60
    print("=" * width)
    print(f"{title:^{width}}")
    print("=" * width)
    print()


def print_menu(options: list, title: str = "Menu"):
    """Print a menu with numbered options"""
    print(f"\n--- {title} ---")
    for i, option in enumerate(options, 1):
        print(f"  [{i}] {option}")
    print(f"  [0] Back / Exit")
    print()


def get_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def get_choice(max_choice: int) -> int:
    """Get a numeric choice from user"""
    try:
        choice = input("Enter choice: ").strip()
        if choice == '':
            return -1
        return int(choice)
    except ValueError:
        return -1


def format_time_ago(timestamp_str: str) -> str:
    """Format a timestamp as relative time"""
    if not timestamp_str:
        return "Never"

    try:
        ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()
        diff = now - ts

        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = (diff.seconds % 3600) // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "Just now"
    except:
        return timestamp_str


class InteractiveCLI:
    """Interactive command-line interface"""

    def __init__(self, health_checker=None):
        self.health_checker = health_checker
        self.stats = SessionStats()
        self.notifications = NotificationManager()
        self.profiles = ProfileManager()
        self.running = True
        self.scheduler_thread: Optional[threading.Thread] = None

    def run(self):
        """Main loop for interactive CLI"""
        while self.running:
            clear_screen()
            self.show_main_menu()

    def show_main_menu(self):
        """Display main menu"""
        print_header()

        # Show quick status
        status = self.stats.get_status_summary()
        print("Current Status:")
        print(f"  Last Check: {format_time_ago(status['last_check'])} ({status['last_status']})")
        print(f"  Today: {status['today_checks']} checks, {status['today_success_rate']:.1f}% success")
        print(f"  Overall: {status['total_sessions']} sessions, {status['overall_success_rate']:.1f}% success")
        print(f"  Streak: {status['current_streak']} consecutive successes")

        # Show active profile
        active = self.profiles.get_active_profile()
        if active:
            print(f"\n  Active Profile: {active.name}")
            if active.daily_reset_time:
                print(f"  Daily Reset: {active.daily_reset_time}")

        options = [
            "Run Health Check Now",
            "Start Scheduler",
            "View Statistics",
            "Manage Profiles",
            "Notification Settings",
            "Configuration",
            "View Logs",
            "Export Data"
        ]

        print_menu(options, "Main Menu")

        choice = get_choice(len(options))

        if choice == 0:
            self.running = False
        elif choice == 1:
            self.run_health_check_now()
        elif choice == 2:
            self.start_scheduler_menu()
        elif choice == 3:
            self.view_statistics()
        elif choice == 4:
            self.manage_profiles()
        elif choice == 5:
            self.notification_settings()
        elif choice == 6:
            self.configuration_menu()
        elif choice == 7:
            self.view_logs()
        elif choice == 8:
            self.export_data()

    def run_health_check_now(self):
        """Run a single health check"""
        clear_screen()
        print_header("Running Health Check")
        print("Executing Claude Code CLI command...")
        print("This may take a few minutes...\n")

        start_time = time.time()

        if self.health_checker:
            success, response = self.health_checker.run_claude_command("Hi")
            response_time = time.time() - start_time

            # Record stats
            self.stats.record_session(
                success=success,
                response_time=response_time,
                error_message=None if success else response,
                session_type="manual",
                response_preview=response[:200] if success else None
            )

            if success:
                print(f"\n[SUCCESS] Health check passed!")
                print(f"Response time: {response_time:.2f}s")
                print(f"\nResponse preview: {response[:300]}...")
            else:
                print(f"\n[FAILED] Health check failed!")
                print(f"Error: {response}")
        else:
            print("Health checker not initialized!")

        input("\nPress Enter to continue...")

    def start_scheduler_menu(self):
        """Menu for starting the scheduler"""
        clear_screen()
        print_header("Start Scheduler")

        options = [
            "Start with Active Profile",
            "Start Fresh (Default 4:01 PM)",
            "Start with Daily Reset",
            "Resume from Last Run",
            "Custom Start Time"
        ]

        # Show available profiles
        print("Available Profiles:")
        for p in self.profiles.list_profiles():
            active_mark = " [ACTIVE]" if p['active'] else ""
            print(f"  - {p['name']}: {p['description']}{active_mark}")

        print_menu(options, "Scheduler Options")

        choice = get_choice(len(options))

        if choice == 0:
            return
        elif choice == 1:
            self.start_with_profile()
        elif choice == 2:
            self.start_fresh()
        elif choice == 3:
            self.start_with_daily_reset()
        elif choice == 4:
            self.start_resume()
        elif choice == 5:
            self.start_custom()

    def start_with_profile(self):
        """Start scheduler with active profile"""
        profile = self.profiles.get_active_profile()
        if not profile:
            print("No active profile set!")
            input("Press Enter to continue...")
            return

        print(f"\nStarting with profile: {profile.name}")
        print(f"Daily Reset: {profile.daily_reset_time or 'None'}")
        print("\nPress Ctrl+C to stop the scheduler\n")

        if self.health_checker:
            args = self.profiles.get_profile_args()
            try:
                self.health_checker.daily_reset_time = args.get('daily_reset_time')
                self.health_checker.start_scheduler(
                    first_run_timestamp=args.get('first_run_timestamp')
                )
            except KeyboardInterrupt:
                print("\nScheduler stopped.")

        input("Press Enter to continue...")

    def start_fresh(self):
        """Start scheduler fresh"""
        print("\nStarting fresh scheduler (first run at 4:01:10 PM)...")
        print("Press Ctrl+C to stop\n")

        if self.health_checker:
            try:
                self.health_checker.start_scheduler()
            except KeyboardInterrupt:
                print("\nScheduler stopped.")

        input("Press Enter to continue...")

    def start_with_daily_reset(self):
        """Start with daily reset"""
        reset_time = get_input("Enter daily reset time (HH:MM)", "08:00")

        print(f"\nStarting with daily reset at {reset_time}...")
        print("Press Ctrl+C to stop\n")

        if self.health_checker:
            try:
                self.health_checker.daily_reset_time = reset_time
                self.health_checker.start_scheduler()
            except KeyboardInterrupt:
                print("\nScheduler stopped.")

        input("Press Enter to continue...")

    def start_resume(self):
        """Resume from last run"""
        try:
            with open('last_run_timestamp.txt', 'r') as f:
                timestamp = int(f.read().strip())
            print(f"\nResuming from timestamp: {timestamp}")
            print(f"That's: {datetime.fromtimestamp(timestamp)}")
            print("Press Ctrl+C to stop\n")

            if self.health_checker:
                try:
                    self.health_checker.start_scheduler(resume_from_timestamp=timestamp)
                except KeyboardInterrupt:
                    print("\nScheduler stopped.")
        except FileNotFoundError:
            print("No previous run found. Starting fresh.")
            self.start_fresh()

        input("Press Enter to continue...")

    def start_custom(self):
        """Start with custom settings"""
        print("\nCustom Start Configuration:")
        unix_ts = get_input("Unix timestamp (or press Enter for default)", "")
        daily_reset = get_input("Daily reset time HH:MM (or press Enter for none)", "")

        timestamp = int(unix_ts) if unix_ts else None
        reset_time = daily_reset if daily_reset else None

        print(f"\nStarting scheduler...")
        print(f"Unix timestamp: {timestamp or 'Default'}")
        print(f"Daily reset: {reset_time or 'None'}")
        print("Press Ctrl+C to stop\n")

        if self.health_checker:
            try:
                self.health_checker.daily_reset_time = reset_time
                self.health_checker.start_scheduler(first_run_timestamp=timestamp)
            except KeyboardInterrupt:
                print("\nScheduler stopped.")

        input("Press Enter to continue...")

    def view_statistics(self):
        """View statistics menu"""
        while True:
            clear_screen()
            print_header("Statistics")

            overall = self.stats.get_overall_stats()
            today = self.stats.get_today_stats()

            print("=== Overall Statistics ===")
            print(f"  Total Sessions: {overall['total_sessions']}")
            print(f"  Successful: {overall['successful_sessions']}")
            print(f"  Failed: {overall['failed_sessions']}")
            print(f"  Success Rate: {overall['success_rate']:.1f}%")
            if overall['avg_response_time']:
                print(f"  Avg Response Time: {overall['avg_response_time']:.2f}s")
            print(f"  Current Streak: {overall['current_success_streak']} successes")
            print(f"  First Session: {format_time_ago(overall['first_session'])}")
            print(f"  Last Session: {format_time_ago(overall['last_session'])}")

            print("\n=== Today's Statistics ===")
            print(f"  Checks: {today['total_checks']}")
            print(f"  Successful: {today['successful']}")
            print(f"  Failed: {today['failed']}")
            print(f"  Uptime: {today['uptime_percentage']:.1f}%")

            options = [
                "View Recent Sessions",
                "View Weekly Stats",
                "View Events Log",
                "Refresh"
            ]

            print_menu(options, "Statistics Menu")

            choice = get_choice(len(options))

            if choice == 0:
                return
            elif choice == 1:
                self.view_recent_sessions()
            elif choice == 2:
                self.view_weekly_stats()
            elif choice == 3:
                self.view_events()
            elif choice == 4:
                continue

    def view_recent_sessions(self):
        """View recent session history"""
        clear_screen()
        print_header("Recent Sessions")

        sessions = self.stats.get_recent_sessions(20)

        if not sessions:
            print("No sessions recorded yet.")
        else:
            print(f"{'Time':<20} {'Status':<10} {'Type':<10} {'Response Time':<15}")
            print("-" * 55)

            for s in sessions:
                status = "SUCCESS" if s['success'] else "FAILED"
                time_str = format_time_ago(s['timestamp'])
                resp_time = f"{s['response_time']:.2f}s" if s['response_time'] else "N/A"
                print(f"{time_str:<20} {status:<10} {s['session_type']:<10} {resp_time:<15}")

        input("\nPress Enter to continue...")

    def view_weekly_stats(self):
        """View weekly statistics"""
        clear_screen()
        print_header("Weekly Statistics")

        weekly = self.stats.get_weekly_stats()

        if not weekly:
            print("No statistics recorded yet.")
        else:
            print(f"{'Date':<12} {'Total':<8} {'Success':<8} {'Failed':<8} {'Uptime':<10}")
            print("-" * 50)

            for day in weekly:
                print(f"{day['date']:<12} {day['total_checks']:<8} {day['successful']:<8} "
                      f"{day['failed']:<8} {day['uptime_percentage']:.1f}%")

        input("\nPress Enter to continue...")

    def view_events(self):
        """View system events"""
        clear_screen()
        print_header("System Events")

        events = self.stats.get_events(30)

        if not events:
            print("No events recorded yet.")
        else:
            for e in events:
                time_str = format_time_ago(e['timestamp'])
                print(f"[{time_str}] {e['event_type']}: {e['description']}")

        input("\nPress Enter to continue...")

    def manage_profiles(self):
        """Manage schedule profiles"""
        while True:
            clear_screen()
            print_header("Schedule Profiles")

            profiles = self.profiles.list_profiles()

            print("Available Profiles:")
            for p in profiles:
                active = " [ACTIVE]" if p['active'] else ""
                reset = f", reset at {p['daily_reset']}" if p['daily_reset'] else ""
                print(f"  - {p['name']}{active}: {p['description']}{reset}")

            options = [
                "Set Active Profile",
                "Create New Profile",
                "Edit Profile",
                "Delete Profile",
                "Duplicate Profile"
            ]

            print_menu(options, "Profile Management")

            choice = get_choice(len(options))

            if choice == 0:
                return
            elif choice == 1:
                self.set_active_profile()
            elif choice == 2:
                self.create_profile()
            elif choice == 3:
                self.edit_profile()
            elif choice == 4:
                self.delete_profile()
            elif choice == 5:
                self.duplicate_profile()

    def set_active_profile(self):
        """Set the active profile"""
        profiles = self.profiles.list_profiles()

        print("\nSelect profile to activate:")
        for i, p in enumerate(profiles, 1):
            active = " [ACTIVE]" if p['active'] else ""
            print(f"  [{i}] {p['name']}{active}")

        choice = get_choice(len(profiles))

        if 0 < choice <= len(profiles):
            name = profiles[choice - 1]['name']
            if self.profiles.set_active_profile(name):
                print(f"\nActivated profile: {name}")
            else:
                print("\nFailed to activate profile.")

        input("Press Enter to continue...")

    def create_profile(self):
        """Create a new profile"""
        print("\n=== Create New Profile ===")

        name = get_input("Profile name")
        if not name:
            print("Name is required!")
            input("Press Enter to continue...")
            return

        description = get_input("Description", "")
        daily_reset = get_input("Daily reset time (HH:MM or empty)", "")
        first_run = get_input("First run time (HH:MM or empty)", "")

        profile = ScheduleProfile(
            name=name,
            description=description,
            daily_reset_time=daily_reset if daily_reset else None,
            first_run_time=first_run if first_run else None
        )

        if self.profiles.create_profile(profile):
            print(f"\nProfile '{name}' created successfully!")
        else:
            print("\nFailed to create profile (name may already exist).")

        input("Press Enter to continue...")

    def edit_profile(self):
        """Edit an existing profile"""
        profiles = self.profiles.list_profiles()

        print("\nSelect profile to edit:")
        for i, p in enumerate(profiles, 1):
            print(f"  [{i}] {p['name']}")

        choice = get_choice(len(profiles))

        if 0 < choice <= len(profiles):
            name = profiles[choice - 1]['name']
            profile = self.profiles.get_profile(name)

            print(f"\n=== Editing: {name} ===")
            print("(Press Enter to keep current value)\n")

            new_desc = get_input(f"Description", profile.description)
            new_reset = get_input(f"Daily reset (HH:MM)", profile.daily_reset_time or "")
            new_first = get_input(f"First run (HH:MM)", profile.first_run_time or "")

            updates = {
                'description': new_desc,
                'daily_reset_time': new_reset if new_reset else None,
                'first_run_time': new_first if new_first else None
            }

            if self.profiles.update_profile(name, updates):
                print("\nProfile updated!")
            else:
                print("\nFailed to update profile.")

        input("Press Enter to continue...")

    def delete_profile(self):
        """Delete a profile"""
        profiles = self.profiles.list_profiles()

        print("\nSelect profile to delete:")
        for i, p in enumerate(profiles, 1):
            print(f"  [{i}] {p['name']}")

        choice = get_choice(len(profiles))

        if 0 < choice <= len(profiles):
            name = profiles[choice - 1]['name']
            confirm = get_input(f"Delete '{name}'? (yes/no)", "no")

            if confirm.lower() == "yes":
                if self.profiles.delete_profile(name):
                    print(f"\nProfile '{name}' deleted!")
                else:
                    print("\nFailed to delete profile.")
            else:
                print("\nCancelled.")

        input("Press Enter to continue...")

    def duplicate_profile(self):
        """Duplicate a profile"""
        profiles = self.profiles.list_profiles()

        print("\nSelect profile to duplicate:")
        for i, p in enumerate(profiles, 1):
            print(f"  [{i}] {p['name']}")

        choice = get_choice(len(profiles))

        if 0 < choice <= len(profiles):
            source = profiles[choice - 1]['name']
            new_name = get_input("New profile name")

            if new_name:
                if self.profiles.duplicate_profile(source, new_name):
                    print(f"\nProfile duplicated as '{new_name}'!")
                else:
                    print("\nFailed to duplicate (name may exist).")

        input("Press Enter to continue...")

    def notification_settings(self):
        """Manage notification settings"""
        while True:
            clear_screen()
            print_header("Notification Settings")

            channels = self.notifications.get_channel_status()

            print("Configured Channels:")
            for ch in channels:
                status = "ENABLED" if ch['enabled'] else "DISABLED"
                webhook = "configured" if ch['has_webhook'] else "not configured"
                print(f"  - {ch['name']} ({ch['type']}): {status}, webhook {webhook}")

            options = [
                "Enable/Disable Channel",
                "Configure Webhook URL",
                "Test Notification",
                "Configure Events"
            ]

            print_menu(options, "Notification Settings")

            choice = get_choice(len(options))

            if choice == 0:
                return
            elif choice == 1:
                self.toggle_notification_channel()
            elif choice == 2:
                self.configure_webhook()
            elif choice == 3:
                self.test_notification()
            elif choice == 4:
                self.configure_notification_events()

    def toggle_notification_channel(self):
        """Toggle a notification channel"""
        channels = self.notifications.channels

        print("\nSelect channel to toggle:")
        for i, ch in enumerate(channels, 1):
            status = "ENABLED" if ch.enabled else "DISABLED"
            print(f"  [{i}] {ch.name}: {status}")

        choice = get_choice(len(channels))

        if 0 < choice <= len(channels):
            ch = channels[choice - 1]
            ch.enabled = not ch.enabled
            self.notifications.save_config()
            status = "enabled" if ch.enabled else "disabled"
            print(f"\n{ch.name} is now {status}")

        input("Press Enter to continue...")

    def configure_webhook(self):
        """Configure webhook URL for a channel"""
        channels = self.notifications.channels

        print("\nSelect channel to configure:")
        for i, ch in enumerate(channels, 1):
            url = ch.webhook_url[:40] + "..." if ch.webhook_url and len(ch.webhook_url) > 40 else ch.webhook_url
            print(f"  [{i}] {ch.name}: {url or 'Not set'}")

        choice = get_choice(len(channels))

        if 0 < choice <= len(channels):
            ch = channels[choice - 1]
            new_url = get_input(f"Webhook URL for {ch.name}", ch.webhook_url or "")
            ch.webhook_url = new_url
            self.notifications.save_config()
            print("\nWebhook URL updated!")

        input("Press Enter to continue...")

    def test_notification(self):
        """Test a notification channel"""
        channels = self.notifications.channels

        print("\nSelect channel to test:")
        for i, ch in enumerate(channels, 1):
            print(f"  [{i}] {ch.name}")

        choice = get_choice(len(channels))

        if 0 < choice <= len(channels):
            ch = channels[choice - 1]
            print(f"\nSending test notification to {ch.name}...")

            if self.notifications.test_channel(ch.name):
                print("Test notification sent successfully!")
            else:
                print("Failed to send test notification.")

        input("Press Enter to continue...")

    def configure_notification_events(self):
        """Configure which events trigger notifications"""
        channels = self.notifications.channels

        print("\nSelect channel to configure events:")
        for i, ch in enumerate(channels, 1):
            print(f"  [{i}] {ch.name}")

        choice = get_choice(len(channels))

        if 0 < choice <= len(channels):
            ch = channels[choice - 1]

            print(f"\n=== Event Configuration for {ch.name} ===")
            print("(Enter 'y' or 'n')\n")

            success = get_input(f"Notify on success? (currently: {ch.notify_on_success})", "n")
            failure = get_input(f"Notify on failure? (currently: {ch.notify_on_failure})", "y")
            reset = get_input(f"Notify on daily reset? (currently: {ch.notify_on_daily_reset})", "y")

            ch.notify_on_success = success.lower() == 'y'
            ch.notify_on_failure = failure.lower() == 'y'
            ch.notify_on_daily_reset = reset.lower() == 'y'

            self.notifications.save_config()
            print("\nEvent configuration updated!")

        input("Press Enter to continue...")

    def configuration_menu(self):
        """General configuration menu"""
        clear_screen()
        print_header("Configuration")

        print("Current Configuration:")

        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                print(f"  Webhook URL: {config.get('webhook_url', 'Not set')[:50]}...")
        except:
            print("  No config.json found")

        print()

        options = [
            "Edit config.json",
            "Reset to Defaults",
            "View All Settings"
        ]

        print_menu(options, "Configuration")

        choice = get_choice(len(options))

        if choice == 1:
            print("\nEdit config.json manually in your text editor.")
        elif choice == 2:
            confirm = get_input("Reset all settings to defaults? (yes/no)", "no")
            if confirm.lower() == "yes":
                print("Settings reset!")
        elif choice == 3:
            print("\nAll settings shown above.")

        input("Press Enter to continue...")

    def view_logs(self):
        """View recent log entries"""
        clear_screen()
        print_header("Recent Logs")

        try:
            with open('claude_health_check.log', 'r') as f:
                lines = f.readlines()
                # Show last 30 lines
                for line in lines[-30:]:
                    print(line.rstrip())
        except FileNotFoundError:
            print("No log file found yet.")

        input("\nPress Enter to continue...")

    def export_data(self):
        """Export statistics data"""
        clear_screen()
        print_header("Export Data")

        options = [
            "Export Statistics (JSON)",
            "Export Profiles",
            "Export All Data"
        ]

        print_menu(options, "Export Options")

        choice = get_choice(len(options))

        if choice == 1:
            filepath = self.stats.export_stats()
            print(f"\nStatistics exported to: {filepath}")
        elif choice == 2:
            filepath = "profiles_export.json"
            import json
            data = {name: asdict(p) for name, p in self.profiles.profiles.items()}
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nProfiles exported to: {filepath}")
        elif choice == 3:
            self.stats.export_stats("stats_export.json")
            print("\nAll data exported!")

        input("Press Enter to continue...")


def run_interactive_mode(health_checker=None):
    """Entry point for interactive mode"""
    cli = InteractiveCLI(health_checker)
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\nExiting...")


if __name__ == "__main__":
    # Allow running standalone for testing
    run_interactive_mode()
