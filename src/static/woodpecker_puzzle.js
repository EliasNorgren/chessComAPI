// ── State ────────────────────────────────────────────────────────────────────
const params     = new URLSearchParams(window.location.search);
const USER       = params.get('user') || '';
const SET_ID     = parseInt(params.get('set_id'));

let attemptId        = null;
let attemptNumber    = null;
let currentPuzzle    = null;
let puzzleMoves      = [];   // full UCI move list from Lichess
let expectedMoveIdx  = 1;    // user plays at odd indices; 0 is trigger, 2,4,.. are opponent replies
let userColor        = 'white';
let acceptingMoves   = false;
let puzzleStartTime  = null;
let timerInterval    = null;
let chessground      = null;
let totalSeconds     = 0;

function setMovable(color) {
    chessground.set({ movable: { color, free: true, events: { after: onUserMove } } });
}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    if (!USER || !SET_ID) {
        showError('user and set_id are required in the URL.');
        return;
    }

    chessground = Chessground(document.getElementById('chessground_board'), {
        movable: {
            free: true,
            color: 'none',
            events: { after: onUserMove }
        }
    });

    // Build button row
    const row = document.getElementById('btn-row');
    const makeBtn = (text, cls, fn) => {
        const b = document.createElement('button');
        b.textContent = text;
        if (cls) b.className = cls;
        b.onclick = fn;
        row.appendChild(b);
        return b;
    };
    makeBtn('Give Up', '', giveUp);

    // Start or resume attempt
    const resp = await fetch(`/woodpecker/api/set/${SET_ID}/start`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ user: USER })
    });
    const data = await resp.json();
    if (data.error) { showError(data.error); return; }

    attemptId     = data.attempt_id;
    attemptNumber = data.attempt_number;

    loadNextPuzzle();
});

// ── Puzzle loading ────────────────────────────────────────────────────────────
async function loadNextPuzzle() {
    acceptingMoves = false;
    stopTimer();
    showFeedback('');

    const resp = await fetch(`/woodpecker/api/attempt/${attemptId}/next?set_id=${SET_ID}`);
    const data = await resp.json();

    if (data.done) {
        await fetch(`/woodpecker/api/attempt/${attemptId}/complete`, { method: 'POST' });
        showCompletion();
        return;
    }

    currentPuzzle   = data;
    puzzleMoves     = data.moves;
    expectedMoveIdx = 1;

    // Solver is the side that does NOT play the trigger move
    const fenActiveColor = data.fen.split(' ')[1]; // 'w' or 'b'
    userColor = fenActiveColor === 'w' ? 'black' : 'white';

    updateProgressUI(data.position, data.total, data.rating);

    chessground.set({
        fen:         data.fen,
        orientation: userColor,
        turnColor:   fenActiveColor === 'w' ? 'white' : 'black',
    });
    setMovable('none');

    // Animate trigger move after a short pause
    setTimeout(playTriggerMove, 600);
}

function playTriggerMove() {
    const trigger = puzzleMoves[0];
    chessground.move(trigger.substring(0, 2), trigger.substring(2, 4));
    chessground.set({ turnColor: userColor });
    setMovable(userColor);
    startTimer();
    acceptingMoves = true;
}

// ── Move handling ─────────────────────────────────────────────────────────────
function onUserMove(orig, dest) {
    if (!acceptingMoves) return;

    let moveUci = orig + dest;
    const expected = puzzleMoves[expectedMoveIdx];
    if (!expected) return;

    // Handle pawn promotion: take piece letter from the expected move
    if (expected.length === 5 && expected.startsWith(moveUci)) {
        moveUci += expected[4];
    }

    if (moveUci !== expected) {
        handleWrongMove();
        return;
    }

    // Correct — check if there's an opponent reply
    const opponentIdx = expectedMoveIdx + 1;
    if (opponentIdx >= puzzleMoves.length) {
        puzzleSolved();
        return;
    }

    // Play opponent reply, then wait for next user move
    acceptingMoves = false;
    setMovable('none');
    setTimeout(() => {
        const opp = puzzleMoves[opponentIdx];
        chessground.move(opp.substring(0, 2), opp.substring(2, 4));
        chessground.set({ turnColor: userColor });
        expectedMoveIdx = opponentIdx + 1;
        if (expectedMoveIdx >= puzzleMoves.length) {
            puzzleSolved();
        } else {
            setMovable(userColor);
            acceptingMoves = true;
        }
    }, 500);
}

function handleWrongMove() {
    acceptingMoves = false;
    showFeedback('Wrong — try again.', false);
    // Reset to pre-trigger FEN, then replay trigger
    chessground.set({ fen: currentPuzzle.fen });
    setMovable('none');
    setTimeout(() => {
        const trigger = puzzleMoves[0];
        chessground.move(trigger.substring(0, 2), trigger.substring(2, 4));
        chessground.set({ turnColor: userColor });
        expectedMoveIdx = 1;
        setMovable(userColor);
        acceptingMoves  = true;
    }, 400);
}

// ── Puzzle outcome ────────────────────────────────────────────────────────────
async function puzzleSolved() {
    const elapsed = stopTimer();
    acceptingMoves = false;
    showFeedback('Correct!', true);

    await submitResult(true, elapsed);
    setTimeout(loadNextPuzzle, 700);
}

async function giveUp() {
    const elapsed = stopTimer();
    acceptingMoves = false;
    await submitResult(false, elapsed);
    showFeedback('Skipped.', false);
    setTimeout(loadNextPuzzle, 600);
}

async function submitResult(solved, elapsed) {
    if (!currentPuzzle) return;
    totalSeconds += elapsed;
    const el = document.getElementById('total-val');
    if (el) el.textContent = fmtSeconds(Math.round(totalSeconds));
    await fetch(`/woodpecker/api/attempt/${attemptId}/result`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            set_puzzle_id:     currentPuzzle.set_puzzle_id,
            solved,
            time_taken_seconds: elapsed
        })
    });
}

// ── Completion ────────────────────────────────────────────────────────────────
async function showCompletion() {
    document.getElementById('puzzle-info-card').style.display = 'none';
    document.getElementById('btn-row').innerHTML = '';
    document.getElementById('feedback').textContent = '';

    const resp = await fetch(`/woodpecker/api/set/${SET_ID}/stats`);
    const stats = await resp.json();

    const screen = document.getElementById('completion-screen');
    screen.style.display = '';

    const rows = stats.attempts.map(a => {
        const isCurrent = a.attempt_number === attemptNumber;
        return `<div class="attempt-row${isCurrent ? ' current' : ''}">
            <span>Attempt #${a.attempt_number}</span>
            <span>${fmtSeconds(a.duration_seconds)}</span>
        </div>`;
    }).join('');

    screen.innerHTML = `
        <div class="completion-header">Set complete — Attempt #${attemptNumber}</div>
        ${rows}
        <div style="padding:0.75em 1em;">
            <button onclick="window.location.href='/woodpecker/puzzle?set_id=${SET_ID}&user=${encodeURIComponent(USER)}'"
                style="width:100%;font-family:inherit;cursor:pointer;border-radius:8px;padding:0.55em;background:#2e4a2e;border:1px solid #3d6b3d;color:#81b64c;font-size:0.9em;">
                Start Next Attempt
            </button>
        </div>`;

    document.getElementById('header-meta').textContent = '';
}

// ── Timer ─────────────────────────────────────────────────────────────────────
function startTimer() {
    puzzleStartTime = Date.now();
    timerInterval = setInterval(() => {
        const el = document.getElementById('timer-val');
        if (el) el.textContent = ((Date.now() - puzzleStartTime) / 1000).toFixed(1) + 's';
    }, 100);
}

function stopTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
    const elapsed = puzzleStartTime ? (Date.now() - puzzleStartTime) / 1000 : 0;
    puzzleStartTime = null;
    return elapsed;
}

// ── UI helpers ────────────────────────────────────────────────────────────────
function updateProgressUI(position, total, rating) {
    const pct = ((position - 1) / total * 100).toFixed(1);
    document.getElementById('progress-bar').style.width = pct + '%';
    document.getElementById('header-meta').textContent =
        `Attempt #${attemptNumber} · Puzzle ${position} / ${total}`;

    document.getElementById('stat-grid').innerHTML = `
        <div class="stat-cell">
            <div class="stat-label">Progress</div>
            <div class="stat-value">${position} / ${total}</div>
        </div>
        <div class="stat-cell">
            <div class="stat-label">Rating</div>
            <div class="stat-value">${rating}</div>
        </div>
        <div class="stat-cell">
            <div class="stat-label">Time</div>
            <div class="stat-value"><span id="timer-val">0.0s</span></div>
        </div>
        <div class="stat-cell">
            <div class="stat-label">Total</div>
            <div class="stat-value"><span id="total-val">${fmtSeconds(Math.round(totalSeconds))}</span></div>
        </div>`;
}

function showFeedback(msg, success) {
    const el = document.getElementById('feedback');
    el.textContent = msg;
    el.style.color = success ? '#81b64c' : '#fa412d';
}

function showError(msg) {
    document.getElementById('error-message').textContent = msg;
}

function fmtSeconds(s) {
    if (s == null) return '–';
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${String(sec).padStart(2, '0')}`;
}
