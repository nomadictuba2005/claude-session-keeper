#!/usr/bin/env python3
"""
Flask Web Dashboard and REST API
Provides a web interface and API for Claude Session Keeper
"""
import os
import json
import threading
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, request, render_template_string, redirect, url_for

from session_stats import SessionStats
from notifications import NotificationManager, NotificationLevel
from profiles import ProfileManager

app = Flask(__name__)

# Global instances
stats = SessionStats()
notifications = NotificationManager()
profiles = ProfileManager()
health_checker = None
scheduler_status = {
    "running": False,
    "started_at": None,
    "next_check": None,
    "profile": None
}

# HTML Templates embedded in Python
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Session Keeper</title>
    <style>
        :root {
            --bg-dark: #1a1a2e;
            --bg-card: #16213e;
            --accent: #e94560;
            --accent-green: #4ecca3;
            --accent-yellow: #ffc107;
            --text: #eee;
            --text-muted: #888;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #333;
        }
        h1 { font-size: 1.8em; }
        h1 span { color: var(--accent); }
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.9em;
        }
        .status-running { background: var(--accent-green); color: #000; }
        .status-stopped { background: var(--accent); color: #fff; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .card h3 {
            color: var(--text-muted);
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: var(--accent-green);
        }
        .card .value.warning { color: var(--accent-yellow); }
        .card .value.danger { color: var(--accent); }
        .card .subtitle {
            color: var(--text-muted);
            font-size: 0.85em;
            margin-top: 5px;
        }
        .section {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .section h2 {
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }
        th { color: var(--text-muted); font-weight: normal; }
        .success { color: var(--accent-green); }
        .failed { color: var(--accent); }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.95em;
            margin-right: 10px;
            margin-bottom: 10px;
            text-decoration: none;
        }
        .btn-primary { background: var(--accent); color: #fff; }
        .btn-secondary { background: #333; color: #fff; }
        .btn-success { background: var(--accent-green); color: #000; }
        .btn:hover { opacity: 0.9; }
        .controls { margin-bottom: 20px; }
        .profile-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .profile-item {
            background: #333;
            padding: 10px 15px;
            border-radius: 8px;
            cursor: pointer;
        }
        .profile-item.active {
            background: var(--accent-green);
            color: #000;
        }
        .countdown {
            font-family: monospace;
            font-size: 1.5em;
            color: var(--accent-green);
        }
        .refresh-notice {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85em;
            margin-top: 20px;
        }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
            header { flex-direction: column; gap: 15px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Claude <span>Session Keeper</span></h1>
            <div class="status-badge {{ 'status-running' if scheduler_running else 'status-stopped' }}">
                {{ 'Scheduler Running' if scheduler_running else 'Scheduler Stopped' }}
            </div>
        </header>

        <div class="grid">
            <div class="card">
                <h3>Today's Checks</h3>
                <div class="value">{{ today.total_checks }}</div>
                <div class="subtitle">{{ today.successful }} successful, {{ today.failed }} failed</div>
            </div>
            <div class="card">
                <h3>Uptime Today</h3>
                <div class="value {{ 'danger' if today.uptime_percentage < 80 else 'warning' if today.uptime_percentage < 95 else '' }}">
                    {{ "%.1f"|format(today.uptime_percentage) }}%
                </div>
                <div class="subtitle">Based on {{ today.total_checks }} checks</div>
            </div>
            <div class="card">
                <h3>Success Streak</h3>
                <div class="value">{{ overall.current_success_streak }}</div>
                <div class="subtitle">Consecutive successful checks</div>
            </div>
            <div class="card">
                <h3>Total Sessions</h3>
                <div class="value">{{ overall.total_sessions }}</div>
                <div class="subtitle">{{ "%.1f"|format(overall.success_rate) }}% lifetime success rate</div>
            </div>
        </div>

        <div class="section">
            <h2>Quick Actions</h2>
            <div class="controls">
                <a href="/api/check" class="btn btn-primary" onclick="return confirm('Run health check now?')">Run Check Now</a>
                {% if not scheduler_running %}
                <a href="/api/scheduler/start" class="btn btn-success">Start Scheduler</a>
                {% else %}
                <a href="/api/scheduler/stop" class="btn btn-secondary">Stop Scheduler</a>
                {% endif %}
                <a href="/profiles" class="btn btn-secondary">Manage Profiles</a>
                <a href="/api/stats/export" class="btn btn-secondary">Export Stats</a>
            </div>
        </div>

        <div class="section">
            <h2>Active Profile</h2>
            {% if active_profile %}
            <p><strong>{{ active_profile.name }}</strong>: {{ active_profile.description }}</p>
            <p>Daily Reset: {{ active_profile.daily_reset_time or 'None' }}</p>
            {% else %}
            <p>No active profile set. <a href="/profiles">Set one now</a></p>
            {% endif %}
        </div>

        <div class="section">
            <h2>Recent Sessions</h2>
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Status</th>
                        <th>Type</th>
                        <th>Response Time</th>
                    </tr>
                </thead>
                <tbody>
                    {% for session in recent_sessions %}
                    <tr>
                        <td>{{ session.timestamp[:19] }}</td>
                        <td class="{{ 'success' if session.success else 'failed' }}">
                            {{ 'SUCCESS' if session.success else 'FAILED' }}
                        </td>
                        <td>{{ session.session_type }}</td>
                        <td>{{ "%.2fs"|format(session.response_time) if session.response_time else 'N/A' }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="4" style="text-align: center; color: var(--text-muted);">
                            No sessions recorded yet
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="refresh-notice">
            Auto-refreshes every 30 seconds | <a href="/" style="color: var(--accent);">Refresh now</a>
        </div>
    </div>

    <script>
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
'''

PROFILES_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Profiles - Claude Session Keeper</title>
    <style>
        :root {
            --bg-dark: #1a1a2e;
            --bg-card: #16213e;
            --accent: #e94560;
            --accent-green: #4ecca3;
            --text: #eee;
            --text-muted: #888;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        header {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #333;
        }
        h1 { font-size: 1.5em; margin-bottom: 10px; }
        .back-link { color: var(--accent); text-decoration: none; }
        .profile-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .profile-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            border: 2px solid transparent;
        }
        .profile-card.active { border-color: var(--accent-green); }
        .profile-card h3 { margin-bottom: 10px; }
        .profile-card p { color: var(--text-muted); font-size: 0.9em; margin-bottom: 10px; }
        .profile-card .meta { font-size: 0.85em; color: var(--text-muted); }
        .profile-card .actions { margin-top: 15px; }
        .btn {
            display: inline-block;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85em;
            text-decoration: none;
            margin-right: 5px;
        }
        .btn-primary { background: var(--accent); color: #fff; }
        .btn-secondary { background: #333; color: #fff; }
        .btn-success { background: var(--accent-green); color: #000; }
        .btn:hover { opacity: 0.9; }
        .form-section {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 25px;
        }
        .form-section h2 { margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: var(--text-muted);
        }
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid #333;
            border-radius: 6px;
            background: #1a1a2e;
            color: var(--text);
        }
        .active-badge {
            display: inline-block;
            background: var(--accent-green);
            color: #000;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <a href="/" class="back-link">&larr; Back to Dashboard</a>
            <h1>Schedule Profiles</h1>
        </header>

        <div class="profile-grid">
            {% for profile in profiles %}
            <div class="profile-card {{ 'active' if profile.active else '' }}">
                <h3>
                    {{ profile.name }}
                    {% if profile.active %}<span class="active-badge">ACTIVE</span>{% endif %}
                </h3>
                <p>{{ profile.description }}</p>
                <div class="meta">
                    <div>Daily Reset: {{ profile.daily_reset or 'None' }}</div>
                    <div>First Run: {{ profile.first_run or 'Default' }}</div>
                </div>
                <div class="actions">
                    {% if not profile.active %}
                    <a href="/api/profiles/{{ profile.name }}/activate" class="btn btn-success">Activate</a>
                    {% endif %}
                    <a href="/api/profiles/{{ profile.name }}/delete" class="btn btn-secondary"
                       onclick="return confirm('Delete this profile?')">Delete</a>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="form-section">
            <h2>Create New Profile</h2>
            <form action="/api/profiles/create" method="POST">
                <div class="form-group">
                    <label>Profile Name</label>
                    <input type="text" name="name" required placeholder="e.g., my-schedule">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <input type="text" name="description" placeholder="Describe this schedule">
                </div>
                <div class="form-group">
                    <label>Daily Reset Time (HH:MM)</label>
                    <input type="text" name="daily_reset" placeholder="e.g., 08:00 (leave empty for none)">
                </div>
                <div class="form-group">
                    <label>First Run Time (HH:MM)</label>
                    <input type="text" name="first_run" placeholder="e.g., 08:00 (leave empty for default)">
                </div>
                <button type="submit" class="btn btn-primary">Create Profile</button>
            </form>
        </div>
    </div>
</body>
</html>
'''


# Routes - Dashboard
@app.route('/')
def dashboard():
    """Main dashboard"""
    today = stats.get_today_stats()
    overall = stats.get_overall_stats()
    recent = stats.get_recent_sessions(10)
    active = profiles.get_active_profile()

    return render_template_string(
        DASHBOARD_HTML,
        today=today,
        overall=overall,
        recent_sessions=recent,
        active_profile=active,
        scheduler_running=scheduler_status['running']
    )


@app.route('/profiles')
def profiles_page():
    """Profiles management page"""
    profile_list = profiles.list_profiles()
    return render_template_string(PROFILES_HTML, profiles=profile_list)


# API Routes - Health Check
@app.route('/api/check', methods=['GET', 'POST'])
def run_check():
    """Run a health check now"""
    global health_checker

    if health_checker:
        import time
        start = time.time()
        success, response = health_checker.run_claude_command("Hi")
        response_time = time.time() - start

        stats.record_session(
            success=success,
            response_time=response_time,
            error_message=None if success else response,
            session_type="manual"
        )

        return jsonify({
            "success": success,
            "response_time": response_time,
            "message": "Check completed"
        })

    return jsonify({"error": "Health checker not initialized"}), 500


@app.route('/api/status')
def get_status():
    """Get current status"""
    summary = stats.get_status_summary()
    active = profiles.get_active_profile()

    return jsonify({
        "status": summary,
        "scheduler": scheduler_status,
        "active_profile": active.name if active else None
    })


# API Routes - Statistics
@app.route('/api/stats')
def get_stats():
    """Get all statistics"""
    return jsonify({
        "today": stats.get_today_stats(),
        "overall": stats.get_overall_stats(),
        "weekly": stats.get_weekly_stats()
    })


@app.route('/api/stats/today')
def get_today_stats():
    """Get today's statistics"""
    return jsonify(stats.get_today_stats())


@app.route('/api/stats/overall')
def get_overall_stats():
    """Get overall statistics"""
    return jsonify(stats.get_overall_stats())


@app.route('/api/stats/weekly')
def get_weekly_stats():
    """Get weekly statistics"""
    return jsonify(stats.get_weekly_stats())


@app.route('/api/stats/export')
def export_stats():
    """Export statistics to JSON file"""
    filepath = stats.export_stats()
    return jsonify({"message": "Stats exported", "filepath": filepath})


@app.route('/api/sessions')
def get_sessions():
    """Get recent sessions"""
    limit = request.args.get('limit', 20, type=int)
    return jsonify(stats.get_recent_sessions(limit))


@app.route('/api/events')
def get_events():
    """Get system events"""
    limit = request.args.get('limit', 50, type=int)
    event_type = request.args.get('type')
    return jsonify(stats.get_events(limit, event_type))


# API Routes - Profiles
@app.route('/api/profiles')
def list_profiles():
    """List all profiles"""
    return jsonify(profiles.list_profiles())


@app.route('/api/profiles/<name>')
def get_profile(name):
    """Get a specific profile"""
    profile = profiles.get_profile(name)
    if profile:
        from dataclasses import asdict
        return jsonify(asdict(profile))
    return jsonify({"error": "Profile not found"}), 404


@app.route('/api/profiles/<name>/activate')
def activate_profile(name):
    """Activate a profile"""
    if profiles.set_active_profile(name):
        return redirect(url_for('profiles_page'))
    return jsonify({"error": "Profile not found"}), 404


@app.route('/api/profiles/<name>/delete')
def delete_profile(name):
    """Delete a profile"""
    if profiles.delete_profile(name):
        return redirect(url_for('profiles_page'))
    return jsonify({"error": "Profile not found or cannot be deleted"}), 404


@app.route('/api/profiles/create', methods=['POST'])
def create_profile():
    """Create a new profile"""
    from profiles import ScheduleProfile

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    name = data.get('name')
    if not name:
        return jsonify({"error": "Name is required"}), 400

    profile = ScheduleProfile(
        name=name,
        description=data.get('description', ''),
        daily_reset_time=data.get('daily_reset') or None,
        first_run_time=data.get('first_run') or None
    )

    if profiles.create_profile(profile):
        if request.is_json:
            return jsonify({"message": "Profile created", "name": name})
        return redirect(url_for('profiles_page'))

    return jsonify({"error": "Profile already exists"}), 400


@app.route('/api/profiles/active')
def get_active_profile():
    """Get the active profile"""
    active = profiles.get_active_profile()
    if active:
        from dataclasses import asdict
        return jsonify(asdict(active))
    return jsonify({"error": "No active profile"}), 404


# API Routes - Scheduler Control
@app.route('/api/scheduler/status')
def scheduler_get_status():
    """Get scheduler status"""
    return jsonify(scheduler_status)


@app.route('/api/scheduler/start', methods=['GET', 'POST'])
def scheduler_start():
    """Start the scheduler"""
    global scheduler_status

    if scheduler_status['running']:
        return jsonify({"error": "Scheduler already running"}), 400

    scheduler_status['running'] = True
    scheduler_status['started_at'] = datetime.now().isoformat()

    active = profiles.get_active_profile()
    if active:
        scheduler_status['profile'] = active.name

    # In a real implementation, this would start the scheduler thread
    # For now, we just update the status

    if request.is_json:
        return jsonify({"message": "Scheduler started", "status": scheduler_status})
    return redirect(url_for('dashboard'))


@app.route('/api/scheduler/stop', methods=['GET', 'POST'])
def scheduler_stop():
    """Stop the scheduler"""
    global scheduler_status

    scheduler_status['running'] = False
    scheduler_status['started_at'] = None
    scheduler_status['profile'] = None

    if request.is_json:
        return jsonify({"message": "Scheduler stopped"})
    return redirect(url_for('dashboard'))


# API Routes - Notifications
@app.route('/api/notifications/channels')
def notification_channels():
    """Get notification channel status"""
    return jsonify(notifications.get_channel_status())


@app.route('/api/notifications/test/<channel_name>', methods=['POST'])
def test_notification(channel_name):
    """Test a notification channel"""
    success = notifications.test_channel(channel_name)
    return jsonify({
        "channel": channel_name,
        "success": success
    })


# API Routes - System
@app.route('/api/health')
def health():
    """Simple health endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })


def set_health_checker(checker):
    """Set the health checker instance"""
    global health_checker
    health_checker = checker


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask server"""
    print(f"Starting web dashboard at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


def run_server_background(host='0.0.0.0', port=5000):
    """Run the Flask server in a background thread"""
    thread = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False),
        daemon=True
    )
    thread.start()
    print(f"Web dashboard started at http://{host}:{port}")
    return thread


if __name__ == '__main__':
    run_server(debug=True)
