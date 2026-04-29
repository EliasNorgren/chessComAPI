function getClassificationColor(classification) {
    const colors = {
        "Best Move":  "#749bbf",
        "Good Move":  "#81b64c",
        "Inaccuracy": "#f7c631",
        "Mistake":    "#ff7769",
        "Blunder":    "#fa412d",
        "Missed mate":"#c3c2c1",
    };
    return colors[classification] || '#888';
}

document.addEventListener('DOMContentLoaded', async function () {
    const user = new URLSearchParams(window.location.search).get('user') || '';
    if (!user) {
        document.getElementById('error-message').textContent = "User parameter is required";
        return;
    }

    const puzzleResp = await fetch(`/get_unsolved_puzzle_personal?user=${user}`);
    const puzzleData = await puzzleResp.json();

    if (puzzleData.error) {
        document.getElementById('error-message').textContent = puzzleData.error;
        return;
    }

    let puzzle = puzzleData;
    // Filter out any empty moves (trailing spaces) and ensure we have a clean list
    let solutionMoves = puzzle.solution_line.split(' ').filter(m => m && m.trim());
    let userColor = puzzle.user_playing_as_white ? 'white' : 'black';

    // Store the initial FEN for resets
    const initialFen = puzzle.fen;

    // Initialize Chessground with the movable event attached so we don't have to
    // re-attach it later. Also lock movement to the user's color.
    let chessground = Chessground(document.getElementById("chessground_board"), {
        fen: initialFen,
        orientation: userColor,
        turnColor: userColor,
        movable: {
            free: true,
            color: userColor,
            events: {
                after: onUserMove
            }
        }
    });

    let resetButton = document.createElement('button');
    resetButton.textContent = "Reset Puzzle";
    resetButton.className = 'reset-btn';
    resetButton.style.display = "none"; // Initially hidden
    resetButton.onclick = resetPuzzle;
    // Place the reset button inside the reset-container in the template
    const resetContainer = document.getElementById('reset-container') || document.body;
    resetContainer.appendChild(resetButton);

    function onUserMove(orig, dest, captured) {
        // Guard: Chessground sometimes triggers events with undefined args when
        // programmatically updating the board. Ignore those.
        if (!orig || !dest || typeof orig !== 'string' || typeof dest !== 'string') {
            return;
        }

        console.log(`User moved from ${orig} to ${dest}`);
        let moveUci = orig + dest;
        let expectedMove = solutionMoves[0]; // Only check the first move
        // Handle pawn promotion: append the promotion piece from the expected move
        if (expectedMove.length === 5 && expectedMove.startsWith(moveUci)) {
            moveUci += expectedMove[4];
        }
        console.log(`Expected move: ${expectedMove}, User move: ${moveUci}`);
        if (moveUci === expectedMove) {
            showFeedback("Correct!", true);
            showSolutionMoves(solutionMoves.slice(1)); // Show the rest of the solution
        } else {
            showFeedback("Wrong move. Try again.", false);
            // Reset board to initial FEN without replacing the movable/events
            // object. Replacing the movable object can remove handlers in some
            // Chessground builds; only change the position so the "after"
            // callback remains attached.
            chessground.set({
                fen: initialFen,
                orientation: userColor,
                turnColor: userColor
            });
        }
    }

    let solutionTimer = null;
    let solutionPaused = false;
    let solutionCurrentMoves = [];
    let solutionIndex = 0;

    function showSolutionMoves(moves) {
        if (solutionTimer) clearTimeout(solutionTimer);
        solutionCurrentMoves = moves;
        solutionIndex = 0;
        solutionPaused = false;
        pauseResumeButton.textContent = 'Pause';
        pauseResumeButton.style.display = '';
        resetLineButton.style.display = '';
        playNextSolutionMove();
    }

    function playNextSolutionMove() {
        if (solutionPaused) return;
        if (solutionIndex >= solutionCurrentMoves.length) {
            pauseResumeButton.style.display = 'none';
            resetLineButton.style.display = 'none';
            resetButton.style.display = 'block';
            markPuzzleAsSolved();
            return;
        }
        const move = solutionCurrentMoves[solutionIndex];
        chessground.move(move.substring(0, 2), move.substring(2, 4));
        solutionIndex++;
        solutionTimer = setTimeout(playNextSolutionMove, 1000);
    }

    function toggleSolutionPlayback() {
        solutionPaused = !solutionPaused;
        pauseResumeButton.textContent = solutionPaused ? 'Resume' : 'Pause';
        if (!solutionPaused) playNextSolutionMove();
    }

    function resetSolutionLine() {
        if (solutionTimer) clearTimeout(solutionTimer);
        solutionIndex = 0;
        solutionPaused = true;
        pauseResumeButton.textContent = 'Resume';
        chessground.set({ fen: initialFen, orientation: userColor, turnColor: userColor });
    }

    async function markPuzzleAsSolved() {
        try {
            const response = await fetch('/set_puzzle_solved', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ puzzle_id: puzzle.puzzle_id }),
            });

            const result = await response.json();
            if (result.status === "success") {
                console.log("Puzzle marked as solved successfully.");
            } else {
                console.error("Failed to mark puzzle as solved:", result.error);
            }
        } catch (error) {
            console.error("Error marking puzzle as solved:", error);
        }
    }

    function resetPuzzle() {
        // Reset the board to the initial state without recreating Chessground.
        // Only update the FEN so we don't disturb the attached handlers.
        chessground.set({
            fen: initialFen,
            orientation: userColor,
            turnColor: userColor
        });
        showFeedback("", false); // Clear feedback
    }

    function showFeedback(msg, success) {
        let el = document.getElementById('feedback');
        el.textContent = msg;
        el.style.color = success ? 'green' : 'red';
    }

    const clsColor = getClassificationColor(puzzle.classification);
    const row = (label, value) => `
        <div style="padding:0.55em 1em;border-bottom:1px solid #2e2c29;border-right:1px solid #2e2c29;">
            <div style="font-size:0.72em;font-weight:600;color:#666;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.2em;">${label}</div>
            <div style="font-size:0.92em;color:#c8c6c3;font-weight:500;">${value}</div>
        </div>`;
    const rowLast = (label, value) => `
        <div style="padding:0.55em 1em;border-bottom:1px solid #2e2c29;">
            <div style="font-size:0.72em;font-weight:600;color:#666;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.2em;">${label}</div>
            <div style="font-size:0.92em;color:#c8c6c3;font-weight:500;">${value}</div>
        </div>`;
    document.getElementById('puzzle-info').innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;padding:0.8em 1em 0.7em;border-bottom:1px solid #2e2c29;">
            <span style="font-size:0.75em;font-weight:700;color:#666;letter-spacing:0.08em;text-transform:uppercase;">Puzzle #${puzzle.puzzle_id}</span>
            <span class="classification-badge" style="--cls-color:${clsColor}">${puzzle.classification}</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;">
            ${row('Game ID', puzzle.game_id)}
            ${rowLast('Date', puzzle.archive_date || '–')}
            <div style="padding:0.55em 1em;border-right:1px solid #2e2c29;">
                <div style="font-size:0.72em;font-weight:600;color:#666;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.2em;">Your move</div>
                <div style="font-size:0.92em;color:#c8c6c3;font-weight:500;">${puzzle.user_move_san || '–'} <span style="color:#555;">${puzzle.user_move_uci ? `(${puzzle.user_move_uci})` : ''}</span></div>
            </div>
            <div id="best-move-cell" style="padding:0.55em 1em;display:none;">
                <div style="font-size:0.72em;font-weight:600;color:#666;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.2em;">Best move</div>
                <div style="font-size:0.92em;color:#c8c6c3;font-weight:500;">${puzzle.best_move_san || '–'} <span style="color:#555;">${puzzle.best_move_uci ? `(${puzzle.best_move_uci})` : ''}</span></div>
            </div>
        </div>
    `;

    const giveUpButton = document.createElement('button');
    giveUpButton.textContent = "Give Up";
    giveUpButton.onclick = () => {
        document.getElementById('best-move-cell').style.display = '';
        showFeedback("Better luck next time.", false);
        giveUpButton.disabled = true;
    };

    const pauseResumeButton = document.createElement('button');
    pauseResumeButton.textContent = 'Pause';
    pauseResumeButton.style.display = 'none';
    pauseResumeButton.onclick = toggleSolutionPlayback;

    const resetLineButton = document.createElement('button');
    resetLineButton.textContent = 'Reset Line';
    resetLineButton.style.display = 'none';
    resetLineButton.onclick = resetSolutionLine;

    resetContainer.appendChild(giveUpButton);
    resetContainer.appendChild(pauseResumeButton);
    resetContainer.appendChild(resetLineButton);
});