"""
Connect 4 Game Server - AI vs AI with Webhook Communication
"""
import json
import time
import requests
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
from copy import deepcopy

app = Flask(__name__)
CORS(app)

class Connect4Game:
    def __init__(self):
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.move_history = []

    def make_move(self, column, player):
        """Place a piece in the specified column"""
        if column < 0 or column > 6:
            return False

        # Find the lowest empty row in the column
        for row in range(5, -1, -1):
            if self.board[row][column] == 0:
                self.board[row][column] = player
                self.move_history.append({"column": column, "player": player, "row": row})
                return True
        return False

    def check_winner(self):
        """Check if there's a winner"""
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if (self.board[row][col] != 0 and
                    self.board[row][col] == self.board[row][col+1] ==
                    self.board[row][col+2] == self.board[row][col+3]):
                    return self.board[row][col]

        # Check vertical
        for row in range(3):
            for col in range(7):
                if (self.board[row][col] != 0 and
                    self.board[row][col] == self.board[row+1][col] ==
                    self.board[row+2][col] == self.board[row+3][col]):
                    return self.board[row][col]

        # Check diagonal (down-right)
        for row in range(3):
            for col in range(4):
                if (self.board[row][col] != 0 and
                    self.board[row][col] == self.board[row+1][col+1] ==
                    self.board[row+2][col+2] == self.board[row+3][col+3]):
                    return self.board[row][col]

        # Check diagonal (down-left)
        for row in range(3):
            for col in range(3, 7):
                if (self.board[row][col] != 0 and
                    self.board[row][col] == self.board[row+1][col-1] ==
                    self.board[row+2][col-2] == self.board[row+3][col-3]):
                    return self.board[row][col]

        return None

    def is_board_full(self):
        """Check if the board is full"""
        return all(self.board[0][col] != 0 for col in range(7))

    def get_valid_moves(self):
        """Get list of valid column indices"""
        return [col for col in range(7) if self.board[0][col] == 0]

    def get_state(self):
        """Get current game state"""
        return {
            "board": self.board,
            "current_player": self.current_player,
            "game_over": self.game_over,
            "winner": self.winner,
            "valid_moves": self.get_valid_moves(),
            "move_history": self.move_history
        }

# Global game instance
game = Connect4Game()
game_lock = threading.Lock()

# AI player configurations
AI_PLAYERS = {
    1: {
        "name": "Random AI",
        "url": "http://localhost:5001/move",
        "color": "#FF6B6B"
    },
    2: {
        "name": "Minimax AI",
        "url": "http://localhost:5002/move",
        "color": "#4ECDC4"
    }
}

@app.route('/')
def index():
    """Serve the main game page"""
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    """Get current game state"""
    with game_lock:
        return jsonify(game.get_state())

@app.route('/api/reset', methods=['POST'])
def reset_game():
    """Reset the game"""
    global game
    with game_lock:
        game = Connect4Game()
    return jsonify({"success": True})

@app.route('/api/start', methods=['POST'])
def start_game():
    """Start a new AI vs AI game"""
    global game
    with game_lock:
        game = Connect4Game()

    # Start game in background thread
    thread = threading.Thread(target=play_game_loop)
    thread.daemon = True
    thread.start()

    return jsonify({"success": True, "message": "Game started!"})

def request_move_from_ai(player_num):
    """Request a move from an AI player via webhook"""
    try:
        ai_config = AI_PLAYERS[player_num]
        game_state = game.get_state()

        # Send game state to AI player
        response = requests.post(
            ai_config['url'],
            json={
                "board": game_state["board"],
                "player": player_num,
                "valid_moves": game_state["valid_moves"]
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("column")
        else:
            print(f"AI {player_num} returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"Error requesting move from AI {player_num}: {e}")
        return None

def play_game_loop():
    """Main game loop for AI vs AI"""
    global game

    print("Starting AI vs AI game...")

    while True:
        with game_lock:
            if game.game_over:
                break

            current_player = game.current_player
            print(f"\nPlayer {current_player}'s turn ({AI_PLAYERS[current_player]['name']})")

        # Request move from current AI player
        column = request_move_from_ai(current_player)

        if column is None:
            # If AI fails to respond, pick a random valid move
            with game_lock:
                valid_moves = game.get_valid_moves()
                if valid_moves:
                    import random
                    column = random.choice(valid_moves)
                    print(f"AI failed to respond, choosing random column: {column}")
                else:
                    break

        # Make the move
        with game_lock:
            success = game.make_move(column, current_player)

            if not success:
                print(f"Invalid move {column} by player {current_player}")
                continue

            print(f"Player {current_player} placed in column {column}")

            # Check for winner
            winner = game.check_winner()
            if winner:
                game.winner = winner
                game.game_over = True
                print(f"\n🎉 Player {winner} ({AI_PLAYERS[winner]['name']}) wins!")
            elif game.is_board_full():
                game.game_over = True
                print("\n🤝 Game is a draw!")
            else:
                # Switch player
                game.current_player = 3 - current_player  # Switches between 1 and 2

        # Delay for visualization (1 second between moves)
        time.sleep(1.5)

    print("\nGame over!")

if __name__ == '__main__':
    print("🎮 Connect 4 AI Battle Server")
    print("=" * 50)
    print(f"Player 1: {AI_PLAYERS[1]['name']} - {AI_PLAYERS[1]['url']}")
    print(f"Player 2: {AI_PLAYERS[2]['name']} - {AI_PLAYERS[2]['url']}")
    print("=" * 50)
    print("\nStarting server on http://localhost:5000")
    print("Open your browser and click 'Start Game' to begin!\n")

    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
