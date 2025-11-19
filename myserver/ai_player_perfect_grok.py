"""
Perfect Minimax AI Player for Connect 4
Uses bitboard representation for optimal performance
"""
from flask import Flask, request, jsonify
import time
import sys

# Increase recursion limit for deep Connect 4 search
sys.setrecursionlimit(2000)

app = Flask(__name__)

# Board dimensions
ROWS = 6
COLS = 7
TOTAL_CELLS = ROWS * COLS

# Transposition table
trans_table = {}

def solve_position(current: int, mask: int) -> int:
    """
    Returns the score from the perspective of the player about to move.
    Positive = win for current player (number of moves until win)
    Negative = loss (opponent wins in -score moves)
    0 = draw
    """
    # Check if the previous player already won (they just moved)
    if is_winning(mask ^ current):  # opponent's pieces = all occupied XOR current player's pieces
        return - (TOTAL_CELLS - bin(mask).count('1') ) // 2 - 1

    # Board full?
    if mask == (1 << (ROWS * COLS)) - 1:
        return 0

    key = (current, mask)
    if key in trans_table:
        return trans_table[key]

    # Try moves in center-first order (greatly improves alpha-beta pruning)
    best_score = -TOTAL_CELLS
    for col in [3, 2, 4, 1, 5, 0, 6]:
        if can_play(mask, col):
            next_current = current | (1 << (col * (ROWS + 1) + height(mask, col)))
            next_mask = mask | (1 << (col * (ROWS + 1) + height(mask, col)))
            score = -solve_position(next_current, next_mask)
            if score > best_score:
                best_score = score
            # Immediate win found → no need to look further
            if best_score >= (TOTAL_CELLS - bin(mask).count('1') - 1) // 2:
                break

    trans_table[key] = best_score
    return best_score

def get_best_move(current: int, mask: int) -> int:
    """Returns the best column (0-6) for the current player"""
    best_score = -TOTAL_CELLS
    best_col = 3
    moves_made = bin(mask).count('1')

    for col in [3, 2, 4, 1, 5, 0, 6]:
        if can_play(mask, col):
            pos = col * (ROWS + 1) + height(mask, col)
            next_current = current | (1 << pos)
            next_mask = mask | (1 << pos)
            score = -solve_position(next_current, next_mask)
            if score > best_score:
                best_score = score
                best_col = col
            if best_score >= (TOTAL_CELLS - moves_made - 1) // 2:
                break
    return best_col

# Helper functions
def height(mask: int, col: int) -> int:
    """Returns the row where the next piece in col will land"""
    return (mask >> (col * (ROWS + 1)) & ((1 << ROWS) - 1)).bit_count()

def can_play(mask: int, col: int) -> bool:
    return height(mask, col) < ROWS

def is_winning(b: int) -> bool:
    # Horizontal
    m = b & (b >> (ROWS + 1))
    if m & (m >> 2 * (ROWS + 1)): return True
    # Vertical
    m = b & (b >> 1)
    if m & (m >> 2): return True
    # Diagonal /
    m = b & (b >> ROWS)
    if m & (m >> 2 * ROWS): return True
    # Diagonal \
    m = b & (b >> (ROWS + 2))
    if m & (m >> 2 * (ROWS + 2)): return True
    return False

def board_to_bitboards(board):
    """Convert 2D board to bitboard representation"""
    current = 0  # Current player's pieces
    mask = 0     # All occupied positions

    for col in range(COLS):
        for row in range(ROWS):
            if board[row][col] != 0:
                # Convert from 2D array coordinates to bitboard coordinates
                # board[0] is top row, board[5] is bottom row
                # In bitboard, bit 0 is bottom of column
                bitboard_row = ROWS - 1 - row
                pos = col * (ROWS + 1) + bitboard_row
                mask |= (1 << pos)
                if board[row][col] == 1:  # Player 1's pieces
                    current |= (1 << pos)

    return current, mask

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

        # Convert board to bitboards
        current, mask = board_to_bitboards(board)

        # If player 2 is moving, we need to flip the perspective
        if player == 2:
            # Player 2's pieces are the opponent in our bitboard representation
            # So we need to invert: current becomes opponent's pieces, and vice versa
            all_pieces = mask
            opponent_pieces = current
            current = all_pieces ^ opponent_pieces  # XOR to get player 2's pieces

        # Clear transposition table for fresh solve
        trans_table.clear()

        start_time = time.time()
        column = get_best_move(current, mask)
        duration = time.time() - start_time

        print(f"Perfect Minimax AI (Player {player}): Choosing column {column} in {duration:.3f}s")

        return jsonify({"column": column})

    except Exception as e:
        print(f"Error in Perfect Minimax AI: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "name": "Perfect Minimax AI"})

if __name__ == '__main__':
    print("Perfect Minimax AI Player")
    print("Listening on http://localhost:5003")
    print("Strategy: Perfect minimax solver with bitboards\n")
    app.run(host='0.0.0.0', port=5003, debug=False)