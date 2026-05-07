const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

const _params        = new URLSearchParams(window.location.search);
let currentUserColor = _params.get('color') || 'white';
let startFen         = _params.get('fen')   || STARTING_FEN;
let currentFen       = startFen;
let chessground      = null;
let acceptingMoves   = false;
let gameOver         = false;
let moves            = [];   // [{num, userSan, engineSan}]

// ── Eval bar state ────────────────────────────────────────────────────────────
let evalVisible = false;
let lastEvalCp   = null;
let lastEvalMate = null;

function toggleEvalBar() {
    evalVisible = !evalVisible;
    document.getElementById('eval-wrap').classList.toggle('visible', evalVisible);
    document.getElementById('btn-eval').classList.toggle('active', evalVisible);
    if (evalVisible) renderEvalBar(lastEvalCp, lastEvalMate);
}

function updateEvalBar(cp, mate) {
    lastEvalCp   = cp;
    lastEvalMate = mate;
    if (evalVisible) renderEvalBar(cp, mate);
}

function renderEvalBar(cp, mate) {
    let blackGrow, whiteGrow, scoreText;
    if (mate !== null) {
        blackGrow = mate > 0 ? 0 : 100;
        whiteGrow = 100 - blackGrow;
        scoreText = mate > 0 ? `M${mate}` : `-M${Math.abs(mate)}`;
    } else if (cp !== null) {
        const capped = Math.max(-1000, Math.min(1000, cp));
        whiteGrow = 50 + (capped / 1000) * 50;
        blackGrow = 100 - whiteGrow;
        const pawns = (Math.abs(cp) / 100).toFixed(1);
        scoreText = cp >= 0 ? `+${pawns}` : `-${pawns}`;
    } else {
        blackGrow = whiteGrow = 50;
        scoreText = '0.0';
    }
    document.getElementById('eval-black').style.flexGrow = blackGrow;
    document.getElementById('eval-white').style.flexGrow = whiteGrow;
    document.getElementById('eval-score').textContent    = scoreText;
}

function resetEvalBar() {
    lastEvalCp   = null;
    lastEvalMate = null;
    renderEvalBar(null, null);
}

// ── Setup mode state ──────────────────────────────────────────────────────────
let setupMode   = false;
let setupTool   = null;    // { role, color } or 'erase'
let setupTurn   = 'w';     // 'w' | 'b'
let setupPieces = new Map();

const PIECE_ROLES  = ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn'];
const ROLE_LETTERS = { king:'K', queen:'Q', rook:'R', bishop:'B', knight:'N', pawn:'P' };
const ROLE_TO_FEN  = { king:'k', queen:'q', rook:'r', bishop:'b', knight:'n', pawn:'p' };
const FEN_TO_ROLE  = Object.fromEntries(Object.entries(ROLE_TO_FEN).map(([k,v]) => [v, k]));

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
    buildPalette();
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

async function startGame(fenOverride) {
    if (setupMode) exitSetupMode(false);

    const fenInputVal = document.getElementById('fen-input')?.value.trim();
    startFen   = fenOverride || fenInputVal || _params.get('fen') || STARTING_FEN;
    currentFen = startFen;
    gameOver       = false;
    acceptingMoves = false;
    moves          = [];
    renderMoveHistory();
    resetEvalBar();
    chessground.set({ fen: startFen, orientation: currentUserColor });

    if (currentUserColor === 'white') {
        const [legalResp, evalResp] = await Promise.all([
            fetch(`/legal_moves?fen=${encodeURIComponent(startFen)}`),
            fetch(`/eval_fen?fen=${encodeURIComponent(startFen)}`),
        ]);
        const [legalData, evalData] = await Promise.all([legalResp.json(), evalResp.json()]);
        setDests(legalData.dests);
        updateEvalBar(evalData.centipawns, evalData.mate);
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

async function shuffleBoard() {
    const resp = await fetch('/shuffle_fen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fen: startFen }),
    });
    const data = await resp.json();
    if (data.fen) startGame(data.fen);
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
        const resp = await fetch(`/legal_moves?fen=${encodeURIComponent(currentFen)}`);
        const legal = await resp.json();
        chessground.set({ fen: currentFen });
        setDests(legal.dests);
        setStatus('Illegal move — try again.');
        acceptingMoves = true;
        return;
    }

    currentFen = data.after_user_fen;
    if (isPromotion(orig, dest)) chessground.set({ fen: currentFen });
    applyEngineMove(data, data.user_san);
}

function applyEngineMove(data, userSan) {
    const moveNum = Math.floor(moves.length) + 1;
    moves.push({ num: moveNum, userSan, engineSan: null });

    updateEvalBar(data.engine_centipawns, data.engine_mate);

    if (!data.engine_move) {
        chessground.set({ fen: data.final_fen, movable: { color: 'none' } });
        moves[moves.length - 1].engineSan = '–';
        renderMoveHistory();
        setStatus(resultLabel(data.result), 'over');
        gameOver = true;
        return;
    }

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
        },
        draggable: { enabled: true },
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

// ── Board setup mode ──────────────────────────────────────────────────────────
function buildPalette() {
    const makeBtn = (role, color) => {
        const btn = document.createElement('div');
        btn.className = `palette-btn piece-${color}`;
        btn.textContent = color === 'white'
            ? ROLE_LETTERS[role]
            : ROLE_LETTERS[role].toLowerCase();
        btn.title = `${color[0].toUpperCase() + color.slice(1)} ${role}`;
        btn.addEventListener('click', () => selectTool(role, color));
        btn.dataset.role  = role;
        btn.dataset.color = color;
        return btn;
    };

    const wp = document.getElementById('palette-white');
    const bp = document.getElementById('palette-black');
    PIECE_ROLES.forEach(r => {
        wp.appendChild(makeBtn(r, 'white'));
        bp.appendChild(makeBtn(r, 'black'));
    });
}

function selectTool(role, color) {
    // Deselect all palette buttons
    document.querySelectorAll('.palette-btn').forEach(b => b.classList.remove('selected'));

    if (role === 'erase') {
        setupTool = 'erase';
        document.getElementById('tool-erase').classList.add('selected');
    } else {
        setupTool = { role, color };
        const btn = document.querySelector(`.palette-btn[data-role="${role}"][data-color="${color}"]`);
        if (btn) btn.classList.add('selected');
    }
}

function setSetupTurn(t) {
    setupTurn = t;
    document.getElementById('setup-turn-w').className = t === 'w' ? 'active' : '';
    document.getElementById('setup-turn-b').className = t === 'b' ? 'active' : '';
}

function toggleSetupMode() {
    if (setupMode) exitSetupMode(true);
    else enterSetupMode();
}

function enterSetupMode() {
    setupMode = true;
    acceptingMoves = false;

    // Snapshot current board as the starting point for editing
    setupPieces = fenToPiecesMap(currentFen);
    setupTurn   = currentFen.split(' ')[1] || 'w';
    setSetupTurn(setupTurn);

    // Lock chessground movement — overlay handles all interaction
    chessground.set({
        movable: { free: false, dests: new Map() },
        draggable: { enabled: false },
    });

    buildSetupOverlay();
    document.getElementById('setup-overlay').classList.add('active');
    document.getElementById('setup-panel').style.display = 'block';
    document.getElementById('btn-setup').classList.add('setup-active');
    setStatus('Setup mode — place pieces, then click Start Game', '');
}

function exitSetupMode(startAfter = true) {
    setupMode = false;
    document.getElementById('setup-overlay').classList.remove('active');
    document.getElementById('setup-panel').style.display = 'none';
    document.getElementById('btn-setup').classList.remove('setup-active');
    setupTool = null;
    document.querySelectorAll('.palette-btn').forEach(b => b.classList.remove('selected'));

    if (startAfter) {
        const fen = buildSetupFen();
        document.getElementById('fen-input').value = fen;
        startGame(fen);
    }
}

function buildSetupOverlay() {
    const overlay = document.getElementById('setup-overlay');
    overlay.innerHTML = '';
    const orientation = chessground.state.orientation;
    const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const RANKS = ['1', '2', '3', '4', '5', '6', '7', '8'];

    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const sq = orientation === 'white'
                ? FILES[col] + RANKS[7 - row]
                : FILES[7 - col] + RANKS[row];
            const cell = document.createElement('div');
            cell.className = 'setup-cell';
            cell.dataset.square = sq;
            cell.addEventListener('click', () => handleSetupClick(sq, cell));
            overlay.appendChild(cell);
        }
    }
}

function handleSetupClick(sq, cellEl) {
    if (!setupTool) return;

    if (setupTool === 'erase') {
        setupPieces.delete(sq);
        flash(cellEl, 'flash-erase');
    } else {
        const existing = setupPieces.get(sq);
        if (existing && existing.role === setupTool.role && existing.color === setupTool.color) {
            // Same piece clicked again → remove (toggle off)
            setupPieces.delete(sq);
            flash(cellEl, 'flash-erase');
        } else {
            setupPieces.set(sq, { role: setupTool.role, color: setupTool.color });
            flash(cellEl, 'flash-place');
        }
    }

    chessground.set({ pieces: new Map(setupPieces) });
}

function flash(el, cls) {
    el.classList.add(cls);
    setTimeout(() => el.classList.remove(cls), 300);
}

function clearSetupBoard() {
    setupPieces.clear();
    chessground.set({ pieces: new Map() });
}

function resetSetupToStart() {
    setupPieces = fenToPiecesMap(STARTING_FEN);
    setSetupTurn('w');
    chessground.set({ pieces: new Map(setupPieces) });
}

function buildSetupFen() {
    const placement = piecesMapToFen(setupPieces);
    const castling  = computeCastling(setupPieces);
    return `${placement} ${setupTurn} ${castling} - 0 1`;
}

// ── FEN utilities ─────────────────────────────────────────────────────────────
function fenToPiecesMap(fen) {
    const placement = fen.split(' ')[0];
    const pieces    = new Map();
    const rows      = placement.split('/');

    for (let rankIdx = 0; rankIdx < 8; rankIdx++) {
        const rank = 8 - rankIdx;
        let fileIdx = 0;
        for (const ch of rows[rankIdx]) {
            if (/\d/.test(ch)) {
                fileIdx += parseInt(ch);
            } else {
                const sq = 'abcdefgh'[fileIdx] + rank;
                pieces.set(sq, {
                    role:  FEN_TO_ROLE[ch.toLowerCase()],
                    color: ch === ch.toUpperCase() ? 'white' : 'black',
                });
                fileIdx++;
            }
        }
    }
    return pieces;
}

function piecesMapToFen(pieces) {
    const ranks = [];
    for (let rank = 8; rank >= 1; rank--) {
        let row = '', empty = 0;
        for (const file of 'abcdefgh') {
            const piece = pieces.get(file + rank);
            if (piece) {
                if (empty) { row += empty; empty = 0; }
                const ch = ROLE_TO_FEN[piece.role];
                row += piece.color === 'white' ? ch.toUpperCase() : ch;
            } else {
                empty++;
            }
        }
        if (empty) row += empty;
        ranks.push(row);
    }
    return ranks.join('/');
}

function computeCastling(pieces) {
    let c = '';
    const wk = pieces.get('e1');
    if (wk?.role === 'king' && wk?.color === 'white') {
        if (pieces.get('h1')?.role === 'rook' && pieces.get('h1')?.color === 'white') c += 'K';
        if (pieces.get('a1')?.role === 'rook' && pieces.get('a1')?.color === 'white') c += 'Q';
    }
    const bk = pieces.get('e8');
    if (bk?.role === 'king' && bk?.color === 'black') {
        if (pieces.get('h8')?.role === 'rook' && pieces.get('h8')?.color === 'black') c += 'k';
        if (pieces.get('a8')?.role === 'rook' && pieces.get('a8')?.color === 'black') c += 'q';
    }
    return c || '-';
}
