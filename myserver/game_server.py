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
        "color": "#FF6B6B",
        "type": "ai"
    },
    2: {
        "name": "Minimax AI",
        "url": "http://localhost:5002/move",
        "color": "#4ECDC4",
        "type": "ai"
    }
}

# Game settings
GAME_SETTINGS = {
    "move_delay": 1.5
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

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update AI player configuration and game settings"""
    global AI_PLAYERS, GAME_SETTINGS
    try:
        data = request.json

        # Update player 1 config
        if 'player1' in data:
            AI_PLAYERS[1].update({
                "name": data['player1'].get('name', AI_PLAYERS[1]['name']),
                "url": data['player1'].get('url', AI_PLAYERS[1]['url']),
                "color": data['player1'].get('color', AI_PLAYERS[1]['color']),
                "type": data['player1'].get('type', AI_PLAYERS[1].get('type', 'ai'))
            })

        # Update player 2 config
        if 'player2' in data:
            AI_PLAYERS[2].update({
                "name": data['player2'].get('name', AI_PLAYERS[2]['name']),
                "url": data['player2'].get('url', AI_PLAYERS[2]['url']),
                "color": data['player2'].get('color', AI_PLAYERS[2]['color']),
                "type": data['player2'].get('type', AI_PLAYERS[2].get('type', 'ai'))
            })

        # Update move delay
        if 'moveDelay' in data:
            GAME_SETTINGS['move_delay'] = float(data['moveDelay'])

        print(f"Configuration updated:")
        print(f"  Player 1: {AI_PLAYERS[1]['name']} @ {AI_PLAYERS[1]['url']}")
        print(f"  Player 2: {AI_PLAYERS[2]['name']} @ {AI_PLAYERS[2]['url']}")
        print(f"  Move Delay: {GAME_SETTINGS['move_delay']}s")

        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating config: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/human_move', methods=['POST'])
def human_move():
    """Handle human player move"""
    try:
        data = request.json
        column = data.get('column')

        if column is None or not isinstance(column, int) or column < 0 or column > 6:
            return jsonify({"success": False, "error": "Invalid column"}), 400

        with game_lock:
            if game.game_over:
                return jsonify({"success": False, "error": "Game is over"}), 400

            # Check if it's a human player's turn
            current_player = game.current_player
            player_config = AI_PLAYERS[current_player]

            if player_config.get('type') != 'human':
                return jsonify({"success": False, "error": "Not human player's turn"}), 400

            # Make the move
            success = game.make_move(column, current_player)

            if not success:
                return jsonify({"success": False, "error": "Invalid move"}), 400

            # Check for winner
            winner = game.check_winner()
            if winner:
                game.winner = winner
                game.game_over = True
            elif game.is_board_full():
                game.game_over = True
                game.winner = None  # Draw
            else:
                # Switch player
                game.current_player = 3 - current_player

                # If the next player is AI, make their move automatically
                next_player = game.current_player
                next_player_config = AI_PLAYERS[next_player]
                if next_player_config.get('type') == 'ai' and not game.game_over:
                    # Make AI move
                    column = request_move_from_ai(next_player)
                    if column is not None:
                        success = game.make_move(column, next_player)
                        if success:
                            print(f"AI Player {next_player} placed in column {column}")

                            # Check for winner again
                            winner = game.check_winner()
                            if winner:
                                game.winner = winner
                                game.game_over = True
                                print(f"AI Player {winner} wins!")
                            elif game.is_board_full():
                                game.game_over = True
                                game.winner = None
                                print("Game is a draw!")
                            else:
                                # Switch back to human player
                                game.current_player = 3 - next_player

        return jsonify({"success": True})

    except Exception as e:
        print(f"Error in human move: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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
    """Main game loop for AI vs AI or Human vs AI"""
    global game

    print("Starting game...")

    while True:
        with game_lock:
            if game.game_over:
                break

            current_player = game.current_player
            player_config = AI_PLAYERS[current_player]
            player_type = player_config.get('type', 'ai')

            print(f"\nPlayer {current_player}'s turn ({player_config['name']}) - Type: {player_type}")

            # If human player, wait for their move (don't make automatic moves)
            if player_type == 'human':
                print(f"Waiting for human player {current_player} to make a move...")
                # Sleep briefly and continue loop to check game state
                time.sleep(0.5)
                continue

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
                print(f"\nPlayer {winner} ({AI_PLAYERS[winner]['name']}) wins!")
            elif game.is_board_full():
                game.game_over = True
                print("\nGame is a draw!")
            else:
                # Switch player
                game.current_player = 3 - current_player  # Switches between 1 and 2

        # Delay for visualization (configurable)
        time.sleep(GAME_SETTINGS['move_delay'])

    print("\nGame over!")

if __name__ == '__main__':
    print("Connect 4 AI Battle Server")
    print("=" * 50)
    print(f"Player 1: {AI_PLAYERS[1]['name']} - {AI_PLAYERS[1]['url']}")
    print(f"Player 2: {AI_PLAYERS[2]['name']} - {AI_PLAYERS[2]['url']}")
    print("=" * 50)
    print("\nStarting server on http://localhost:5000")
    print("Open your browser to begin\n")

    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
