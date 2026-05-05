const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

const _params        = new URLSearchParams(window.location.search);
let currentUserColor = _params.get('color') || 'white';
let startFen         = _params.get('fen')   || STARTING_FEN;
let currentFen       = startFen;
let chessground      = null;
let acceptingMoves   = false;
let gameOver         = false;
let moves            = [];   // [{num, userSan, engineSan}]

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    chessground = Chessground(document.getElementById('chessground_board'), {
        orientation: currentUserColor,
        movable: {
            free: false,
            showDests: true,
            events: { after: onUserMove }
        }
    });
    setupColorUI();
    startGame();
});

function setupColorUI() {
    const engineColor = currentUserColor === 'white' ? 'black' : 'white';
    document.getElementById('engine-dot').className = `player-dot ${engineColor}-dot`;
    document.getElementById('user-dot').className   = `player-dot ${currentUserColor}-dot`;
    document.getElementById('btn-white').className  = currentUserColor === 'white' ? 'active' : '';
    document.getElementById('btn-black').className  = currentUserColor === 'black' ? 'active' : '';
}

async function startGame() {
    const fenInputVal = document.getElementById('fen-input')?.value.trim();
    startFen   = fenInputVal || _params.get('fen') || STARTING_FEN;
    currentFen = startFen;
    gameOver       = false;
    acceptingMoves = false;
    moves          = [];
    renderMoveHistory();
    chessground.set({ fen: startFen, orientation: currentUserColor });

    if (currentUserColor === 'white') {
        const resp = await fetch(`/legal_moves?fen=${encodeURIComponent(startFen)}`);
        const data = await resp.json();
        setDests(data.dests);
        setStatus('Your turn');
        acceptingMoves = true;
    } else {
        setStatus('Engine thinking…', 'thinking');
        const data = await callPlayMove('');
        applyEngineMove(data, null);
    }
}

function newGame(color) {
    currentUserColor = color;
    setupColorUI();
    startGame();
}

// ── Move handling ─────────────────────────────────────────────────────────────
async function onUserMove(orig, dest) {
    if (!acceptingMoves || gameOver) return;
    acceptingMoves = false;

    let uci = orig + dest;
    if (isPromotion(orig, dest)) uci += 'q';

    setStatus('Engine thinking…', 'thinking');
    const data = await callPlayMove(uci);

    if (data.error) {
        // Illegal — reset board
        const resp = await fetch(`/legal_moves?fen=${encodeURIComponent(currentFen)}`);
        const legal = await resp.json();
        chessground.set({ fen: currentFen });
        setDests(legal.dests);
        setStatus('Illegal move — try again.');
        acceptingMoves = true;
        return;
    }

    currentFen = data.after_user_fen;
    applyEngineMove(data, data.user_san);
}

function applyEngineMove(data, userSan) {
    // Record the move pair
    const moveNum = Math.floor(moves.length) + 1;
    moves.push({ num: moveNum, userSan, engineSan: null });

    if (!data.engine_move) {
        // Game over after user's move
        chessground.set({ fen: data.final_fen, movable: { color: 'none' } });
        moves[moves.length - 1].engineSan = '–';
        renderMoveHistory();
        setStatus(resultLabel(data.result), 'over');
        gameOver = true;
        return;
    }

    // Apply engine move after short delay
    setTimeout(() => {
        const e = data.engine_move;
        chessground.move(e.substring(0, 2), e.substring(2, 4));
        chessground.set({ turnColor: currentUserColor });
        currentFen = data.final_fen;
        moves[moves.length - 1].engineSan = data.engine_san || e;
        renderMoveHistory();

        if (data.game_over) {
            chessground.set({ movable: { color: 'none' } });
            setStatus(resultLabel(data.result), 'over');
            gameOver = true;
            return;
        }

        setDests(data.dests);
        setStatus(data.is_check ? 'Check!' : 'Your turn', data.is_check ? 'check' : '');
        acceptingMoves = true;
    }, 500);
}

// ── Helpers ───────────────────────────────────────────────────────────────────
async function callPlayMove(userMove) {
    const resp = await fetch('/play_move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fen: currentFen, move: userMove })
    });
    return resp.json();
}

function setDests(destsObj) {
    chessground.set({
        turnColor: currentUserColor,
        movable: {
            color:     currentUserColor,
            free:      false,
            showDests: true,
            dests:     new Map(Object.entries(destsObj || {})),
            events:    { after: onUserMove }
        }
    });
}

function isPromotion(orig, dest) {
    const fromRank = orig[1], toRank = dest[1];
    return (currentUserColor === 'white' && fromRank === '7' && toRank === '8') ||
           (currentUserColor === 'black' && fromRank === '2' && toRank === '1');
}

function setStatus(msg, cls = '') {
    const el = document.getElementById('status');
    el.textContent = msg;
    el.className   = cls;
}

function resultLabel(result) {
    if (!result) return 'Game over';
    if (result === '1-0') return currentUserColor === 'white' ? 'You win! ♟' : 'Stockfish wins';
    if (result === '0-1') return currentUserColor === 'black' ? 'You win! ♟' : 'Stockfish wins';
    return 'Draw';
}

function renderMoveHistory() {
    const el = document.getElementById('move-history');
    if (!moves.length) { el.innerHTML = ''; return; }

    el.innerHTML = moves.map(m => {
        const userCls   = currentUserColor === 'white' ? 'user'   : 'engine';
        const engineCls = currentUserColor === 'white' ? 'engine' : 'user';
        const col1 = m.userSan   || '…';
        const col2 = m.engineSan || '…';
        return `<div class="move-pair">
            <span class="move-num">${m.num}.</span>
            <span class="move-cell ${userCls}">${col1}</span>
            <span class="move-cell ${engineCls}">${col2}</span>
        </div>`;
    }).join('');
    el.scrollTop = el.scrollHeight;
}
