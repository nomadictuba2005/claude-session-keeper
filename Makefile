# Claude Session Keeper - Makefile
# Common operations for development and usage

.PHONY: help install install-dev uninstall run web interactive check stats clean

# Default target
help:
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║        Claude Session Keeper - Commands                   ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Installation:"
	@echo "  make install       - Install Claude Session Keeper"
	@echo "  make install-dev   - Install in development mode"
	@echo "  make uninstall     - Uninstall"
	@echo ""
	@echo "Usage:"
	@echo "  make run           - Start the scheduler"
	@echo "  make web           - Start web dashboard"
	@echo "  make interactive   - Launch interactive menu"
	@echo "  make check         - Run single health check"
	@echo "  make stats         - Show statistics"
	@echo ""
	@echo "Development:"
	@echo "  make clean         - Remove generated files"
	@echo "  make test          - Run tests"
	@echo ""

# Installation
install:
	@echo "Installing Claude Session Keeper..."
	pip install --user .
	@echo "Done! Run 'claude-session-keeper --help' or 'csk --help'"

install-dev:
	@echo "Installing in development mode..."
	pip install --user -e ".[full]"
	@echo "Done!"

install-full:
	@echo "Installing with all dependencies..."
	pip install --user ".[full]"
	@echo "Done!"

uninstall:
	@echo "Uninstalling Claude Session Keeper..."
	pip uninstall -y claude-session-keeper
	@echo "Done!"

# Quick install without pip (for systems with restrictions)
install-local:
	@echo "Installing locally..."
	./install.sh
	@echo "Done!"

# Usage commands
run:
	python3 claude_health_check_cli.py

web:
	python3 claude_health_check_cli.py --web

interactive:
	python3 claude_health_check_cli.py --interactive

check:
	python3 claude_health_check_cli.py --once

stats:
	python3 claude_health_check_cli.py --stats

profiles:
	python3 claude_health_check_cli.py --list-profiles

# Run with specific profile
morning:
	python3 claude_health_check_cli.py --profile morning

afternoon:
	python3 claude_health_check_cli.py --profile afternoon

evening:
	python3 claude_health_check_cli.py --profile evening

# Development
clean:
	@echo "Cleaning generated files..."
	rm -f *.pyc
	rm -rf __pycache__
	rm -f session_history.db
	rm -f *.log
	rm -f config.json
	rm -f profiles.json
	rm -f notifications_config.json
	rm -f last_run_timestamp.txt
	rm -rf *.egg-info
	rm -rf dist build
	@echo "Done!"

clean-db:
	rm -f session_history.db

clean-logs:
	rm -f *.log

test:
	@echo "Running module import tests..."
	python3 -c "from session_stats import SessionStats; print('session_stats: OK')"
	python3 -c "from profiles import ProfileManager; print('profiles: OK')"
	python3 -c "from notifications import NotificationManager; print('notifications: OK')"
	python3 -c "from interactive_cli import InteractiveCLI; print('interactive_cli: OK')"
	@echo "All imports successful!"

# Dependencies
deps:
	pip install --user requests pytz flask

deps-min:
	pip install --user requests pytz
