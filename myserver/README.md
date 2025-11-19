# 🎮 Connect 4 AI Battle Arena

A modern, sleek web application where AI players battle each other in Connect 4 using webhook-based communication. Watch in real-time as different AI strategies compete!

## ✨ Features

- **AI vs AI Gameplay**: Watch two AI players battle it out
- **Webhook Architecture**: AI players communicate via HTTP webhooks
- **Modern UI**: Beautiful, animated interface with real-time updates
- **Visual Delays**: Smooth animations so humans can follow the action
- **Two AI Players**:
  - 🤖 **Random AI**: Makes random valid moves
  - 🧠 **Minimax AI**: Uses minimax algorithm with alpha-beta pruning

## 🏗️ Architecture

```
┌─────────────────┐
│  Game Server    │
│   (Flask)       │
│  Port: 5000     │
└────────┬────────┘
         │
         ├──────webhook──────→ ┌─────────────────┐
         │                     │  Random AI      │
         │                     │  Port: 5001     │
         │                     └─────────────────┘
         │
         └──────webhook──────→ ┌─────────────────┐
                               │  Minimax AI     │
                               │  Port: 5002     │
                               └─────────────────┘
```

## 📋 Requirements

- Python 3.7+
- Flask
- flask-cors
- requests

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the AI Players

Open three separate terminals:

**Terminal 1 - Random AI:**
```bash
python ai_player_random.py
```

**Terminal 2 - Minimax AI:**
```bash
python ai_player_minimax.py
```

**Terminal 3 - Game Server:**
```bash
python game_server.py
```

### 3. Open Your Browser

Navigate to: `http://localhost:5000`

Click "Start New Game" and watch the AIs battle!

## 🎯 How It Works

### Game Flow

1. Game server manages the Connect 4 board and game state
2. When it's a player's turn, the server sends a webhook POST request to that AI's endpoint
3. The AI receives the board state and responds with a column number
4. The server places the piece and checks for a winner
5. The browser polls the server every 500ms for updates
6. Animations and delays (1.5s between moves) make the game watchable

### Webhook API

**Request to AI Player:**
```json
POST /move
{
  "board": [[0,0,0,0,0,0,0], ...],  // 6x7 grid (0=empty, 1=player1, 2=player2)
  "player": 1,                       // Current player number
  "valid_moves": [0,1,2,3,4,5,6]     // Available columns
}
```

**Response from AI Player:**
```json
{
  "column": 3  // Column index (0-6) to place piece
}
```

## 🤖 AI Strategies

### Random AI (Port 5001)

- **Strategy**: Randomly selects from valid columns
- **Complexity**: O(1)
- **Advantage**: Fast, unpredictable
- **Weakness**: No strategy

### Minimax AI (Port 5002)

- **Strategy**: Minimax algorithm with alpha-beta pruning
- **Depth**: 4 levels deep
- **Complexity**: O(b^d) with pruning optimization
- **Features**:
  - Evaluates board positions
  - Prefers center columns
  - Blocks opponent winning moves
  - Plans ahead 4 moves

## 🎨 UI Features

- **Live Board Updates**: Real-time piece placement with animations
- **Player Status**: Shows which AI is thinking
- **Move History**: Scrollable list of all moves
- **Win Detection**: Highlights winning position
- **Responsive Design**: Works on desktop and mobile

## 🔧 Customization

### Change AI Difficulty

Edit `ai_player_minimax.py`:
```python
ai = Connect4AI(depth=6)  # Increase for harder AI
```

### Adjust Move Speed

Edit `game_server.py`:
```python
time.sleep(2.0)  # Increase delay between moves
```

### Use Different AI Players

Edit the `AI_PLAYERS` dictionary in `game_server.py`:
```python
AI_PLAYERS = {
    1: {
        "name": "Your AI Name",
        "url": "http://localhost:5003/move",
        "color": "#FF6B6B"
    },
    # ...
}
```

## 🛠️ Creating Your Own AI

Create a new Python file (e.g., `ai_player_custom.py`):

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/move', methods=['POST'])
def get_move():
    data = request.json
    board = data['board']
    player = data['player']
    valid_moves = data['valid_moves']

    # Your AI logic here
    column = your_strategy(board, player, valid_moves)

    return jsonify({"column": column})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
```

Then update `game_server.py` to use your new AI!

## 📝 Project Structure

```
connect4mod/
├── game_server.py           # Main game server
├── ai_player_random.py      # Random AI player
├── ai_player_minimax.py     # Minimax AI player
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── static/
│   ├── style.css           # Modern UI styles
│   └── game.js             # Frontend JavaScript
└── templates/
    └── index.html          # Main page
```

## 🐛 Troubleshooting

**Problem**: Game won't start
- **Solution**: Make sure all three servers are running (game server + 2 AI players)

**Problem**: AI not responding
- **Solution**: Check the terminal for error messages. Ensure the ports (5001, 5002) are not in use

**Problem**: Board not updating
- **Solution**: Check browser console for errors. Try refreshing the page

## 🎓 Learning Resources

This project demonstrates:
- Flask web framework
- RESTful API design
- Webhook architecture
- Game AI algorithms (Minimax)
- Real-time web updates
- Modern CSS animations

## 📄 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

Want to add a new AI strategy? Create a pull request!

Ideas for contributions:
- Monte Carlo Tree Search AI
- Neural network-based AI
- Different board sizes
- Tournament mode
- AI vs Human mode

---

**Enjoy watching the AI battle! 🎮🤖🧠**
