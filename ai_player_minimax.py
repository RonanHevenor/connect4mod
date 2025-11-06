"""
Minimax AI Player for Connect 4
This AI uses the minimax algorithm with alpha-beta pruning
"""
from flask import Flask, request, jsonify
from copy import deepcopy

app = Flask(__name__)

class Connect4AI:
    def __init__(self, depth=4):
        self.depth = depth

    def evaluate_window(self, window, player):
        """Evaluate a window of 4 cells"""
        score = 0
        opponent = 3 - player

        # Count pieces
        player_count = window.count(player)
        opponent_count = window.count(opponent)
        empty_count = window.count(0)

        # Scoring heuristic
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif player_count == 2 and empty_count == 2:
            score += 2

        if opponent_count == 3 and empty_count == 1:
            score -= 4  # Block opponent

        return score

    def evaluate_board(self, board, player):
        """Evaluate the entire board position"""
        score = 0

        # Score center column (strategic advantage)
        center_array = [board[row][3] for row in range(6)]
        center_count = center_array.count(player)
        score += center_count * 3

        # Score horizontal
        for row in range(6):
            for col in range(4):
                window = [board[row][col+i] for i in range(4)]
                score += self.evaluate_window(window, player)

        # Score vertical
        for col in range(7):
            for row in range(3):
                window = [board[row+i][col] for i in range(4)]
                score += self.evaluate_window(window, player)

        # Score diagonal (down-right)
        for row in range(3):
            for col in range(4):
                window = [board[row+i][col+i] for i in range(4)]
                score += self.evaluate_window(window, player)

        # Score diagonal (down-left)
        for row in range(3):
            for col in range(3, 7):
                window = [board[row+i][col-i] for i in range(4)]
                score += self.evaluate_window(window, player)

        return score

    def check_winner(self, board):
        """Check if there's a winner"""
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if (board[row][col] != 0 and
                    board[row][col] == board[row][col+1] ==
                    board[row][col+2] == board[row][col+3]):
                    return board[row][col]

        # Check vertical
        for row in range(3):
            for col in range(7):
                if (board[row][col] != 0 and
                    board[row][col] == board[row+1][col] ==
                    board[row+2][col] == board[row+3][col]):
                    return board[row][col]

        # Check diagonal (down-right)
        for row in range(3):
            for col in range(4):
                if (board[row][col] != 0 and
                    board[row][col] == board[row+1][col+1] ==
                    board[row+2][col+2] == board[row+3][col+3]):
                    return board[row][col]

        # Check diagonal (down-left)
        for row in range(3):
            for col in range(3, 7):
                if (board[row][col] != 0 and
                    board[row][col] == board[row+1][col-1] ==
                    board[row+2][col-2] == board[row+3][col-3]):
                    return board[row][col]

        return None

    def is_terminal_node(self, board):
        """Check if the game is over"""
        winner = self.check_winner(board)
        if winner:
            return True
        # Check if board is full
        return all(board[0][col] != 0 for col in range(7))

    def get_valid_moves(self, board):
        """Get list of valid column indices"""
        return [col for col in range(7) if board[0][col] == 0]

    def make_move(self, board, column, player):
        """Make a move on a copy of the board"""
        new_board = deepcopy(board)
        for row in range(5, -1, -1):
            if new_board[row][column] == 0:
                new_board[row][column] = player
                return new_board
        return None

    def minimax(self, board, depth, alpha, beta, maximizing_player, player):
        """Minimax algorithm with alpha-beta pruning"""
        valid_moves = self.get_valid_moves(board)
        is_terminal = self.is_terminal_node(board)

        if depth == 0 or is_terminal:
            if is_terminal:
                winner = self.check_winner(board)
                if winner == player:
                    return (None, 100000)
                elif winner == (3 - player):
                    return (None, -100000)
                else:  # Draw
                    return (None, 0)
            else:  # Depth is 0
                return (None, self.evaluate_board(board, player))

        if maximizing_player:
            value = float('-inf')
            best_column = valid_moves[0] if valid_moves else None

            for col in valid_moves:
                new_board = self.make_move(board, col, player)
                if new_board is None:
                    continue

                new_score = self.minimax(new_board, depth - 1, alpha, beta, False, player)[1]

                if new_score > value:
                    value = new_score
                    best_column = col

                alpha = max(alpha, value)
                if alpha >= beta:
                    break

            return best_column, value

        else:  # Minimizing player
            value = float('inf')
            best_column = valid_moves[0] if valid_moves else None
            opponent = 3 - player

            for col in valid_moves:
                new_board = self.make_move(board, col, opponent)
                if new_board is None:
                    continue

                new_score = self.minimax(new_board, depth - 1, alpha, beta, True, player)[1]

                if new_score < value:
                    value = new_score
                    best_column = col

                beta = min(beta, value)
                if alpha >= beta:
                    break

            return best_column, value

    def get_best_move(self, board, player):
        """Get the best move using minimax"""
        column, score = self.minimax(board, self.depth, float('-inf'), float('inf'), True, player)
        return column

# Global AI instance
ai = Connect4AI(depth=4)

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

        # Use minimax to find best move
        column = ai.get_best_move(board, player)

        # Fallback to center if minimax returns None
        if column is None:
            column = 3 if 3 in valid_moves else valid_moves[0]

        print(f"🧠 Minimax AI (Player {player}): Choosing column {column}")

        return jsonify({"column": column})

    except Exception as e:
        print(f"Error in Minimax AI: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "name": "Minimax AI"})

if __name__ == '__main__':
    print("🧠 Minimax AI Player Starting...")
    print("Listening on http://localhost:5002")
    print("Strategy: Minimax algorithm with alpha-beta pruning (depth=4)\n")
    app.run(host='0.0.0.0', port=5002, debug=False)
