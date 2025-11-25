#!/usr/bin/env python3
"""
Multi-Channel Notification System
Supports Discord, Slack, generic webhooks, and desktop notifications
"""
import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

@dataclass
class NotificationConfig:
    """Configuration for a notification channel"""
    enabled: bool = True
    webhook_url: str = None
    channel_type: str = "generic"  # discord, slack, generic, desktop
    name: str = "Default"
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notify_on_daily_reset: bool = True


class NotificationManager:
    """Manage multiple notification channels"""

    def __init__(self, config_file: str = "notifications_config.json"):
        self.config_file = config_file
        self.channels: List[NotificationConfig] = []
        self.load_config()

    def load_config(self):
        """Load notification configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.channels = [
                    NotificationConfig(**ch) for ch in data.get('channels', [])
                ]
        except FileNotFoundError:
            # Create default config
            self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading notification config: {e}")
            self.channels = []

    def _create_default_config(self):
        """Create default notification configuration"""
        default_config = {
            "channels": [
                {
                    "name": "Webhook",
                    "channel_type": "generic",
                    "webhook_url": "",
                    "enabled": False,
                    "notify_on_success": False,
                    "notify_on_failure": True,
                    "notify_on_daily_reset": True
                },
                {
                    "name": "Discord",
                    "channel_type": "discord",
                    "webhook_url": "",
                    "enabled": False,
                    "notify_on_success": False,
                    "notify_on_failure": True,
                    "notify_on_daily_reset": False
                },
                {
                    "name": "Slack",
                    "channel_type": "slack",
                    "webhook_url": "",
                    "enabled": False,
                    "notify_on_success": False,
                    "notify_on_failure": True,
                    "notify_on_daily_reset": False
                }
            ]
        }

        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        logger.info(f"Created default notification config: {self.config_file}")
        self.channels = [NotificationConfig(**ch) for ch in default_config['channels']]

    def save_config(self):
        """Save current configuration to file"""
        data = {
            "channels": [
                {
                    "name": ch.name,
                    "channel_type": ch.channel_type,
                    "webhook_url": ch.webhook_url,
                    "enabled": ch.enabled,
                    "notify_on_success": ch.notify_on_success,
                    "notify_on_failure": ch.notify_on_failure,
                    "notify_on_daily_reset": ch.notify_on_daily_reset
                }
                for ch in self.channels
            ]
        }

        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_channel(self, config: NotificationConfig):
        """Add a new notification channel"""
        self.channels.append(config)
        self.save_config()

    def remove_channel(self, name: str):
        """Remove a notification channel by name"""
        self.channels = [ch for ch in self.channels if ch.name != name]
        self.save_config()

    def send_discord(self, webhook_url: str, title: str, message: str, level: NotificationLevel):
        """Send Discord webhook notification"""
        colors = {
            NotificationLevel.INFO: 3447003,     # Blue
            NotificationLevel.SUCCESS: 3066993,  # Green
            NotificationLevel.WARNING: 15105570, # Orange
            NotificationLevel.ERROR: 15158332    # Red
        }

        emoji = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.SUCCESS: "✅",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌"
        }

        payload = {
            "embeds": [{
                "title": f"{emoji[level]} {title}",
                "description": message,
                "color": colors[level],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Claude Session Keeper"
                }
            }]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
            return False

    def send_slack(self, webhook_url: str, title: str, message: str, level: NotificationLevel):
        """Send Slack webhook notification"""
        colors = {
            NotificationLevel.INFO: "#3498db",
            NotificationLevel.SUCCESS: "#2ecc71",
            NotificationLevel.WARNING: "#f39c12",
            NotificationLevel.ERROR: "#e74c3c"
        }

        emoji = {
            NotificationLevel.INFO: ":information_source:",
            NotificationLevel.SUCCESS: ":white_check_mark:",
            NotificationLevel.WARNING: ":warning:",
            NotificationLevel.ERROR: ":x:"
        }

        payload = {
            "attachments": [{
                "color": colors[level],
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji[level]} {title}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    },
                    {
                        "type": "context",
                        "elements": [{
                            "type": "mrkdwn",
                            "text": f"Claude Session Keeper | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }]
                    }
                ]
            }]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False

    def send_generic_webhook(self, webhook_url: str, title: str, message: str, level: NotificationLevel):
        """Send generic webhook notification"""
        payload = {
            "title": title,
            "message": message,
            "level": level.value,
            "timestamp": datetime.now().isoformat(),
            "source": "Claude Session Keeper"
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False

    def send_desktop_notification(self, title: str, message: str, level: NotificationLevel):
        """Send desktop notification (Linux/Mac/Windows)"""
        try:
            import platform
            system = platform.system()

            if system == "Linux":
                import subprocess
                subprocess.run([
                    "notify-send",
                    "-a", "Claude Session Keeper",
                    title,
                    message
                ], timeout=5)
                return True
            elif system == "Darwin":  # macOS
                import subprocess
                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(["osascript", "-e", script], timeout=5)
                return True
            elif system == "Windows":
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=5)
                    return True
                except ImportError:
                    logger.warning("win10toast not installed for Windows notifications")
                    return False
        except Exception as e:
            logger.error(f"Desktop notification failed: {e}")
            return False

    def notify(self, title: str, message: str, level: NotificationLevel = NotificationLevel.INFO,
               event_type: str = "general"):
        """Send notification to all enabled channels"""
        results = {}

        for channel in self.channels:
            if not channel.enabled or not channel.webhook_url:
                continue

            # Check if this event type should be notified
            if event_type == "success" and not channel.notify_on_success:
                continue
            if event_type == "failure" and not channel.notify_on_failure:
                continue
            if event_type == "daily_reset" and not channel.notify_on_daily_reset:
                continue

            success = False

            if channel.channel_type == "discord":
                success = self.send_discord(channel.webhook_url, title, message, level)
            elif channel.channel_type == "slack":
                success = self.send_slack(channel.webhook_url, title, message, level)
            elif channel.channel_type == "desktop":
                success = self.send_desktop_notification(title, message, level)
            else:  # generic
                success = self.send_generic_webhook(channel.webhook_url, title, message, level)

            results[channel.name] = success
            if success:
                logger.info(f"Notification sent via {channel.name}")
            else:
                logger.error(f"Failed to send notification via {channel.name}")

        return results

    def notify_health_check_result(self, success: bool, response_time: float = None,
                                   error: str = None, consecutive_failures: int = 0):
        """Send notification for health check result"""
        if success:
            title = "Health Check Passed"
            message = f"Claude Code health check completed successfully."
            if response_time:
                message += f"\nResponse time: {response_time:.2f}s"
            level = NotificationLevel.SUCCESS
            event_type = "success"
        else:
            title = f"Health Check Failed ({consecutive_failures}x)"
            message = f"Claude Code health check failed."
            if error:
                message += f"\nError: {error}"
            if consecutive_failures >= 3:
                message += f"\n\n⚠️ {consecutive_failures} consecutive failures!"
            level = NotificationLevel.ERROR
            event_type = "failure"

        return self.notify(title, message, level, event_type)

    def notify_daily_reset(self, next_check_time: str):
        """Send notification for daily reset"""
        title = "Daily Session Reset"
        message = f"Claude Code session has been reset for the day.\nNext check: {next_check_time}"
        return self.notify(title, message, NotificationLevel.INFO, "daily_reset")

    def notify_scheduler_started(self, schedule_info: str):
        """Send notification when scheduler starts"""
        title = "Scheduler Started"
        message = f"Claude Session Keeper is now running.\n{schedule_info}"
        return self.notify(title, message, NotificationLevel.INFO, "general")

    def test_channel(self, channel_name: str) -> bool:
        """Test a specific notification channel"""
        for channel in self.channels:
            if channel.name == channel_name and channel.webhook_url:
                title = "Test Notification"
                message = "This is a test notification from Claude Session Keeper."

                if channel.channel_type == "discord":
                    return self.send_discord(channel.webhook_url, title, message, NotificationLevel.INFO)
                elif channel.channel_type == "slack":
                    return self.send_slack(channel.webhook_url, title, message, NotificationLevel.INFO)
                elif channel.channel_type == "desktop":
                    return self.send_desktop_notification(title, message, NotificationLevel.INFO)
                else:
                    return self.send_generic_webhook(channel.webhook_url, title, message, NotificationLevel.INFO)

        return False

    def get_channel_status(self) -> List[Dict]:
        """Get status of all channels"""
        return [
            {
                "name": ch.name,
                "type": ch.channel_type,
                "enabled": ch.enabled,
                "has_webhook": bool(ch.webhook_url),
                "notify_success": ch.notify_on_success,
                "notify_failure": ch.notify_on_failure,
                "notify_reset": ch.notify_on_daily_reset
            }
            for ch in self.channels
        ]
