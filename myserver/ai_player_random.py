"""
Random AI Player for Connect 4
This AI randomly selects from valid moves
"""
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/move', methods=['POST'])
def get_move():
    """
    Receive game state and return a move

    Expected JSON payload:
    {
        "board": [[...], ...],  # 6x7 board
        "player": 1 or 2,
        "valid_moves": [0, 1, 2, ...]  # List of valid column indices
    }

    Returns JSON:
    {
        "column": 0-6  # Column to place the piece
    }
    """
    try:
        data = request.json
        board = data.get('board')
        player = data.get('player')
        valid_moves = data.get('valid_moves', [])

        if not valid_moves:
            return jsonify({"error": "No valid moves available"}), 400

        # Random strategy: pick a random valid column
        column = random.choice(valid_moves)

        print(f"Random AI (Player {player}): Choosing column {column}")

        return jsonify({"column": column})

    except Exception as e:
        print(f"Error in Random AI: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "name": "Random AI"})

if __name__ == '__main__':
    print("Random AI Player")
    print("Listening on http://localhost:5001")
    print("Strategy: Randomly selects from valid moves\n")
    app.run(host='0.0.0.0', port=5001, debug=False)
