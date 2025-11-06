// Connect 4 AI Battle - Frontend JavaScript

let gameState = null;
let pollingInterval = null;
let config = {
    player1: {
        name: 'Random AI',
        url: 'http://localhost:5001/move',
        color: '#FF6B6B'
    },
    player2: {
        name: 'Minimax AI',
        url: 'http://localhost:5002/move',
        color: '#4ECDC4'
    },
    moveDelay: 1.5
};

// DOM Elements - Screens
const configScreen = document.getElementById('config-screen');
const gameScreen = document.getElementById('game-screen');

// DOM Elements - Config
const startBattleBtn = document.getElementById('start-battle-btn');
const player1UrlInput = document.getElementById('player1-url');
const player1NameInput = document.getElementById('player1-name');
const player1ColorInput = document.getElementById('player1-color');
const player2UrlInput = document.getElementById('player2-url');
const player2NameInput = document.getElementById('player2-name');
const player2ColorInput = document.getElementById('player2-color');
const moveDelayInput = document.getElementById('move-delay');

// DOM Elements - Game
const gameBoard = document.getElementById('game-board');
const newGameBtn = document.getElementById('new-game-btn');
const resetBtn = document.getElementById('reset-btn');
const backConfigBtn = document.getElementById('back-config-btn');
const gameStatus = document.getElementById('game-status');
const moveCount = document.getElementById('move-count');
const moveHistory = document.getElementById('move-history');
const player1Status = document.getElementById('player1-status');
const player2Status = document.getElementById('player2-status');
const player1DisplayName = document.getElementById('player1-display-name');
const player2DisplayName = document.getElementById('player2-display-name');

// Screen Management
function showConfigScreen() {
    configScreen.classList.add('active');
    gameScreen.classList.remove('active');
    stopPolling();
}

function showGameScreen() {
    configScreen.classList.remove('active');
    gameScreen.classList.add('active');
}

// Save configuration from form
function saveConfig() {
    config.player1.name = player1NameInput.value;
    config.player1.url = player1UrlInput.value;
    config.player1.color = player1ColorInput.value;

    config.player2.name = player2NameInput.value;
    config.player2.url = player2UrlInput.value;
    config.player2.color = player2ColorInput.value;

    config.moveDelay = parseFloat(moveDelayInput.value);

    // Update display names on game screen
    player1DisplayName.textContent = config.player1.name;
    player2DisplayName.textContent = config.player2.name;

    // Update CSS variables for colors
    updatePlayerColors();
}

// Update player colors in the UI
function updatePlayerColors() {
    const style = document.createElement('style');
    style.textContent = `
        .player1 { border-left-color: ${config.player1.color} !important; }
        .player2 { border-left-color: ${config.player2.color} !important; }
        .cell.player1::before {
            background: radial-gradient(circle, ${config.player1.color}, ${adjustColor(config.player1.color, -30)}) !important;
            box-shadow: 0 0 20px ${config.player1.color}99 !important;
        }
        .cell.player2::before {
            background: radial-gradient(circle, ${config.player2.color}, ${adjustColor(config.player2.color, -30)}) !important;
            box-shadow: 0 0 20px ${config.player2.color}99 !important;
        }
        .move-item.player1 { border-left-color: ${config.player1.color} !important; }
        .move-item.player2 { border-left-color: ${config.player2.color} !important; }
    `;
    document.head.appendChild(style);
}

// Helper function to adjust color brightness
function adjustColor(color, amount) {
    const num = parseInt(color.replace('#', ''), 16);
    const r = Math.max(0, Math.min(255, (num >> 16) + amount));
    const g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + amount));
    const b = Math.max(0, Math.min(255, (num & 0x0000FF) + amount));
    return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0');
}

// Initialize the board display
function initBoard() {
    gameBoard.innerHTML = '';
    for (let row = 0; row < 6; row++) {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'board-row';
        for (let col = 0; col < 7; col++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.row = row;
            cell.dataset.col = col;
            rowDiv.appendChild(cell);
        }
        gameBoard.appendChild(rowDiv);
    }
}

// Update the board display based on game state
function updateBoard(state) {
    if (!state || !state.board) return;

    const cells = document.querySelectorAll('.cell');
    cells.forEach(cell => {
        const row = parseInt(cell.dataset.row);
        const col = parseInt(cell.dataset.col);
        const value = state.board[row][col];

        // Remove all player classes
        cell.classList.remove('player1', 'player2', 'winning');

        // Add appropriate class
        if (value === 1) {
            cell.classList.add('player1');
        } else if (value === 2) {
            cell.classList.add('player2');
        }
    });

    // Update game status
    updateGameStatus(state);
    updateMoveHistory(state);
    updatePlayerStatus(state);
}

// Update game status display
function updateGameStatus(state) {
    if (state.game_over) {
        if (state.winner) {
            const winnerName = state.winner === 1 ? config.player1.name : config.player2.name;
            gameStatus.textContent = `🎉 ${winnerName} Wins!`;
            gameStatus.style.color = state.winner === 1 ? config.player1.color : config.player2.color;
        } else {
            gameStatus.textContent = '🤝 Draw!';
            gameStatus.style.color = '#FFD700';
        }
        stopPolling();
    } else {
        const currentPlayerName = state.current_player === 1 ? config.player1.name : config.player2.name;
        gameStatus.textContent = `${currentPlayerName}'s turn`;
        gameStatus.style.color = '#fff';
    }

    moveCount.textContent = state.move_history ? state.move_history.length : 0;
}

// Update move history display
function updateMoveHistory(state) {
    if (!state.move_history) return;

    // Only add new moves
    const currentMoveCount = moveHistory.children.length;
    const newMoves = state.move_history.slice(currentMoveCount);

    newMoves.forEach(move => {
        const moveItem = document.createElement('div');
        moveItem.className = `move-item player${move.player}`;
        const playerName = move.player === 1 ? config.player1.name : config.player2.name;
        moveItem.textContent = `${playerName} → Column ${move.column + 1}`;
        moveHistory.appendChild(moveItem);
    });

    // Scroll to bottom
    moveHistory.scrollTop = moveHistory.scrollHeight;
}

// Update player status indicators
function updatePlayerStatus(state) {
    const player1Card = document.querySelector('.player-card.player1');
    const player2Card = document.querySelector('.player-card.player2');

    if (!player1Card || !player2Card) return;

    // Remove active class
    player1Card.classList.remove('active');
    player2Card.classList.remove('active');

    if (!state.game_over) {
        if (state.current_player === 1) {
            player1Card.classList.add('active');
            player1Status.textContent = 'Thinking...';
            player2Status.textContent = 'Waiting';
        } else {
            player2Card.classList.add('active');
            player1Status.textContent = 'Waiting';
            player2Status.textContent = 'Thinking...';
        }
    } else {
        if (state.winner === 1) {
            player1Status.textContent = '🏆 Winner!';
            player2Status.textContent = 'Lost';
        } else if (state.winner === 2) {
            player1Status.textContent = 'Lost';
            player2Status.textContent = '🏆 Winner!';
        } else {
            player1Status.textContent = 'Draw';
            player2Status.textContent = 'Draw';
        }
    }
}

// Fetch current game state
async function fetchGameState() {
    try {
        const response = await fetch('/api/state');
        if (response.ok) {
            gameState = await response.json();
            updateBoard(gameState);
        }
    } catch (error) {
        console.error('Error fetching game state:', error);
    }
}

// Start polling for game state updates
function startPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    // Poll every 500ms for smooth updates
    pollingInterval = setInterval(fetchGameState, 500);
}

// Stop polling
function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// Send configuration to server
async function sendConfigToServer() {
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        return response.ok;
    } catch (error) {
        console.error('Error sending config:', error);
        return false;
    }
}

// Start battle (from config screen)
async function startBattle() {
    try {
        startBattleBtn.disabled = true;
        startBattleBtn.textContent = '🔄 Initializing...';

        // Save configuration
        saveConfig();

        // Send config to server
        const configOk = await sendConfigToServer();
        if (!configOk) {
            alert('Failed to configure server');
            return;
        }

        // Switch to game screen
        showGameScreen();

        // Initialize board
        initBoard();

        // Start the game
        await startGame();

    } catch (error) {
        console.error('Error starting battle:', error);
        alert('Failed to start battle. Make sure AI players are running!');
    } finally {
        startBattleBtn.disabled = false;
        startBattleBtn.textContent = '🚀 Start Battle';
    }
}

// Start a new game
async function startGame() {
    try {
        newGameBtn.disabled = true;
        newGameBtn.textContent = 'Starting...';

        const response = await fetch('/api/start', {
            method: 'POST'
        });

        if (response.ok) {
            // Clear move history
            moveHistory.innerHTML = '';
            gameStatus.textContent = 'Game starting...';
            gameStatus.style.color = '#fff';

            // Start polling for updates
            startPolling();

            // Fetch initial state
            await fetchGameState();
        } else {
            alert('Failed to start game. Check that AI players are running!');
        }
    } catch (error) {
        console.error('Error starting game:', error);
        alert('Failed to start game. Make sure AI players are running!');
    } finally {
        setTimeout(() => {
            newGameBtn.disabled = false;
            newGameBtn.textContent = 'New Game';
        }, 2000);
    }
}

// Reset the game
async function resetGame() {
    try {
        stopPolling();
        const response = await fetch('/api/reset', {
            method: 'POST'
        });

        if (response.ok) {
            moveHistory.innerHTML = '';
            gameStatus.textContent = 'Ready to start';
            gameStatus.style.color = '#fff';
            moveCount.textContent = '0';
            player1Status.textContent = 'Waiting...';
            player2Status.textContent = 'Waiting...';

            const player1Card = document.querySelector('.player-card.player1');
            const player2Card = document.querySelector('.player-card.player2');

            if (player1Card) player1Card.classList.remove('active');
            if (player2Card) player2Card.classList.remove('active');

            await fetchGameState();
        }
    } catch (error) {
        console.error('Error resetting game:', error);
    }
}

// Event Listeners
startBattleBtn.addEventListener('click', startBattle);
newGameBtn.addEventListener('click', startGame);
resetBtn.addEventListener('click', resetGame);
backConfigBtn.addEventListener('click', () => {
    stopPolling();
    showConfigScreen();
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Show config screen by default
    showConfigScreen();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopPolling();
});
