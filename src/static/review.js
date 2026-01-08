let entries = [];
let move_idx = 0;
let meta = {};

const circle = document.getElementById('progress-ring');
const radius = circle.r.baseVal.value;
const circumference = 2 * Math.PI * radius;

const captureAudio = new Audio(captureSoundUrl);
const moveSelfAudio = new Audio(moveSelfSoundUrl);
const promoteSound = new Audio(promoteSoundUrl);
const checkSound = new Audio(checkSoundUrl);
const castleSound = new Audio(castleSoundurl);

circle.style.strokeDasharray = `${circumference} ${circumference}`;
circle.style.strokeDashoffset = circumference;

let chessground;
let bestLineTimer = null;
let bestLinePlaying = false;
let bestLineOriginalFen = null;
let bestLineMoves = [];
let bestLineIndex = 0;
let bestLineSavedShapes = null;
let lastShapes = [];

function setProgress(percent) {
    const offset = circumference - (percent / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    document.getElementById('loading-text').textContent = `${percent}%`;
}

async function loadReviewData() {
    document.getElementById('eval-bar').style.display = 'none';
    document.getElementById('move-classifications').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';

    let url = '/review_data?' + new URLSearchParams(window.location.search).toString();
    console.log("Fetching review data from:", url);
    const initialResponse = await fetch(url);
    const initialData = await initialResponse.json();
    console.log("Received review data:", initialData);
    uuid = initialData.uuid;
    attempts = 0;
    await sleep(150);
    while (attempts < 60) {
        try {
            const statusResponse = await fetch(`/get_entry_status?uuid=${uuid}`);
            const statusData = await statusResponse.json();
            if (statusData.error) {
                responseStatus = statusResponse.status
                console.error("Error fetching status:", statusData, responseStatus);

                // Handle 404 and other errors 
                document.getElementById('loading-container').style.display = 'none';
                document.getElementById('error-message').style.display = 'block';
                document.getElementById('error-message').textContent = `Error ${responseStatus}: ${statusData.error}`;
                break; // Exit loop on error
            }
            if (typeof statusData == "string" && statusData.includes("loading")) {
                let progressPercent = 0;
                if (!statusData.includes('loading 0')) {
                    progressPercent = statusData.substring(statusData.indexOf('(') + 1, statusData.indexOf(')') - 1);
                    progressPercent = parseInt(progressPercent, 10);
                }
                console.log("Attempt ", attempts, "Progress percent:", progressPercent);
                setProgress(progressPercent);
                document.getElementById('loading-container').style.display = 'block';
                await sleep(2000);
                attempts++;
            } else {
                console.log("Final status data:", statusData);
                setProgress(100);
                document.getElementById('loading-container').style.display = 'none';
                document.getElementById('eval-bar').style.display = '';
                document.getElementById('move-classifications').style.display = '';
                entries = statusData.analysis;
                meta = statusData;
                user_color = meta.user_playing_as_white ? "white" : "black";
                opponent_color = meta.user_playing_as_white ? "black" : "white";
                classification_frequency_user = meta.classification_frequency[user_color];
                classification_frequency_opponent = meta.classification_frequency[opponent_color];
                setClassificationFrequency(classification_frequency_user, classification_frequency_opponent);
                chessground = Chessground(document.getElementById("chessground_board"), {
                    orientation: user_color,
                    movable: {
                        free: false,
                        showDests: true,
                    }
                });
                showMove(0)
                break
            }
        } catch (error) {
            console.error("Error fetching review data:", error);
            attempts++;
        }
    }

    if (attempts >= 60) {
        console.warn("Reached max attempts, stopping load.");
        document.getElementById('loading-container').style.display = 'none';
        document.getElementById('error-message').style.display = 'block';
        document.getElementById('error-message').textContent = `Error : Maximum attempts reached while loading data. Please try again later.`;
    }
}

loadReviewData();

function setClassificationFrequency(classification_frequency_user, classification_frequency_opponent) {
    const classifications = [
        "Best Move",
        "Good Move",
        "Inaccuracy",
        "Mistake",
        "Blunder",
        "Missed mate",
    ];

    let classificationContainer = document.getElementById('move-classifications');
    classificationContainer.innerHTML = ''; // Clear previous content

    // Create table
    let table = document.createElement('table');
    table.classList.add('classification-table');

    // Table header
    let thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Move Type</th>
            <th>User</th>
            <th>Opponent</th>
        </tr>
    `;
    table.appendChild(thead);

    // Table body
    let tbody = document.createElement('tbody');

    for (let classification of classifications) {
        let color = getColor(classification);
        let count_user = classification_frequency_user[classification] || 0;
        let count_opponent = classification_frequency_opponent[classification] || 0;

        let row = document.createElement('tr');
        row.innerHTML = `
            <td style="color:${color}; font-weight:bold;">${classification}</td>
            <td class="white-count">${count_user}</td>
            <td class="black-count">${count_opponent}</td>
        `;
        tbody.appendChild(row);
    }

    table.appendChild(tbody);
    classificationContainer.appendChild(table);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function safePlay(audio) {
    const playPromise = audio.play();
    if (playPromise !== undefined) {
        playPromise.catch(error => {
            console.warn("Audio play failed:", error);
        });
    }
}

function showMove(idx) {
    move_idx = idx;
    let entry = entries[move_idx];
    if (entry.move.includes('+') || entry.move.includes('#')) {
        safePlay(checkSound);
    } else if (entry.move.includes('=')) {
        safePlay(promoteSound);
    } else if (entry.move.includes('x')) {
        safePlay(captureAudio);
    }
    else if (entry.move.includes('O-O')) {
        safePlay(castleSound);
    }
    else {
        safePlay(moveSelfAudio);
    }
    let user_playing_as_white = meta.user_playing_as_white;
    let evaluation = entry.evaluation || {};
    let evalText = "";
    let evalCp = 0;
    if (evaluation.type === "mate") {
        if (evaluation.value > 0) {
            evalCp = 1000; // Convert to centipawns
            evalText = `White mate in ${evaluation.value}`;
        } else if (evaluation.value < 0) {
            evalCp = -1000; // Convert to centipawns
            evalText = `Black mate in ${Math.abs(evaluation.value)}`;
        } else {
            evalText = "Game over";
        }
    } else if (evaluation.type === "cp") {
        evalCp = evaluation.value;
        evalText = `${evaluation.value} centipawns`;
    } else {
        evalText = "No evaluation available";
    }
    document.getElementById('move-info').innerHTML = `
    <span><strong>Move:</strong> ${entry.move}</span><br>
    <span><strong>Classification:</strong> <span style="color:${getColor(entry.classification)}">${entry.classification}</span></span><br>
    <span><strong>Evaluation:</strong> ${evalText}</span><br>
    <span><strong>Board:</strong> ${entry.board}</span><br>
    <span><strong>Accuracy:</strong> User ${user_playing_as_white ? meta.white_accuracy : meta.black_accuracy} % - Opponent ${user_playing_as_white ? meta.black_accuracy : meta.white_accuracy} %</span><br>
    <span><strong>Result:</strong> User: ${meta.user_result} - Opponent: ${meta.opponent_result}</span><br>
    <span><strong>Score per min:</strong> User: ${meta.user_score_per_min} - Opponent: ${meta.opponent_score_per_min}</span><br>
    <span><strong>Best Line:</strong> ${entry.best_line}</span><br>
    <span><strong>Played Line:</strong> ${entry.played_line}</span><br>
    `;
    console.log(entry)
    chessground.set({
        fen: entry.board,
        orientation: user_color,
        movable: {
            free: true,
            showDests: true,
        }
    });

    if (entry.classification != "Best Move") {

        shapes = []

        shapes.push(
            {
                orig: entry.best_move_uci.substring(0, 2),
                dest: entry.best_move_uci.substring(2, 4),
                brush: 'green',
            }
        )


        shapes.push({
            orig: entry.uci_move.substring(2, 4),  // just the square
            customSvg: {
                html: getSvg(entry.classification),
            }
        })

        chessground.setShapes(shapes);
            lastShapes = shapes;
        }
        else {
            lastShapes = [];
        }
    let url_id, url_id_split;
    url_id_split = meta.url.split("/");
    url_id = url_id_split[url_id_split.length - 1];
    document.getElementById('game-header').innerText =
        `Game ID: ${url_id} | Move ${move_idx + 1} / ${entries.length} | ${meta.archiveDate || ""} | ${meta.user || ""} (${meta.user_rating || ""}) VS ${meta.opponent_user || ""} (${meta.opponent_rating || ""})`;
    document.getElementById('prev').disabled = move_idx === 0;
    document.getElementById('firstMove').disabled = move_idx === 0;
    document.getElementById('next').disabled = move_idx === entries.length - 1;
    document.getElementById('lastMove').disabled = move_idx === entries.length - 1;
    let white_turn = move_idx % 2;
    let now_it_is_users_turn = (user_playing_as_white && white_turn) || (!user_playing_as_white && !white_turn)
    // console.log("idx ", idx, " white_turn ", white_turn, "user_playing_as_whtie ", user_playing_as_white, " now_user_turn ", now_it_is_users_turn)
    if (idx == 0) {
        if (user_playing_as_white) {
            renderClockTime(entries[move_idx].clock_time, true, user_playing_as_white)
            renderClockTime(meta.time_control, false, user_playing_as_white)
        } else {
            renderClockTime(entries[move_idx].clock_time, false, user_playing_as_white)
            renderClockTime(meta.time_control, true, user_playing_as_white)
        }

    } else {
        renderClockTime(entries[move_idx].clock_time, !now_it_is_users_turn, user_playing_as_white)
    }
    renderEvalBar(evalCp, user_playing_as_white);
    renderBoardValue(user_playing_as_white, entry.board);
}

function renderBoardValue(user_playing_as_white, fen) {
    white_sum = 0
    black_sum = 0
    const piece_values = {
        'p': 1,
        'n': 3,
        'b': 3,
        'r': 5,
        'q': 9,
        'k': 0
    };
    let board_part = fen.split(" ")[0];
    let rows = board_part.split("/");

    for (let row of rows) {
        for (let char of row) {
            if (char in piece_values) {
                black_sum += piece_values[char];
            } else if (char.toLowerCase() in piece_values) {
                white_sum += piece_values[char.toLowerCase()];
            }
        }
    }
    if (user_playing_as_white) {
        document.getElementById('lower-board-value').innerText = `${white_sum - black_sum}`;
    } else {
        document.getElementById('lower-board-value').innerText = `${black_sum - white_sum}`;
    }
}

function renderClockTime(clock_time, render_lower_time_control, user_playing_as_white) {
    let clock_time_str = clock_time.toString()
    let decimal = ""
    if (clock_time_str.includes('.')) {
        decimal = clock_time_str.substring(clock_time_str.indexOf('.'), clock_time_str.length)
    }
    let clockTimeElementID = render_lower_time_control ? "lower_time" : "upper_time"
    let clockTimeElement = document.getElementById(clockTimeElementID);
    setClockTimeStyle(clockTimeElement,
        (render_lower_time_control && !user_playing_as_white) || (!render_lower_time_control && user_playing_as_white))
    clock_time = Math.floor(clock_time)
    if (clock_time !== null) {
        let minutes = Math.floor(clock_time / 60);
        let seconds = clock_time - minutes * 60;
        console.log("clock_time ", clock_time, " minutes ", minutes, " seconds ", seconds, " decimal ", decimal, "render_lower_time_control ", render_lower_time_control, " user_playing_as_white ", user_playing_as_white)
        clockTimeElement.innerText = `${minutes}:${seconds.toString().padStart(2, '0')}${decimal}`;
    } else {
        clockTimeElement.innerText = "Clock Time: Not available";
    }
}

function setClockTimeStyle(element, time_control_is_black) {
    if (time_control_is_black) {
        element.style.color = "#ffffff";
        element.style.backgroundColor = "#262522";
        element.style.borderRadius = "8px";
        element.style.padding = "0.2em 0.5em";
        element.style.fontWeight = "bold";
        element.style.fontSize = "1.2em";
        element.style.minWidth = "4.5em";
        element.style.textAlign = "center";
    } else {
        element.style.color = "#000000";
        element.style.backgroundColor = "#ffffff";
        element.style.borderRadius = "8px";
        element.style.padding = "0.2em 0.5em";
        element.style.fontWeight = "bold";
        element.style.fontSize = "1.2em";
        element.style.minWidth = "4.5em";
        element.style.textAlign = "center";
    }
    element.style.width = "fit-content";
}

function renderEvalBar(evalCp, user_playing_as_white) {
    // Clamp eval to [-10, 10] for display (1000 centipawns)
    let evalClamped = Math.max(-1000, Math.min(1000, evalCp));
    // If user is playing as white, 100% = white wins; if black, 100% = black wins
    let percent;
    if (user_playing_as_white) {
        percent = 50 + (evalClamped / 20); // 100 = white wins
    } else {
        percent = 50 + (evalClamped / 20); // 100 = black wins
    }
    percent = Math.max(0, Math.min(100, percent));
    if (user_playing_as_white) {
        evalBarFillStyle = document.getElementById('eval-bar-fill').style;
        evalBarStyle = document.getElementById('eval-bar').style;

        evalBarStyle.width = '18px';
        evalBarStyle.height = '40vw';
        evalBarStyle.backgroundColor = '#403d39';
        evalBarStyle.borderRadius = '8px';
        evalBarStyle.marginRight = '1.2em';
        evalBarStyle.position = 'relative';
        evalBarStyle.overflow = 'hidden';
        evalBarStyle.flexShrink = '0';

        evalBarFillStyle.position = 'absolute';
        evalBarFillStyle.left = '0';
        evalBarFillStyle.width = '100%';
        evalBarFillStyle.background = '#ffffff';
        evalBarFillStyle.transition = 'height 0.3s';
        evalBarFillStyle.borderRadius = '8px';
        evalBarFillStyle.zIndex = '2';
    } else {
        evalBarFillStyle = document.getElementById('eval-bar-fill').style;
        evalBarStyle = document.getElementById('eval-bar').style;

        evalBarFillStyle.width = '18px';
        evalBarFillStyle.height = '40vw';
        evalBarFillStyle.backgroundColor = '#ffffff';
        evalBarFillStyle.borderRadius = '8px';
        evalBarFillStyle.marginRight = '1.2em';
        evalBarFillStyle.position = 'relative';
        evalBarFillStyle.overflow = 'hidden';
        evalBarFillStyle.flexShrink = '0';

        // evalBarStyle.position = 'absolute';
        evalBarStyle.left = '0';
        // evalBarStyle.width = '100%';
        evalBarStyle.background = '#403d39';
        evalBarStyle.transition = 'height 0.3s';
        evalBarStyle.borderRadius = '8px';
        evalBarStyle.zIndex = '2';
    };
    document.getElementById('eval-bar-fill').style.height = percent + "%";
    document.getElementById('eval-bar-fill').style.bottom = 0;
}

function getColor(classification) {
    const colors = {
        "Best Move": "#749bbf",
        "Good Move": "#81b64c",
        "Inaccuracy": "#f7c631",
        "Mistake": "#ff7769",
        "Blunder": "#fa412d",
        "Missed mate": "#c3c2c1",
    };
    if (!colors[classification]) {
        console.warn(`No color defined for classification: ${classification}`);
        throw new Error(`Unknown classification: ${classification}`);
    }
    return colors[classification];
}

function getSvg(classification) {
    const svgs = {
        "Good Move": goodMoveSvgHtml,
        "Inaccuracy": inaccuracySvgHtml,
        "Mistake": mistakeSvgHtml,
        "Blunder": blunderSvgHtml,
        "Missed mate": missedWinSvgHtml,
    };
    if (!svgs[classification]) {
        console.warn(`No SVG defined for classification: ${classification}`);
        throw new Error(`Unknown classification: ${classification}`);
    }
    return svgs[classification];
}

function togglePlayBestLine() {
    if (bestLinePlaying) {
        pausePlayingBestLine();
    } else {
        playBestLine();
    }
}

function playBestLine() {
    const entry = entries[move_idx];
    if (!entry || !entry.best_line) return;

    // Initialize moves only if not resuming
    if (!bestLineMoves || bestLineMoves.length === 0) {
        // Parse UCI moves robustly from the best_line string.
        // Accept tokens like "e2e4", "e2-e4", or "1.e2e4" and extract UCI pairs.
        bestLineMoves = [];
        const tokens = entry.best_line.split(/\s+/);
        for (let t of tokens) {
            if (!t) continue;
            // strip leading move numbers like "1." or "1..."
            t = t.replace(/^\d+\.*\.*/, '');
            // find a UCI pattern within the token
            const m = t.match(/([a-h][1-8][a-h][1-8])/i);
            if (m && m[1]) {
                bestLineMoves.push(m[1].toLowerCase());
            }
        }
        bestLineIndex = 0;
        // Save original fen (the currently displayed board) to restore later if desired
        bestLineOriginalFen = entry.board;
        // Save existing shapes so we can restore them later
        bestLineSavedShapes = lastShapes ? lastShapes.slice() : [];
    }
    if (bestLineMoves.length === 0) return;

    // Only reset the board to the position before this move when starting fresh.
    // Don't reset on resume so playback continues from the paused position.
    if (bestLineIndex === 0) {
        try {
            let startFen = entry.board;
            if (move_idx > 0 && entries[move_idx - 1] && entries[move_idx - 1].board) {
                startFen = entries[move_idx - 1].board;
            }
            chessground.set({
                fen: startFen,
                orientation: user_color,
                movable: {
                    free: true,
                    showDests: true,
                }
            });
        } catch (e) {
            console.warn('Failed to set starting FEN for best-line playback', e);
        }
    }

    // Disable navigation while playing (also keep disabled while paused)
    document.getElementById('prev').disabled = true;
    document.getElementById('next').disabled = true;
    document.getElementById('firstMove').disabled = true;
    document.getElementById('lastMove').disabled = true;
    document.getElementById('playBestLine').innerText = 'Pause';
    bestLinePlaying = true;
    // enable Stop button
    try { document.getElementById('stopBestLine').disabled = false; } catch (e) { }

    // Clear any arrows/shapes while playing the best line
    try {
        chessground.setShapes([]);
    } catch (e) {
        console.warn('Failed to clear shapes before playback', e);
    }

    function step() {
        if (!bestLinePlaying) return;
        if (bestLineIndex >= bestLineMoves.length) {
            // finished: stop and restore saved shapes
            stopPlayingBestLine(true);
            return;
        }
        const move = bestLineMoves[bestLineIndex];
        const orig = move.substring(0, 2);
        const dest = move.substring(2, 4);
        try {
            chessground.move(orig, dest);
        } catch (e) {
            console.warn('Failed to play move', move, e);
        }
        bestLineIndex++;
        bestLineTimer = setTimeout(step, 800);
    }

    step();
}

function pausePlayingBestLine() {
    if (bestLineTimer) {
        clearTimeout(bestLineTimer);
        bestLineTimer = null;
    }
    bestLinePlaying = false;
    // Keep navigation disabled while paused so board state isn't changed
    document.getElementById('playBestLine').innerText = 'Resume';
    try { document.getElementById('stopBestLine').disabled = false; } catch (e) { }
}

function stopPlayingBestLine(restore = true) {
    if (bestLineTimer) {
        clearTimeout(bestLineTimer);
        bestLineTimer = null;
    }
    bestLinePlaying = false;
    document.getElementById('playBestLine').innerText = 'Play Best Line';
    // Re-enable navigation
    document.getElementById('prev').disabled = move_idx === 0;
    document.getElementById('firstMove').disabled = move_idx === 0;
    document.getElementById('next').disabled = move_idx === entries.length - 1;
    document.getElementById('lastMove').disabled = move_idx === entries.length - 1;

    // Restore saved shapes (don't revert the board position)
    try {
        if (restore && bestLineSavedShapes) {
            chessground.setShapes(bestLineSavedShapes);
        }
    } catch (e) {
        console.warn('Failed to restore shapes after stopping best-line playback', e);
    }

    // clear stored best-line state
    bestLineMoves = [];
    bestLineIndex = 0;
    bestLineSavedShapes = null;
    bestLineOriginalFen = null;
    try { document.getElementById('stopBestLine').disabled = true; } catch (e) { }
}

function cancelPlayingBestLine() {
    // Completely cancel playback and restore original board and shapes
    if (bestLineTimer) {
        clearTimeout(bestLineTimer);
        bestLineTimer = null;
    }
    bestLinePlaying = false;

    // Restore original fen if available
    try {
        if (bestLineOriginalFen) {
            chessground.set({
                fen: bestLineOriginalFen,
                orientation: user_color,
                movable: {
                    free: true,
                    showDests: true,
                }
            });
        }
    } catch (e) {
        console.warn('Failed to restore original FEN on cancel', e);
    }

    // Restore saved shapes
    try {
        if (bestLineSavedShapes) chessground.setShapes(bestLineSavedShapes);
    } catch (e) {
        console.warn('Failed to restore shapes on cancel', e);
    }

    // Re-enable navigation
    document.getElementById('prev').disabled = move_idx === 0;
    document.getElementById('firstMove').disabled = move_idx === 0;
    document.getElementById('next').disabled = move_idx === entries.length - 1;
    document.getElementById('lastMove').disabled = move_idx === entries.length - 1;

    // reset UI
    document.getElementById('playBestLine').innerText = 'Play Best Line';
    try { document.getElementById('stopBestLine').disabled = true; } catch (e) { }

    // clear stored best-line state
    bestLineMoves = [];
    bestLineIndex = 0;
    bestLineSavedShapes = null;
    bestLineOriginalFen = null;
}

document.getElementById('firstMove').onclick = () => showMove(0);
document.getElementById('playBestLine').onclick = () => togglePlayBestLine();
document.getElementById('stopBestLine').onclick = () => cancelPlayingBestLine();
document.getElementById('prev').onclick = () => showMove(move_idx - 1);
document.getElementById('next').onclick = () => showMove(move_idx + 1);
document.getElementById('lastMove').onclick = () => showMove(entries.length - 1);
document.addEventListener('keydown', function (event) {
    if (event.key === "ArrowLeft" && move_idx > 0) showMove(move_idx - 1);
    if (event.key === "ArrowRight" && move_idx < entries.length - 1) showMove(move_idx + 1);
    if (event.key === "ArrowDown") showMove(0);
    if (event.key === "ArrowUp") showMove(entries.length - 1);
    if (event.key === 'p') togglePlayBestLine();
    if (event.key === 's') cancelPlayingBestLine();
});