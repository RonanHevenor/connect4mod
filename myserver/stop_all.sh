#!/bin/bash

# Connect 4 AI Battle - Stop Script
# Stops all running servers

echo "🛑 Stopping Connect 4 AI Battle Arena..."
echo "========================================"

if [ -f .pids ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null
            echo "✓ Stopped process $pid"
        else
            echo "  Process $pid not running"
        fi
    done < .pids
    rm .pids
    echo ""
    echo "✓ All servers stopped!"
else
    echo "No PID file found. Attempting to kill by port..."

    # Try to kill by port
    lsof -ti:5000 | xargs kill 2>/dev/null && echo "✓ Stopped server on port 5000"
    lsof -ti:5001 | xargs kill 2>/dev/null && echo "✓ Stopped server on port 5001"
    lsof -ti:5002 | xargs kill 2>/dev/null && echo "✓ Stopped server on port 5002"
fi

echo "========================================"
