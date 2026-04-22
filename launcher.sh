#!/bin/bash
#
# Log Scanner Supreme - Shell Launcher
# Compatible with Local Hoster desktop app
#
# Usage: bash launcher.sh -p 5001 -b 8001
#   -p PORT  Frontend port (default: 5000)
#   -b PORT  Backend port (accepted for compatibility; this app is a unified server)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default ports
FRONTEND_PORT=5000
BACKEND_PORT=""

# Parse command-line flags
while getopts "p:b:" opt; do
    case "$opt" in
        p) FRONTEND_PORT="$OPTARG" ;;
        b) BACKEND_PORT="$OPTARG" ;;
        *) echo "Usage: $0 [-p frontend_port] [-b backend_port]"; exit 1 ;;
    esac
done

# This is a unified Flask server (serves both UI and API).
# Use the frontend port as the app port.
APP_PORT="$FRONTEND_PORT"

if [ -n "$BACKEND_PORT" ] && [ "$BACKEND_PORT" != "$FRONTEND_PORT" ]; then
    echo "ℹ️  Note: Log Scanner Supreme is a unified server. Running on port $APP_PORT (frontend port)."
    echo "   The -b flag ($BACKEND_PORT) is accepted for compatibility but this app serves both UI and API on one port."
fi

echo ""
echo "=================================================="
echo "  Log Scanner Supreme - Launcher"
echo "=================================================="
echo ""

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "🐍 Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
    PYTHON="$SCRIPT_DIR/venv/bin/python"
else
    echo "⚠️  No virtual environment found at $SCRIPT_DIR/venv"
    echo "   Using system Python. Consider creating a venv:"
    echo "     cd $SCRIPT_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    PYTHON="python3"
fi

# Kill any existing process on the target port
echo "🔍 Checking for existing processes on port $APP_PORT..."
EXISTING_PIDS=$(lsof -ti :"$APP_PORT" 2>/dev/null)
if [ -n "$EXISTING_PIDS" ]; then
    echo "⚠️  Killing existing processes on port $APP_PORT..."
    echo "$EXISTING_PIDS" | xargs kill -TERM 2>/dev/null
    sleep 1
    # Force kill any remaining
    REMAINING=$(lsof -ti :"$APP_PORT" 2>/dev/null)
    if [ -n "$REMAINING" ]; then
        echo "$REMAINING" | xargs kill -9 2>/dev/null
        sleep 0.5
    fi
    echo "✅ Existing processes terminated"
else
    echo "✅ No existing process found on port $APP_PORT"
fi

# Check dependencies
echo "📦 Checking dependencies..."
if $PYTHON -c "import flask; import openai; import tiktoken; import dotenv" 2>/dev/null; then
    echo "✅ All dependencies satisfied"
else
    echo "❌ Missing dependencies. Installing..."
    $PYTHON -m pip install -r "$SCRIPT_DIR/requirements.txt"
    echo "✅ Dependencies installed"
fi

# Launch the app
echo ""
echo "🚀 Launching Log Scanner Supreme on port $APP_PORT..."
echo "   URL: http://localhost:$APP_PORT"
echo "   Press Ctrl+C to stop"
echo "=================================================="

cd "$SCRIPT_DIR"
$PYTHON app.py --port "$APP_PORT" &
APP_PID=$!

# Trap Ctrl+C to clean up
trap "echo ''; echo '👋 Shutting down...'; kill $APP_PID 2>/dev/null; exit 0" INT TERM

# Wait for all background processes
wait
