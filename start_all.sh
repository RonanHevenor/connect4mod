#!/bin/bash

# Connect 4 AI Battle - Startup Script
# Starts all three servers in the background

echo "🎮 Starting Connect 4 AI Battle Arena..."
echo "========================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if required packages are installed
python3 -c "import flask" 2>/dev/null || {
    echo "Installing dependencies..."
    pip install -r requirements.txt
}

echo ""
echo "Starting AI Players..."

# Start Random AI (Player 1)
python3 ai_player_random.py > logs_random_ai.txt 2>&1 &
PID_RANDOM=$!
echo "✓ Random AI started (PID: $PID_RANDOM) on port 5001"

# Start Minimax AI (Player 2)
python3 ai_player_minimax.py > logs_minimax_ai.txt 2>&1 &
PID_MINIMAX=$!
echo "✓ Minimax AI started (PID: $PID_MINIMAX) on port 5002"

# Wait a moment for AI players to start
sleep 2

echo ""
echo "Starting Game Server..."

# Start Game Server
python3 game_server.py > logs_game_server.txt 2>&1 &
PID_GAME=$!
echo "✓ Game Server started (PID: $PID_GAME) on port 5000"

echo ""
echo "========================================"
echo "🎉 All servers are running!"
echo "========================================"
echo ""
echo "🌐 Open your browser to: http://localhost:5000"
echo ""
echo "Process IDs:"
echo "  - Random AI:    $PID_RANDOM"
echo "  - Minimax AI:   $PID_MINIMAX"
echo "  - Game Server:  $PID_GAME"
echo ""
echo "To stop all servers, run: ./stop_all.sh"
echo "Or use: kill $PID_RANDOM $PID_MINIMAX $PID_GAME"
echo ""

# Save PIDs to file for stop script
echo "$PID_RANDOM" > .pids
echo "$PID_MINIMAX" >> .pids
echo "$PID_GAME" >> .pids

echo "Logs are being written to:"
echo "  - logs_random_ai.txt"
echo "  - logs_minimax_ai.txt"
echo "  - logs_game_server.txt"
echo ""
