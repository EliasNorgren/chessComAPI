document.addEventListener('DOMContentLoaded', function () {
    const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const RANKS = ['1', '2', '3', '4', '5', '6', '7', '8'];
    const ALL_SQUARES = FILES.flatMap(f => RANKS.map(r => f + r));

    let orientation = 'white';
    let currentSquare = null;
    let locked = false;
    let correct = 0;
    let total = 0;
    let streak = 0;
    let bestStreak = 0;

    const boardEl = document.getElementById('chessground_board');
    const overlayEl = document.getElementById('click-overlay');
    const promptEl = document.getElementById('prompt-square');
    const feedbackEl = document.getElementById('feedback');

    const cg = Chessground(boardEl, {
        fen: '8/8/8/8/8/8/8/8',
        orientation: 'white',
        coordinates: false,
        movable: { free: false },
        draggable: { enabled: false },
    });

    function squareAt(row, col) {
        if (orientation === 'white') {
            return FILES[col] + RANKS[7 - row];
        } else {
            return FILES[7 - col] + RANKS[row];
        }
    }

    function buildOverlay() {
        overlayEl.innerHTML = '';
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const cell = document.createElement('div');
                cell.className = 'click-cell';
                const sq = squareAt(row, col);
                cell.dataset.square = sq;
                cell.addEventListener('click', () => handleClick(sq));
                overlayEl.appendChild(cell);
            }
        }
    }

    function pickNextSquare() {
        const pool = currentSquare ? ALL_SQUARES.filter(s => s !== currentSquare) : ALL_SQUARES;
        return pool[Math.floor(Math.random() * pool.length)];
    }

    function showPrompt() {
        currentSquare = pickNextSquare();
        promptEl.textContent = currentSquare;
        feedbackEl.textContent = '';
        feedbackEl.style.color = '';
        locked = false;
    }

    function handleClick(sq) {
        if (locked || !currentSquare) return;
        locked = true;
        total++;

        const clickedCell = overlayEl.querySelector(`[data-square="${sq}"]`);
        const targetCell = overlayEl.querySelector(`[data-square="${currentSquare}"]`);

        if (sq === currentSquare) {
            correct++;
            streak++;
            if (streak > bestStreak) bestStreak = streak;
            feedbackEl.textContent = 'Correct!';
            feedbackEl.style.color = '#81b64c';
            if (clickedCell) clickedCell.classList.add('correct');
            updateStats();
            setTimeout(() => {
                if (clickedCell) clickedCell.classList.remove('correct');
                showPrompt();
            }, 450);
        } else {
            streak = 0;
            feedbackEl.textContent = `Wrong — that was ${sq}`;
            feedbackEl.style.color = '#fa412d';
            if (clickedCell) clickedCell.classList.add('wrong');
            if (targetCell) targetCell.classList.add('correct');
            updateStats();
            setTimeout(() => {
                if (clickedCell) clickedCell.classList.remove('wrong');
                if (targetCell) targetCell.classList.remove('correct');
                showPrompt();
            }, 900);
        }
    }

    function updateStats() {
        document.getElementById('score-correct').textContent = correct;
        document.getElementById('score-total').textContent = total;
        document.getElementById('score-streak').textContent = streak;
        document.getElementById('score-best').textContent = bestStreak;
    }

    document.getElementById('flip-btn').addEventListener('click', () => {
        orientation = orientation === 'white' ? 'black' : 'white';
        cg.set({ orientation });
        buildOverlay();
    });

    document.getElementById('reset-btn').addEventListener('click', () => {
        correct = 0;
        total = 0;
        streak = 0;
        bestStreak = 0;
        updateStats();
        showPrompt();
    });

    buildOverlay();
    showPrompt();
});
