// Connect 4 AI Battle - Frontend JavaScript

let gameState = null;
let pollingInterval = null;

// DOM Elements
const gameBoard = document.getElementById('game-board');
const startBtn = document.getElementById('start-btn');
const resetBtn = document.getElementById('reset-btn');
const gameStatus = document.getElementById('game-status');
const moveCount = document.getElementById('move-count');
const moveHistory = document.getElementById('move-history');
const player1Status = document.getElementById('player1-status');
const player2Status = document.getElementById('player2-status');

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
            const winnerName = state.winner === 1 ? 'Random AI' : 'Minimax AI';
            gameStatus.textContent = `🎉 ${winnerName} Wins!`;
            gameStatus.style.color = state.winner === 1 ? '#FF6B6B' : '#4ECDC4';
        } else {
            gameStatus.textContent = '🤝 Draw!';
            gameStatus.style.color = '#FFD700';
        }
        stopPolling();
    } else {
        const currentPlayerName = state.current_player === 1 ? 'Random AI' : 'Minimax AI';
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
        const playerName = move.player === 1 ? 'Random' : 'Minimax';
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

// Start a new game
async function startGame() {
    try {
        startBtn.disabled = true;
        startBtn.textContent = 'Starting...';

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
        }
    } catch (error) {
        console.error('Error starting game:', error);
        alert('Failed to start game. Make sure AI players are running!');
    } finally {
        setTimeout(() => {
            startBtn.disabled = false;
            startBtn.textContent = 'Start New Game';
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

            // Remove active classes
            document.querySelector('.player-card.player1').classList.remove('active');
            document.querySelector('.player-card.player2').classList.remove('active');

            await fetchGameState();
        }
    } catch (error) {
        console.error('Error resetting game:', error);
    }
}

// Event Listeners
startBtn.addEventListener('click', startGame);
resetBtn.addEventListener('click', resetGame);

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initBoard();
    fetchGameState();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopPolling();
});
