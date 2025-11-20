#-----Imports-----
import numpy as np
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Force CPU (stable)
import torch #Basically a matrix
from enum import Enum
from typing import Optional
import random
import copy
from flask import Flask, request, jsonify
import asyncio
import websockets  # Added for server connect
from multiprocessing import Pool

#-----Creating chip class-----
#Each number represents the current state of a position
class Chip(Enum):
    EMPTY= [1,0,0]
    MINE= [0,1,0]
    THEIRS= [0,0,1]

def makeatensor(chip: Chip) -> torch.Tensor:
    return torch.tensor(chip.value, dtype=torch.float32)

#-----Storing the board as an array-----
#Creating a 2D array with empty chip objects
board = [[Chip.EMPTY for _ in range(7)] for _ in range(6)]

#-----AI go here-----
#Name of our AI: connect6x7
class AI(torch.nn.Module):
    def __init__(self, hidden_layers:int, hidden_size:int):
        super(AI, self).__init__()
        # 42 input nodes, representing the possible 2D positions
        layers = [torch.nn.Linear(126, hidden_size)]  # Fixed to 126 (42 positions * 3 one-hot)
        for _ in range(hidden_layers):
            layers.append(torch.nn.Linear(hidden_size, hidden_size))
        layers.append(torch.nn.ReLU())
        layers.append(torch.nn.Linear(hidden_size, 7))
        self.layers = torch.nn.Sequential(*layers)
        # seven possible oHow much farther from this point will the
        # object move before it stops momentarily and then starts to
        # move back to the left?utputs, representing the possible columns
        # for training steps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)

#-----Training connect6x7-----
model: AI = AI(3, 9) #three hidden layers with 9 nodes each
# Training loop
POPULATION_SIZE = 40
GENERATIONS = 50
MUTATION_RATE = 0.10 # 10% of weights get mutated
MUTATION_STRENGTH = 0.5 # changes the weights that are mutated
ELITE_COUNT = 8 # keeping 2% out of 400

def flatten_model(model):
    return torch.cat([p.view(-1) for p in model.parameters()])  # Fixed from torch.flatten(model)

def unflatten_weights(model, weights):
    idx = 0
    for p in model.parameters():
        numel = p.numel()
        p.data.copy_(weights[idx:idx+numel].view_as(p))
        idx += numel

def mutate(weights: torch.Tensor):
    mask = torch.rand_like(weights) < MUTATION_RATE
    noise = torch.randn_like(weights) * MUTATION_STRENGTH
    weights = weights + mask.float() * noise
    return weights

def create_random_individual():
    m = AI(3,9)
    for p in m.parameters():
        torch.nn.init.normal_(p, mean=0.0, std=0.3) # small random init
    return m

def play_match(model1, model2, games=2):
    model1_wins = model2_wins = draws = 0
    for _ in range(games):
        board = [[0] * 7 for _ in range(6)] # row 0=top
        player1_turn = True
        while True:
            valid_cols = [c for c in range(7) if board[0][c] == 0]
            if not valid_cols:
                draws += 1
                break
            if player1_turn:
                tensor = get_player_tensor(board, 1)
                with torch.no_grad():
                    logits = model1(tensor)
                col = max(valid_cols, key=lambda c: logits[c].item())
                drop_piece(board, col, 1)
                if check_winner(board) == 1:
                    model1_wins += 1
                    break
            else:
                tensor = get_player_tensor(board, 2)
                with torch.no_grad():
                    logits = model2(tensor)
                col = max(valid_cols, key=lambda c: logits[c].item())
                drop_piece(board, col, 2)
                if check_winner(board) == 2:
                    model2_wins += 1
                    break
            if is_board_full(board):
                draws += 1
                break
            player1_turn = not player1_turn
    return (model1_wins - model2_wins) / games if games else 0

def get_player_tensor(board, player):
    own = torch.tensor([0,1,0]) if player == 1 else torch.tensor([0,0,1])
    opp = torch.tensor([0,0,1]) if player == 1 else torch.tensor([0,1,0])
    empty = torch.tensor([1,0,0])
    flat = []
    for r in range(6):
        for c in range(7):
            cell = board[r][c]
            if cell == 0:
                flat.extend(empty)
            elif cell == player:
                flat.extend(own)
            else:
                flat.extend(opp)
    return torch.tensor(flat, dtype=torch.float32)

def drop_piece(board, col, player):
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            board[row][col] = player
            return True
    return False

def check_winner(board):
    # horizontal
    for r in range(6):
        for c in range(4):
            if board[r][c] and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                return board[r][c]
    # vertical
    for r in range(3):
        for c in range(7):
            if board[r][c] and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                return board[r][c]
    # diag /
    for r in range(3):
        for c in range(4):
            if board[r][c] and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                return board[r][c]
    # diag \
    for r in range(3):
        for c in range(3, 7):
            if board[r][c] and board[r][c] == board[r+1][c-1] == board[r+2][c-2] == board[r+3][c-3]:
                return board[r][c]
    return None

def is_board_full(board):
    return all(board[0][c] != 0 for c in range(7))

# ===== PERFECT AI (MINIMAX) FOR TRAINING =====
def evaluate_window(window, player, opponent):
    """Evaluate a 4-cell window for minimax heuristic"""
    score = 0
    player_count = window.count(player)
    opponent_count = window.count(opponent)
    empty_count = window.count(0)

    if player_count == 4:
        score += 100
    elif player_count == 3 and empty_count == 1:
        score += 5
    elif player_count == 2 and empty_count == 2:
        score += 2

    if opponent_count == 3 and empty_count == 1:
        score -= 4  # Block opponent

    return score

def evaluate_position(board, player):
    """Simple evaluation function for minimax"""
    opponent = 3 - player
    score = 0

    # Horizontal
    for r in range(6):
        for c in range(4):
            window = [board[r][c+i] for i in range(4)]
            score += evaluate_window(window, player, opponent)

    # Vertical
    for r in range(3):
        for c in range(7):
            window = [board[r+i][c] for i in range(4)]
            score += evaluate_window(window, player, opponent)

    # Diagonal /
    for r in range(3):
        for c in range(4):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, player, opponent)

    # Diagonal \
    for r in range(3):
        for c in range(3, 7):
            window = [board[r+i][c-i] for i in range(4)]
            score += evaluate_window(window, player, opponent)

    # Center column preference
    center_count = sum(1 for r in range(6) if board[r][3] == player)
    score += center_count * 3

    return score

def minimax(board, depth, alpha, beta, maximizing, player):
    """Minimax with alpha-beta pruning"""
    opponent = 3 - player

    # Check terminal states
    winner = check_winner(board)
    if winner == player:
        return 100000
    elif winner == opponent:
        return -100000
    elif is_board_full(board):
        return 0
    elif depth == 0:
        return evaluate_position(board, player)

    valid_cols = [c for c in range(7) if board[0][c] == 0]

    if maximizing:
        max_eval = float('-inf')
        for col in valid_cols:
            board_copy = [row[:] for row in board]
            drop_piece(board_copy, col, player)
            eval_score = minimax(board_copy, depth - 1, alpha, beta, False, player)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in valid_cols:
            board_copy = [row[:] for row in board]
            drop_piece(board_copy, col, opponent)
            eval_score = minimax(board_copy, depth - 1, alpha, beta, True, player)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def perfect_ai_move(board, player):
    """Perfect AI that uses minimax to find the best move"""
    valid_cols = [c for c in range(7) if board[0][c] == 0]

    # Check for immediate win
    for col in valid_cols:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, col, player)
        if check_winner(board_copy) == player:
            return col

    # Check for immediate block
    opponent = 3 - player
    for col in valid_cols:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, col, opponent)
        if check_winner(board_copy) == opponent:
            return col

    # Use minimax with depth 3 (fast but still strong)
    best_score = float('-inf')
    best_col = valid_cols[0]
    for col in valid_cols:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, col, player)
        score = minimax(board_copy, 3, float('-inf'), float('inf'), False, player)
        if score > best_score:
            best_score = score
            best_col = col

    return best_col

def play_match_vs_perfect(model, model_player=1, games=1):
    """Play match where model plays against perfect minimax AI
    model_player: 1 or 2, which player the model is
    Returns: (model_wins - perfect_wins) / games
    """
    model_wins = perfect_wins = draws = 0
    perfect_player = 3 - model_player

    for _ in range(games):
        board = [[0] * 7 for _ in range(6)]
        current_player = 1

        while True:
            valid_cols = [c for c in range(7) if board[0][c] == 0]
            if not valid_cols:
                draws += 1
                break

            if current_player == model_player:
                # Model's turn
                tensor = get_player_tensor(board, model_player)
                with torch.no_grad():
                    logits = model(tensor)
                col = max(valid_cols, key=lambda c: logits[c].item())
                drop_piece(board, col, model_player)
                if check_winner(board) == model_player:
                    model_wins += 1
                    break
            else:
                # Perfect AI's turn
                col = perfect_ai_move(board, perfect_player)
                drop_piece(board, col, perfect_player)
                if check_winner(board) == perfect_player:
                    perfect_wins += 1
                    break

            if is_board_full(board):
                draws += 1
                break
            current_player = 3 - current_player  # Switch between 1 and 2

    total = games
    return (model_wins - perfect_wins) / total if total else 0

def evaluate_network_vs_perfect(net):
    """Evaluate a single network against perfect AI (for multiprocessing)"""
    score = 0.0
    for _ in range(6):
        # Play both sides for fair fitness!
        score += play_match_vs_perfect(net, model_player=1, games=1)  # net as player 1
        score += play_match_vs_perfect(net, model_player=2, games=1)  # net as player 2
    return score

# ================================================================================
# ===== TRAINING SECTION AGAINST OTHERS FROM THE POOL =====
# population = [create_random_individual() for _ in range(POPULATION_SIZE)]
# for generation in range(GENERATIONS):
#     # Evaluate everyone (you can pair them randomly or round-robin subset
#     fitness = []
#     for i, net in enumerate(population):
#         # play say 6 games against random opponents from this pop
#         score = 0.0
#         for _ in range(6):
#             opponent = random.choice(population)
#             if opponent is net:  # avoid self-play
#                 opponent = random.choice(population)
#
#             # Play both sides for fair fitness!
#             score += play_match(net, opponent, games=1)      # net goes first
#             score -= play_match(opponent, net, games=1)      # net goes second (opponent first, so subtract their wins)
#         fitness.append((score, net))
#
#     # Sort by fitness descending
#     fitness.sort(reverse=True, key=lambda x: x[0])
#     print(f"Gen {generation} Best fitness: {fitness[0][0]:.3f}  (range: {fitness[-1][0]:.3f} → {fitness[0][0]:.3f})")
#
#     # Keep elite
#     new_pop = [copy.deepcopy(net) for _, net in fitness[:ELITE_COUNT]]
#
#     # Breed the rest
#     while len(new_pop) < POPULATION_SIZE:
#         parent = random.choice(fitness[:15])[1] # top 15 as parents
#         child = copy.deepcopy(parent)
#         weights = flatten_model(child)
#         weights = mutate(weights)
#         unflatten_weights(child, weights)
#         new_pop.append(child)
#     population = new_pop
#
# # Save best
# best_model = fitness[0][1]
# torch.save(best_model.state_dict(), "connect6x7.pth")
# ================================================================================

# ===== TRAINING SECTION (VS PERFECT AI) =====
population = [create_random_individual() for _ in range(POPULATION_SIZE)]
for generation in range(GENERATIONS):
    # Evaluate everyone against the perfect minimax AI (parallelized across 19 cores)
    with Pool(19) as pool:
        scores = pool.map(evaluate_network_vs_perfect, population)

    fitness = list(zip(scores, population))

    # Sort by fitness descending
    fitness.sort(reverse=True, key=lambda x: x[0])
    print(f"Gen {generation} Best fitness: {fitness[0][0]:.3f}  (range: {fitness[-1][0]:.3f} → {fitness[0][0]:.3f})")

    # Keep elite
    new_pop = [copy.deepcopy(net) for _, net in fitness[:ELITE_COUNT]]

    # Breed the rest
    while len(new_pop) < POPULATION_SIZE:
        parent = random.choice(fitness[:15])[1] # top 15 as parents
        child = copy.deepcopy(parent)
        weights = flatten_model(child)
        weights = mutate(weights)
        unflatten_weights(child, weights)
        new_pop.append(child)
    population = new_pop

# Save best
best_model = fitness[0][1]
torch.save(best_model.state_dict(), "connect6x7v1.pth")
# ===============================================================================

# Load model (or fresh if no file)
model = AI(3, 9)
try:
    model.load_state_dict(torch.load("connect6x7v1.pth"))
except FileNotFoundError:
    pass  # Use random
model.eval()

# Global int board for online play (consistent with training)
current_board = [[0] * 7 for _ in range(6)]
we_are_player1 = False  # Set on start

#-----Method to calculate the actual move the AI should make (Guidelines we want connect6x7 to "follow")-----
def calculate_move(currBoard: Optional[torch.Tensor]) -> int:
    global current_board
    #The AI will play against a PERFECT AI and will "learn" from it
    #BASED ON THE TRAINING, we want the AI to generally follow the instructions below
    #(also these comments are here for the paper part of the project so pls no delete)
    #https://www.rd.com/article/how-to-win-connect-4/
    """
        GOAL - Force player to make moves such that when it's the AI's turn, the AI has two possible
        winning positions at the same time which would then be impossible for the second player
        to block (ensuring a win)
        [From article]
        In Connect 4 parlance, whenever three playing pieces are lined up adjacently, it's called a "major threat,"
        even if it might take several moves to complete the line-of-four (due to the vertical nature of the columns).
        An "adjacent threat pair" refers to two major threats that are connected by at least one playing piece. And
        forming an adjacent threat pair—also known as "forking your threats"—is one key to a quicker win than you may
        achieve using the parity strategy, says Galli.
        """
    #If the AI is the beginning player....
    #choose the 4th column [0][3]
    """
        Also known as the parity strategy, "playing the odd rows" is when the first player
        aims to secure three pieces in a line so that an empty fourth spot is in one of the
        odd-numbered rows (the first, third or fifth from the bottom). That line can be horizontal,
        vertical or diagonal. Galli says that this is not only his favorite how-to-win Connect 4 strategy
        but also the one that is talked about least on social media—thus making it all the more powerful
        for those in the know.
        Given the finite number of positions on the grid, and assuming perfect play, this strategy should
        have the effect of leaving one of the columns "either free or nearly free" by the 37th move of the
        game, Galli notes. This will have the effect of forcing the second player to place their piece in the
        last spot before the first player’s winning spot.
        """
    # If the AI is the second player....
    # Same goal as above
    """
        The parity strategy discussed above works for the second player as well, except that the second player
        must set up their three-in-line in an even row, Galli points out. Of course, while setting things up as
        such, "you still have to make sure you're not ignoring some other risk." In other words, even as you play
        offensively, it's still important to play defensively, eliminating any advantage gained by the first player
        in an earlier move. This, of course, applies to the odd-parity play as well.
        """
    # IN THE CASE OF "DEFENDING"
    """
        In Connect 4 parlance, whenever three playing pieces are lined up adjacently, it's called a "major threat,"
        even if it might take several moves to complete the line-of-four (due to the vertical nature of the columns).
        An "adjacent threat pair" refers to two major threats that are connected by at least one playing piece. And
        forming an adjacent threat pair—also known as "forking your threats"—is one key to a quicker win than you may
        achieve using the parity strategy, says Galli.
        Galli's preferred fork is known by many as the "figure 7 trap" because the player making use of it creates a
        seven-shaped formation of their playing pieces. This involves three pieces in a diagonal line, where the top
        piece is also part of a three-piece horizontal line. If executed in the center of the board, in any orientation,
        this offers multiple opportunities for a win, and that can be difficult, if not impossible, for the other player
        to block. As you play more, you're likely to pick up on other forks as they arise organically, Allis notes.
        """
    # Output is an int representing the column to put circle thing
    # output = make a call to the ai network

    # Handle if currBoard is str col from opponent (ignore tensor param for server)
    if isinstance(currBoard, str):
        col = int(currBoard)
        opponent_player = 2 if we_are_player1 else 1
        drop_piece(current_board, col, opponent_player)

    # Compute our move
    our_player = 1 if we_are_player1 else 2
    tensor = get_player_tensor(current_board, our_player)
    with torch.no_grad():
        logits = model(tensor)
    valid_cols = [c for c in range(7) if current_board[0][c] == 0]
    col = max(valid_cols, key=lambda c: logits[c].item())
    
    # Apply locally
    drop_piece(current_board, col, our_player)

    # Returning the output
    return col  # Fixed placeholder

#-----Sending information to and from the server-----
async def gameloop (socket, created):
    global we_are_player1, current_board
    active = True
    while active: # While game is active, continually anticipate messages
        message = (await socket.recv()).split(':') # Receive message from server
        match message[0]:
            case 'GAMESTART': # Game has started
                we_are_player1 = created
                current_board = [[0] * 7 for _ in range(6)]
                if created: # If we created the game, it's our turn since we go first
                    col = calculate_move(None) # calculate_move is some arbitrary function you have created to figure out the next move
                    await socket.send(f'PLAY:{col}') # Send your move to the server
            case 'OPPONENT': # Opponent has gone; calculate next move
                col = calculate_move(message[1]) # Give your function your opponent's move
                await socket.send(f'PLAY:{col}') # Send your move to the server
            case 'WIN' | 'LOSS' | 'DRAW' | 'TERMINATED': # Game has ended
                print(message[0])
                active = False

async def create_game (server):
    async with websockets.connect(f'ws://{server}/create') as socket: # Establish websocket connection
        await gameloop(socket, True)

async def join_game(server, id):
    async with websockets.connect(f'ws://{server}/join/{id}') as socket: # Establish websocket connection
        await gameloop(socket, False)

#-----Main-----
if __name__ == '__main__': # Program entrypoint
    server = input('Server IP: ').strip() # Get IP from console
    protocol = input('Join game or create game? (j/c): ').strip() # Get action from console
    match protocol:
        case 'c':
                    asyncio.run(create_game(server))
        case 'j':
            id = input('Game ID: ').strip()
            asyncio.run(join_game(server, id))
        case _:
            print('Invalid protocol!')