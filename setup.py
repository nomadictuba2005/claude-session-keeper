#!/usr/bin/env python3
"""
Claude Session Keeper - Setup Script
Install with: pip install .
"""
from setuptools import setup, find_packages
import os

# Read README for long description
def read_file(filename):
    try:
        with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""

setup(
    name="claude-session-keeper",
    version="2.0.0",
    author="Claude Session Keeper Contributors",
    description="Advanced health check and session management for Claude Code CLI",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/nomadictuba2005/claude-session-keeper",
    py_modules=[
        "claude_health_check_cli",
        "session_stats",
        "notifications",
        "profiles",
        "interactive_cli",
        "web_dashboard",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "pytz>=2021.1",
    ],
    extras_require={
        "web": ["flask>=2.0.0"],
        "full": ["flask>=2.0.0"],
    },
    entry_points={
        "console_scripts": [
            "claude-session-keeper=claude_health_check_cli:main",
            "csk=claude_health_check_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
    ],
    keywords="claude, anthropic, session, health-check, monitoring, cli",
    project_urls={
        "Bug Reports": "https://github.com/nomadictuba2005/claude-session-keeper/issues",
        "Source": "https://github.com/nomadictuba2005/claude-session-keeper",
    },
)
