#!/usr/bin/env python3
"""
Schedule Profile Management
Save, load, and manage different schedule configurations
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class ScheduleProfile:
    """A schedule profile configuration"""
    name: str
    description: str = ""
    daily_reset_time: Optional[str] = None  # HH:MM format
    first_run_time: Optional[str] = None  # HH:MM format for first check
    unix_timestamp: Optional[int] = None
    interval_hours: int = 5
    webhook_url: Optional[str] = None
    notifications_enabled: bool = True
    created_at: str = None
    last_used: str = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class ProfileManager:
    """Manage schedule profiles"""

    def __init__(self, profiles_file: str = "profiles.json"):
        self.profiles_file = profiles_file
        self.profiles: Dict[str, ScheduleProfile] = {}
        self.active_profile: Optional[str] = None
        self.load_profiles()

    def load_profiles(self):
        """Load profiles from file"""
        try:
            with open(self.profiles_file, 'r') as f:
                data = json.load(f)
                self.active_profile = data.get('active_profile')
                for name, profile_data in data.get('profiles', {}).items():
                    self.profiles[name] = ScheduleProfile(**profile_data)
        except FileNotFoundError:
            self._create_default_profiles()
        except Exception as e:
            print(f"Error loading profiles: {e}")
            self._create_default_profiles()

    def _create_default_profiles(self):
        """Create default profiles"""
        defaults = {
            "morning": ScheduleProfile(
                name="morning",
                description="Start fresh each morning at 8 AM",
                daily_reset_time="08:00",
                first_run_time="08:00"
            ),
            "afternoon": ScheduleProfile(
                name="afternoon",
                description="Default afternoon schedule (4:01 PM)",
                first_run_time="16:01"
            ),
            "evening": ScheduleProfile(
                name="evening",
                description="Evening schedule starting at 6 PM",
                daily_reset_time="18:00",
                first_run_time="18:00"
            ),
            "night-owl": ScheduleProfile(
                name="night-owl",
                description="Late night schedule for night workers",
                daily_reset_time="22:00",
                first_run_time="22:00"
            ),
            "always-on": ScheduleProfile(
                name="always-on",
                description="No daily reset, continuous 5-hour cycles",
                daily_reset_time=None
            )
        }

        self.profiles = defaults
        self.active_profile = "morning"
        self.save_profiles()

    def save_profiles(self):
        """Save profiles to file"""
        data = {
            'active_profile': self.active_profile,
            'profiles': {name: asdict(profile) for name, profile in self.profiles.items()}
        }

        with open(self.profiles_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_profile(self, profile: ScheduleProfile) -> bool:
        """Create a new profile"""
        if profile.name in self.profiles:
            return False

        self.profiles[profile.name] = profile
        self.save_profiles()
        return True

    def update_profile(self, name: str, updates: Dict) -> bool:
        """Update an existing profile"""
        if name not in self.profiles:
            return False

        profile = self.profiles[name]
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        self.save_profiles()
        return True

    def delete_profile(self, name: str) -> bool:
        """Delete a profile"""
        if name not in self.profiles:
            return False

        if self.active_profile == name:
            self.active_profile = None

        del self.profiles[name]
        self.save_profiles()
        return True

    def get_profile(self, name: str) -> Optional[ScheduleProfile]:
        """Get a profile by name"""
        return self.profiles.get(name)

    def list_profiles(self) -> List[Dict]:
        """List all profiles"""
        return [
            {
                "name": p.name,
                "description": p.description,
                "daily_reset": p.daily_reset_time,
                "first_run": p.first_run_time,
                "interval": p.interval_hours,
                "active": p.name == self.active_profile,
                "last_used": p.last_used
            }
            for p in self.profiles.values()
        ]

    def set_active_profile(self, name: str) -> bool:
        """Set the active profile"""
        if name not in self.profiles:
            return False

        self.active_profile = name
        self.profiles[name].last_used = datetime.now().isoformat()
        self.save_profiles()
        return True

    def get_active_profile(self) -> Optional[ScheduleProfile]:
        """Get the currently active profile"""
        if self.active_profile:
            return self.profiles.get(self.active_profile)
        return None

    def export_profile(self, name: str, filepath: str) -> bool:
        """Export a profile to a file"""
        if name not in self.profiles:
            return False

        with open(filepath, 'w') as f:
            json.dump(asdict(self.profiles[name]), f, indent=2)
        return True

    def import_profile(self, filepath: str) -> bool:
        """Import a profile from a file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                profile = ScheduleProfile(**data)
                return self.create_profile(profile)
        except Exception as e:
            print(f"Error importing profile: {e}")
            return False

    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        """Duplicate an existing profile"""
        if source_name not in self.profiles or new_name in self.profiles:
            return False

        source = self.profiles[source_name]
        new_profile = ScheduleProfile(
            name=new_name,
            description=f"Copy of {source_name}",
            daily_reset_time=source.daily_reset_time,
            first_run_time=source.first_run_time,
            unix_timestamp=source.unix_timestamp,
            interval_hours=source.interval_hours,
            webhook_url=source.webhook_url,
            notifications_enabled=source.notifications_enabled
        )

        return self.create_profile(new_profile)

    def get_profile_args(self, name: str = None) -> Dict:
        """Get command-line arguments for a profile"""
        profile = self.profiles.get(name or self.active_profile)
        if not profile:
            return {}

        args = {}
        if profile.daily_reset_time:
            args['daily_reset_time'] = profile.daily_reset_time
        if profile.unix_timestamp:
            args['first_run_timestamp'] = profile.unix_timestamp

        return args
