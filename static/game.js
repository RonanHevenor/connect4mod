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
    moveDelay: 1.5,
    mode: 'single',
    numGames: 10,
    gameInterval: 3
};

// Tournament state
let tournamentState = {
    active: false,
    currentGame: 0,
    totalGames: 0,
    wins: {
        player1: 0,
        player2: 0,
        draws: 0
    }
};

// DOM Elements - Screens
const configScreen = document.getElementById('config-screen');
const gameScreen = document.getElementById('game-screen');
const tournamentScreen = document.getElementById('tournament-screen');

// DOM Elements - Config
const startBattleBtn = document.getElementById('start-battle-btn');
const player1UrlInput = document.getElementById('player1-url');
const player1NameInput = document.getElementById('player1-name');
const player1ColorInput = document.getElementById('player1-color');
const player2UrlInput = document.getElementById('player2-url');
const player2NameInput = document.getElementById('player2-name');
const player2ColorInput = document.getElementById('player2-color');
const moveDelayInput = document.getElementById('move-delay');
const modeRadios = document.querySelectorAll('input[name="game-mode"]');
const tournamentSettingsSection = document.getElementById('tournament-settings');
const numGamesInput = document.getElementById('num-games');
const gameIntervalInput = document.getElementById('game-interval');

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

// DOM Elements - Tournament Screen
const tournamentPlayer1Name = document.getElementById('tournament-player1-name');
const tournamentPlayer2Name = document.getElementById('tournament-player2-name');
const tournamentPlayer1Wins = document.getElementById('tournament-player1-wins');
const tournamentPlayer2Wins = document.getElementById('tournament-player2-wins');
const tournamentStatusText = document.getElementById('tournament-status-text');
const tournamentElectionLeft = document.getElementById('tournament-election-left');
const tournamentElectionRight = document.getElementById('tournament-election-right');
const tournamentElectionLeftPercent = document.getElementById('tournament-election-left-percent');
const tournamentElectionRightPercent = document.getElementById('tournament-election-right-percent');
const tournamentProgressText = document.getElementById('tournament-progress-text');
const tournamentBackBtn = document.getElementById('tournament-back-btn');
const ballPitCanvas = document.getElementById('ball-pit-canvas');

// Screen Management
function showConfigScreen() {
    configScreen.classList.add('active');
    gameScreen.classList.remove('active');
    tournamentScreen.classList.remove('active');
    stopPolling();
    stopBallPitPhysics();
}

function showGameScreen() {
    configScreen.classList.remove('active');
    gameScreen.classList.add('active');
    tournamentScreen.classList.remove('active');
    stopBallPitPhysics();
}

function showTournamentScreen() {
    configScreen.classList.remove('active');
    gameScreen.classList.remove('active');
    tournamentScreen.classList.add('active');
    initBallPitCanvas();
    startBallPitPhysics();
}

// ============================================================================
// BALL PIT PHYSICS SIMULATION
// ============================================================================

// Physics constants
const GRAVITY = 0.5;
const FRICTION = 0.99;
const BOUNCE_DAMPING = 0.8;
const BALL_RADIUS = 15;

// Physics state
let balls = [];
let ctx = null;
let canvasWidth = 0;
let canvasHeight = 0;
let physicsAnimationId = null;

// Ball class
class Ball {
    constructor(x, y, color) {
        this.x = x;
        this.y = y;
        this.vx = (Math.random() - 0.5) * 4; // Random horizontal velocity
        this.vy = 0; // Start with no vertical velocity
        this.radius = BALL_RADIUS;
        this.color = color;
    }

    update() {
        // Apply gravity
        this.vy += GRAVITY;

        // Apply friction
        this.vx *= FRICTION;
        this.vy *= FRICTION;

        // Update position
        this.x += this.vx;
        this.y += this.vy;

        // Wall collisions
        if (this.x - this.radius < 0) {
            this.x = this.radius;
            this.vx *= -BOUNCE_DAMPING;
        }
        if (this.x + this.radius > canvasWidth) {
            this.x = canvasWidth - this.radius;
            this.vx *= -BOUNCE_DAMPING;
        }

        // Floor collision
        if (this.y + this.radius > canvasHeight) {
            this.y = canvasHeight - this.radius;
            this.vy *= -BOUNCE_DAMPING;

            // Stop tiny bounces
            if (Math.abs(this.vy) < 0.5) {
                this.vy = 0;
            }
        }

        // Ceiling collision (shouldn't happen but just in case)
        if (this.y - this.radius < 0) {
            this.y = this.radius;
            this.vy *= -BOUNCE_DAMPING;
        }
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();

        // Add subtle shadow/depth
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.2)';
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}

// Check collision between two balls
function checkBallCollision(ball1, ball2) {
    const dx = ball2.x - ball1.x;
    const dy = ball2.y - ball1.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const minDistance = ball1.radius + ball2.radius;

    if (distance < minDistance) {
        // Collision detected - calculate response
        const angle = Math.atan2(dy, dx);
        const targetX = ball1.x + Math.cos(angle) * minDistance;
        const targetY = ball1.y + Math.sin(angle) * minDistance;

        // Separate balls
        const ax = (targetX - ball2.x) * 0.5;
        const ay = (targetY - ball2.y) * 0.5;

        ball1.x -= ax;
        ball1.y -= ay;
        ball2.x += ax;
        ball2.y += ay;

        // Exchange velocities (simplified elastic collision)
        const tempVx = ball1.vx;
        const tempVy = ball1.vy;
        ball1.vx = ball2.vx * BOUNCE_DAMPING;
        ball1.vy = ball2.vy * BOUNCE_DAMPING;
        ball2.vx = tempVx * BOUNCE_DAMPING;
        ball2.vy = tempVy * BOUNCE_DAMPING;
    }
}

// Initialize canvas
function initBallPitCanvas() {
    if (!ballPitCanvas) return;

    ctx = ballPitCanvas.getContext('2d');

    // Set canvas size to match container
    const container = ballPitCanvas.parentElement;
    canvasWidth = container.clientWidth;
    canvasHeight = container.clientHeight;
    ballPitCanvas.width = canvasWidth;
    ballPitCanvas.height = canvasHeight;

    // Clear balls array
    balls = [];
}

// Physics update loop
function updatePhysics() {
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvasWidth, canvasHeight);

    // Update all balls
    balls.forEach(ball => ball.update());

    // Check ball-to-ball collisions
    for (let i = 0; i < balls.length; i++) {
        for (let j = i + 1; j < balls.length; j++) {
            checkBallCollision(balls[i], balls[j]);
        }
    }

    // Draw all balls
    balls.forEach(ball => ball.draw());

    // Continue animation loop
    physicsAnimationId = requestAnimationFrame(updatePhysics);
}

// Start physics simulation
function startBallPitPhysics() {
    if (!physicsAnimationId) {
        physicsAnimationId = requestAnimationFrame(updatePhysics);
    }
}

// Stop physics simulation
function stopBallPitPhysics() {
    if (physicsAnimationId) {
        cancelAnimationFrame(physicsAnimationId);
        physicsAnimationId = null;
    }
}

// Add a ball to the pit
function addBallToPitCanvas(player) {
    if (!ctx) return;

    const color = player === 1 ? config.player1.color : config.player2.color;

    // Spawn ball at random x position near top
    const x = canvasWidth * 0.3 + Math.random() * canvasWidth * 0.4;
    const y = BALL_RADIUS;

    const ball = new Ball(x, y, color);
    balls.push(ball);
}

// Handle canvas resize
window.addEventListener('resize', () => {
    if (tournamentScreen.classList.contains('active')) {
        initBallPitCanvas();
    }
});

// Save configuration from form
function saveConfig() {
    config.player1.name = player1NameInput.value;
    config.player1.url = player1UrlInput.value;
    config.player1.color = player1ColorInput.value;

    config.player2.name = player2NameInput.value;
    config.player2.url = player2UrlInput.value;
    config.player2.color = player2ColorInput.value;

    config.moveDelay = parseFloat(moveDelayInput.value);

    // Get mode
    const selectedMode = document.querySelector('input[name="game-mode"]:checked').value;
    config.mode = selectedMode;

    // Get tournament settings if tournament mode
    if (selectedMode === 'tournament') {
        config.numGames = parseInt(numGamesInput.value);
        config.gameInterval = parseFloat(gameIntervalInput.value);
    }

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
        .bar-left { background: ${config.player1.color} !important; }
        .bar-right { background: ${config.player2.color} !important; }
    `;
    document.head.appendChild(style);
}

// Tournament Functions
function initTournament() {
    tournamentState.active = true;
    tournamentState.currentGame = 0;
    tournamentState.totalGames = config.numGames;
    tournamentState.wins.player1 = 0;
    tournamentState.wins.player2 = 0;
    tournamentState.wins.draws = 0;

    // Update tournament screen with player names
    tournamentPlayer1Name.textContent = config.player1.name;
    tournamentPlayer2Name.textContent = config.player2.name;

    // Reset win counts
    tournamentPlayer1Wins.textContent = '0';
    tournamentPlayer2Wins.textContent = '0';

    // Reset status
    tournamentStatusText.textContent = 'Preparing tournament...';

    // Reset election bar
    updateTournamentElectionBar();
    updateTournamentProgressText();
}

// Update tournament screen election bar
function updateTournamentElectionBar() {
    const total = tournamentState.wins.player1 + tournamentState.wins.player2 + tournamentState.wins.draws;
    if (total === 0) {
        tournamentElectionLeft.style.width = '0%';
        tournamentElectionRight.style.width = '0%';
        tournamentElectionLeftPercent.textContent = '0%';
        tournamentElectionRightPercent.textContent = '0%';
        return;
    }

    const player1Percent = (tournamentState.wins.player1 / total) * 100;
    const player2Percent = (tournamentState.wins.player2 / total) * 100;

    tournamentElectionLeft.style.width = player1Percent + '%';
    tournamentElectionRight.style.width = player2Percent + '%';
    tournamentElectionLeftPercent.textContent = Math.round(player1Percent) + '%';
    tournamentElectionRightPercent.textContent = Math.round(player2Percent) + '%';

    // Update win count displays (just the numbers)
    tournamentPlayer1Wins.textContent = tournamentState.wins.player1.toString();
    tournamentPlayer2Wins.textContent = tournamentState.wins.player2.toString();
}

function updateTournamentProgressText() {
    tournamentProgressText.textContent = `Game ${tournamentState.currentGame} of ${tournamentState.totalGames}`;
}

async function runTournament() {
    initTournament();

    for (let i = 1; i <= config.numGames; i++) {
        tournamentState.currentGame = i;
        updateTournamentProgressText();
        tournamentStatusText.textContent = `Game ${i} in progress...`;

        // Start game
        await startGame();

        // Wait for game to complete
        await waitForGameComplete();

        // Record result and add ball to pit
        if (gameState.winner === 1) {
            tournamentState.wins.player1++;
            addBallToPitCanvas(1);
        } else if (gameState.winner === 2) {
            tournamentState.wins.player2++;
            addBallToPitCanvas(2);
        } else {
            tournamentState.wins.draws++;
            // For draws, could add a different colored ball or skip
        }

        // Update election bar
        updateTournamentElectionBar();

        // Wait interval before next game (except on last game)
        if (i < config.numGames) {
            tournamentStatusText.textContent = `Next game in ${config.gameInterval} seconds...`;
            await new Promise(resolve => setTimeout(resolve, config.gameInterval * 1000));
        }
    }

    // Tournament complete
    tournamentState.active = false;
    tournamentStatusText.textContent = 'Tournament Complete!';
}

function waitForGameComplete() {
    return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
            if (gameState && gameState.game_over) {
                clearInterval(checkInterval);
                resolve();
            }
        }, 500);
    });
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
            gameStatus.textContent = `${winnerName} wins`;
            gameStatus.style.color = '#333';
        } else {
            gameStatus.textContent = 'Draw';
            gameStatus.style.color = '#333';
        }
        stopPolling();
    } else {
        const currentPlayerName = state.current_player === 1 ? config.player1.name : config.player2.name;
        gameStatus.textContent = `${currentPlayerName}'s turn`;
        gameStatus.style.color = '#333';
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
    const player1Info = document.querySelector('.scoreboard .player-info:first-child');
    const player2Info = document.querySelector('.scoreboard .player-info:last-child');

    if (!player1Info || !player2Info) return;

    // Remove active class
    player1Info.classList.remove('active');
    player2Info.classList.remove('active');

    if (!state.game_over) {
        if (state.current_player === 1) {
            player1Info.classList.add('active');
            player1Status.textContent = 'Thinking';
            player2Status.textContent = 'Waiting';
        } else {
            player2Info.classList.add('active');
            player1Status.textContent = 'Waiting';
            player2Status.textContent = 'Thinking';
        }
    } else {
        if (state.winner === 1) {
            player1Status.textContent = 'Winner';
            player2Status.textContent = 'Lost';
        } else if (state.winner === 2) {
            player1Status.textContent = 'Lost';
            player2Status.textContent = 'Winner';
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
        startBattleBtn.textContent = 'Initializing...';

        // Save configuration
        saveConfig();

        // Send config to server
        const configOk = await sendConfigToServer();
        if (!configOk) {
            alert('Failed to configure server');
            return;
        }

        // Switch to appropriate screen based on mode
        if (config.mode === 'tournament') {
            showTournamentScreen();
            await runTournament();
        } else {
            showGameScreen();
            initBoard();
            await startGame();
        }

    } catch (error) {
        console.error('Error starting battle:', error);
        alert('Failed to start battle. Make sure AI players are running.');
    } finally {
        startBattleBtn.disabled = false;
        startBattleBtn.textContent = 'Start Battle';
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
            gameStatus.textContent = 'Starting';
            gameStatus.style.color = '#333';

            // Start polling for updates
            startPolling();

            // Fetch initial state
            await fetchGameState();
        } else {
            alert('Failed to start game. Check that AI players are running.');
        }
    } catch (error) {
        console.error('Error starting game:', error);
        alert('Failed to start game. Make sure AI players are running.');
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
            gameStatus.textContent = 'Ready';
            gameStatus.style.color = '#333';
            moveCount.textContent = '0';
            player1Status.textContent = 'Waiting';
            player2Status.textContent = 'Waiting';

            const player1Info = document.querySelector('.scoreboard .player-info:first-child');
            const player2Info = document.querySelector('.scoreboard .player-info:last-child');

            if (player1Info) player1Info.classList.remove('active');
            if (player2Info) player2Info.classList.remove('active');

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
tournamentBackBtn.addEventListener('click', () => {
    stopPolling();
    showConfigScreen();
});

// Mode selection toggle
modeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'tournament') {
            tournamentSettingsSection.style.display = 'block';
        } else {
            tournamentSettingsSection.style.display = 'none';
        }
    });
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
