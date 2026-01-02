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

    function showSolutionMoves(moves) {
        let currentFen = initialFen;
        let index = 0;

        async function playNextMove() {
            if (index >= moves.length) {
                resetButton.style.display = "block"; // Show reset button after solution is complete
                await markPuzzleAsSolved(); // Mark the puzzle as solved
                // Show the user's played move (if available)
                try {
                    const playedSan = puzzle.user_move_san || '';
                    const playedUci = puzzle.user_move_uci || '';
                    if (playedSan || playedUci) {
                        const playedHtml = `<div><strong>Your move:</strong> ${playedSan} ${playedUci ? `(${playedUci})` : ''}</div>`;
                        document.getElementById('puzzle-info').insertAdjacentHTML('beforeend', playedHtml);
                    }
                } catch (e) {
                    console.warn('Failed to display played move:', e);
                }
                return;
            }

            const move = moves[index];
            const orig = move.substring(0, 2);
            const dest = move.substring(2, 4);

            chessground.move(orig, dest);

            // Simulate the move (this is a stub; replace with actual FEN update logic if needed)
            currentFen = currentFen; // Replace with updated FEN after the move

            index++;
            setTimeout(playNextMove, 1000); // Delay between moves
        }

        playNextMove();
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

    document.getElementById('puzzle-info').innerHTML = `
        <strong>Puzzle ID:</strong> ${puzzle.puzzle_id}<br>
        <strong>Game ID:</strong> ${puzzle.game_id}<br>
        <strong>Classification:</strong> ${puzzle.classification}<br>
    `;
});