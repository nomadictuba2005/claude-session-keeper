#!/bin/bash
#
# Claude Session Keeper - One-Line Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/nomadictuba2005/claude-session-keeper/main/install.sh | bash
#
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        Claude Session Keeper - Installer                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=linux;;
    Darwin*)    PLATFORM=mac;;
    CYGWIN*|MINGW*|MSYS*) PLATFORM=windows;;
    *)          PLATFORM=unknown;;
esac

echo -e "${YELLOW}Detected platform: ${PLATFORM}${NC}"

# Installation directory
INSTALL_DIR="${HOME}/.claude-session-keeper"
BIN_DIR="${HOME}/.local/bin"

# Create directories
echo -e "${BLUE}Creating installation directory...${NC}"
mkdir -p "${INSTALL_DIR}"
mkdir -p "${BIN_DIR}"

# Check for Python 3
echo -e "${BLUE}Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}Found Python ${PYTHON_VERSION}${NC}"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}Found Python ${PYTHON_VERSION}${NC}"
else
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    echo "Please install Python 3.7+ and try again."
    exit 1
fi

# Check Python version is 3.7+
PYTHON_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
    echo -e "${RED}Error: Python 3.7+ is required. Found Python ${PYTHON_MAJOR}.${PYTHON_MINOR}${NC}"
    exit 1
fi

# Download or copy files
echo -e "${BLUE}Downloading Claude Session Keeper...${NC}"

# Check if we're running from repo or need to download
if [ -f "claude_health_check_cli.py" ]; then
    echo -e "${YELLOW}Installing from local directory...${NC}"
    cp -r ./*.py "${INSTALL_DIR}/"
    cp requirements.txt "${INSTALL_DIR}/" 2>/dev/null || true
else
    # Download from GitHub
    REPO_URL="https://raw.githubusercontent.com/nomadictuba2005/claude-session-keeper/main"

    echo "Downloading main files..."
    curl -fsSL "${REPO_URL}/claude_health_check_cli.py" -o "${INSTALL_DIR}/claude_health_check_cli.py"
    curl -fsSL "${REPO_URL}/session_stats.py" -o "${INSTALL_DIR}/session_stats.py"
    curl -fsSL "${REPO_URL}/notifications.py" -o "${INSTALL_DIR}/notifications.py"
    curl -fsSL "${REPO_URL}/profiles.py" -o "${INSTALL_DIR}/profiles.py"
    curl -fsSL "${REPO_URL}/interactive_cli.py" -o "${INSTALL_DIR}/interactive_cli.py"
    curl -fsSL "${REPO_URL}/web_dashboard.py" -o "${INSTALL_DIR}/web_dashboard.py"
    curl -fsSL "${REPO_URL}/requirements.txt" -o "${INSTALL_DIR}/requirements.txt"
fi

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
$PYTHON_CMD -m pip install --user -q requests pytz flask 2>/dev/null || {
    echo -e "${YELLOW}Warning: Could not install some dependencies. Trying with --break-system-packages...${NC}"
    $PYTHON_CMD -m pip install --user --break-system-packages -q requests pytz flask 2>/dev/null || true
}

# Create the CLI wrapper script
echo -e "${BLUE}Creating CLI command...${NC}"

cat > "${BIN_DIR}/claude-session-keeper" << 'WRAPPER'
#!/bin/bash
# Claude Session Keeper CLI Wrapper
INSTALL_DIR="${HOME}/.claude-session-keeper"
cd "${INSTALL_DIR}" && python3 claude_health_check_cli.py "$@"
WRAPPER

chmod +x "${BIN_DIR}/claude-session-keeper"

# Create short alias
cat > "${BIN_DIR}/csk" << 'WRAPPER'
#!/bin/bash
# Claude Session Keeper CLI (short alias)
INSTALL_DIR="${HOME}/.claude-session-keeper"
cd "${INSTALL_DIR}" && python3 claude_health_check_cli.py "$@"
WRAPPER

chmod +x "${BIN_DIR}/csk"

# Add to PATH if needed
SHELL_RC=""
if [ -f "${HOME}/.bashrc" ]; then
    SHELL_RC="${HOME}/.bashrc"
elif [ -f "${HOME}/.zshrc" ]; then
    SHELL_RC="${HOME}/.zshrc"
elif [ -f "${HOME}/.profile" ]; then
    SHELL_RC="${HOME}/.profile"
fi

# Check if BIN_DIR is in PATH
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo -e "${YELLOW}Adding ${BIN_DIR} to PATH...${NC}"

    if [ -n "${SHELL_RC}" ]; then
        echo "" >> "${SHELL_RC}"
        echo "# Claude Session Keeper" >> "${SHELL_RC}"
        echo "export PATH=\"\${HOME}/.local/bin:\${PATH}\"" >> "${SHELL_RC}"
        echo -e "${GREEN}Added to ${SHELL_RC}${NC}"

        # Also export for current session
        export PATH="${BIN_DIR}:${PATH}"
    else
        echo -e "${YELLOW}Please add the following to your shell config:${NC}"
        echo "export PATH=\"\${HOME}/.local/bin:\${PATH}\""
    fi
fi

# Create default config files
echo -e "${BLUE}Creating default configuration...${NC}"
cd "${INSTALL_DIR}"

# Create config.json if it doesn't exist
if [ ! -f "config.json" ]; then
    echo '{"webhook_url": ""}' > config.json
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Installation Complete!                             ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Installed to:${NC} ${INSTALL_DIR}"
echo -e "${BLUE}Commands:${NC}"
echo "  claude-session-keeper    - Full command"
echo "  csk                      - Short alias"
echo ""
echo -e "${YELLOW}Quick Start:${NC}"
echo "  csk --help               - Show all options"
echo "  csk --interactive        - Launch interactive menu"
echo "  csk --web                - Start web dashboard"
echo "  csk --once               - Run single health check"
echo "  csk --stats              - View statistics"
echo ""

# Check if we need to reload shell
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo -e "${YELLOW}Note: Run 'source ${SHELL_RC}' or restart your terminal to use the commands.${NC}"
fi

echo -e "${GREEN}Enjoy using Claude Session Keeper!${NC}"
