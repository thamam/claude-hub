#!/bin/bash
# Installation script for Claude Code Usage Pattern Logger

set -e

echo "========================================"
echo "Claude Code Usage Pattern Logger Setup"
echo "========================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Found Python $PYTHON_VERSION"
echo ""

# Make scripts executable
echo "Making scripts executable..."
chmod +x "$SCRIPT_DIR/logger.py"
chmod +x "$SCRIPT_DIR/stats_poc.py"
echo "✓ Scripts are now executable"
echo ""

# Create symlinks in ~/bin (if directory exists) or /usr/local/bin
echo "Setting up command-line tools..."

BIN_DIR=""
if [ -d "$HOME/bin" ]; then
    BIN_DIR="$HOME/bin"
elif [ -w "/usr/local/bin" ]; then
    BIN_DIR="/usr/local/bin"
else
    echo "Warning: Could not find suitable bin directory."
    echo "You can manually create symlinks:"
    echo "  ln -sf $SCRIPT_DIR/stats_poc.py ~/bin/claude-usage-stats-poc"
    BIN_DIR=""
fi

if [ -n "$BIN_DIR" ]; then
    mkdir -p "$BIN_DIR"
    ln -sf "$SCRIPT_DIR/stats_poc.py" "$BIN_DIR/claude-usage-stats-poc"
    echo "✓ Created symlink: claude-usage-stats-poc -> $BIN_DIR"

    # Check if bin directory is in PATH
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo ""
        echo "Warning: $BIN_DIR is not in your PATH."
        echo "Add this line to your ~/.bashrc or ~/.zshrc:"
        echo "  export PATH=\"\$PATH:$BIN_DIR\""
    fi
fi

echo ""
echo "========================================"
echo "Phase 1 Installation Complete!"
echo "========================================"
echo ""
echo "Testing the logger..."
python3 "$SCRIPT_DIR/logger.py"
echo ""

echo "Viewing stats..."
python3 "$SCRIPT_DIR/stats_poc.py"
echo ""

echo "========================================"
echo "Next Steps:"
echo "========================================"
echo ""
echo "1. Test the logger:"
echo "   python3 ~/claude-usage-logger/logger.py"
echo ""
echo "2. View usage statistics:"
if [ -n "$BIN_DIR" ]; then
    echo "   claude-usage-stats-poc"
else
    echo "   python3 ~/claude-usage-logger/stats_poc.py"
fi
echo ""
echo "3. The log file is located at:"
echo "   ~/.claude_usage_log.jsonl"
echo ""
echo "4. To use the logger in your own scripts:"
echo "   import sys"
echo "   sys.path.insert(0, '$SCRIPT_DIR')"
echo "   from logger import log_tool_usage, log_skill"
echo ""
echo "5. For Phase 2 (SQLite migration), run:"
echo "   python3 ~/claude-usage-logger/migrate.py"
echo "   (after Phase 2 files are created)"
echo ""
echo "========================================"
echo "Documentation: See README.md for details"
echo "========================================"
