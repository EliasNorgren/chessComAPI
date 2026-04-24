let entries = [];
let move_idx = 0;
let meta = {};
let servedByHostname = '';

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
let suppressMoveEvents = false;
let currentBoardFen = null;
let self_played_move_list = [];

function setProgress(percent) {
    const offset = circumference - (percent / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    document.getElementById('loading-text').textContent = `${percent}%`;
}

async function loadReviewData() {
    document.getElementById('eval-bar').style.display = 'none';
    document.getElementById('move-info').style.display = 'none';
    document.getElementById('horizontal-layout').style.display = 'none';
    document.getElementById('nav-btns').style.display = 'none';
    document.getElementById('best-line-btns').style.display = 'none';
    document.getElementById('get-position-stats').style.display = 'none';
    document.getElementById('get-responses').style.display = 'none';
    document.getElementById('lower-board-value').style.display = 'none';
    document.getElementById('move-classifications').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';
    document.getElementById('chessground_board').style.display = 'none';
    document.getElementById('eval-graph-container').style.display = 'none';

    let url = '/review_data?' + new URLSearchParams(window.location.search).toString();
    console.log("Fetching review data from:", url);
    const initialResponse = await fetch(url);
    const initialData = await initialResponse.json();
    console.log("Received review data:", initialData);
    uuid = initialData.uuid;
    servedByHostname = initialData.hostname || '';
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
                document.getElementById('move-info').style.display = '';
                document.getElementById('horizontal-layout').style.display = '';
                document.getElementById('nav-btns').style.display = '';
                document.getElementById('best-line-btns').style.display = '';
                document.getElementById('get-position-stats').style.display = '';
                document.getElementById('get-responses').style.display = '';
                document.getElementById('lower-board-value').style.display = '';
                document.getElementById('move-classifications').style.display = '';
                document.getElementById('chessground_board').style.display = '';
                document.getElementById('eval-graph-container').style.display = '';

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
                    },
                    events: {
                        move: (orig, dest, captured) => {
                            const moveUci = `${orig}${dest}`;
                            console.log('Move event received. Suppress:', suppressMoveEvents, 'Self-play queue:', self_played_move_list, 'Move:', orig, dest, 'Captured:', captured);
                            if (suppressMoveEvents) return;
                            // If this move matches an expected self-played move, consume it and ignore handling.
                            if (self_played_move_list.length && self_played_move_list[0] === moveUci) {
                                self_played_move_list.shift();
                                return;
                            }
                            try {
                                handlePieceMove(orig, dest, captured);
                            } catch (e) {
                                console.warn('handlePieceMove failed', e);
                            }
                        }
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

    // Find max count across both players for scaling bars
    let maxCount = 1;
    for (const cls of classifications) {
        maxCount = Math.max(maxCount,
            classification_frequency_user[cls] || 0,
            classification_frequency_opponent[cls] || 0);
    }

    const container = document.getElementById('move-classifications');
    const rows = classifications.map(cls => {
        const color = getColor(cls);
        const cu = classification_frequency_user[cls] || 0;
        const co = classification_frequency_opponent[cls] || 0;
        const barU = Math.round((cu / maxCount) * 100);
        const barO = Math.round((co / maxCount) * 100);
        return `
            <tr>
                <td><span class="cls-name" style="color:${color}">${cls}</span></td>
                <td class="count-cell">
                    <div class="count-bar-bg" style="background:${color}; width:${barU}%"></div>
                    <span class="count-text">${cu}</span>
                </td>
                <td class="count-cell">
                    <div class="count-bar-bg" style="background:${color}; width:${barO}%"></div>
                    <span class="count-text">${co}</span>
                </td>
            </tr>`;
    }).join('');

    container.innerHTML = `
        <div class="section-title">Move breakdown</div>
        <table class="classification-table">
            <thead><tr>
                <th>Type</th>
                <th>You</th>
                <th>Opp</th>
            </tr></thead>
            <tbody>${rows}</tbody>
        </table>`;
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
    self_played_move_list = [];
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
    let evalCp = 0;
    let evalDisplay = '';
    let evalClass = 'positive';

    if (evaluation.type === "mate") {
        if (evaluation.value > 0) {
            evalCp = 1000;
            evalDisplay = `+M${evaluation.value}`;
            evalClass = 'mate';
        } else if (evaluation.value < 0) {
            evalCp = -1000;
            evalDisplay = `-M${Math.abs(evaluation.value)}`;
            evalClass = 'mate';
        } else {
            evalDisplay = 'Game over';
            evalClass = 'negative';
        }
    } else if (evaluation.type === "cp") {
        evalCp = evaluation.value;
        const pawns = evaluation.value / 100;
        evalDisplay = (pawns >= 0 ? '+' : '') + pawns.toFixed(2);
        evalClass = pawns >= 0 ? 'positive' : 'negative';
    } else {
        evalDisplay = '–';
    }

    const clsColor = getColor(entry.classification);
    const moveNum = Math.floor(move_idx / 2) + 1;
    const isWhiteMove = move_idx % 2 === 0;
    const moveNumStr = isWhiteMove ? `${moveNum}.` : `${moveNum}…`;

    const userAcc  = user_playing_as_white ? meta.white_accuracy : meta.black_accuracy;
    const oppAcc   = user_playing_as_white ? meta.black_accuracy : meta.white_accuracy;
    const userResult = (meta.user_result || '').toLowerCase();

    document.getElementById('move-info').innerHTML = `
        <div class="move-header">
            <div class="move-title">
                <span class="move-number">${moveNumStr}</span>
                <span class="move-san">${entry.move}</span>
            </div>
            <span class="classification-badge" style="--cls-color:${clsColor}">${entry.classification}</span>
        </div>
        <div class="eval-row">
            <span class="eval-label">Eval</span>
            <span class="eval-value ${evalClass}">${evalDisplay}</span>
        </div>
        <div class="lines-section">
            <div class="line-item">
                <span class="line-label best-label">Best</span>
                <span class="line-moves">${entry.best_line || '–'}</span>
            </div>
            <div class="line-item">
                <span class="line-label played-label">Played</span>
                <span class="line-moves">${entry.played_line || '–'}</span>
            </div>
        </div>
        <div class="stats-section">
            <div class="stat-item">
                <div class="stat-label">Your accuracy</div>
                <div class="stat-value">${userAcc != null ? userAcc + '%' : '–'}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Opp accuracy</div>
                <div class="stat-value">${oppAcc != null ? oppAcc + '%' : '–'}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Your result</div>
                <div class="stat-value" style="color:${resultColor(userResult)}">${capitalize(userResult) || '–'}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Score / min</div>
                <div class="stat-value">${meta.user_score_per_min ?? '–'} · ${meta.opponent_score_per_min ?? '–'}</div>
            </div>
        </div>
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
    // Store the board FEN before any moves, so we can send pre-move FEN to backend
    currentBoardFen = entry.board;

    if (entry.classification != "Best Move") {
        setShapesForMove(entry.best_move_uci, entry.uci_move, entry.classification);
        lastShapes = shapes;
    }
    else {
        lastShapes = [];
    }
    const url_id = (meta.url || '').split("/").pop();
    const whitePlayer = meta.user_playing_as_white ? meta.user : meta.opponent_user;
    const blackPlayer = meta.user_playing_as_white ? meta.opponent_user : meta.user;
    const whiteRating = meta.user_playing_as_white ? meta.user_rating : meta.opponent_rating;
    const blackRating = meta.user_playing_as_white ? meta.opponent_rating : meta.user_rating;
    const whiteResult = meta.user_playing_as_white ? (meta.user_result || '').toLowerCase() : (meta.opponent_result || '').toLowerCase();
    const blackResult = meta.user_playing_as_white ? (meta.opponent_result || '').toLowerCase() : (meta.user_result || '').toLowerCase();
    document.getElementById('game-header').innerHTML = `
        <div class="header-players">
            <div class="header-player">
                <div class="player-dot white-dot"></div>
                <span class="player-name">${whitePlayer || '?'}</span>
                <span class="player-rating">(${whiteRating || '?'})</span>
                ${whiteResult ? `<span class="result-chip ${whiteResult}">${capitalize(whiteResult)}</span>` : ''}
            </div>
            <span class="vs-divider">vs</span>
            <div class="header-player">
                <div class="player-dot black-dot"></div>
                <span class="player-name">${blackPlayer || '?'}</span>
                <span class="player-rating">(${blackRating || '?'})</span>
                ${blackResult ? `<span class="result-chip ${blackResult}">${capitalize(blackResult)}</span>` : ''}
            </div>
        </div>
        <div class="header-meta">${meta.archiveDate || ''} &middot; Move ${move_idx + 1} / ${entries.length} &middot; #${url_id}${servedByHostname ? ` &middot; <span style="opacity:0.6">${servedByHostname}</span>` : ''}</div>
    `;
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
    renderEvalGraph(idx);
}

function setShapesForMove(best_move_uci, played_uci, classification) {
    shapes = []
    shapes.push(
        {
            orig: best_move_uci.substring(0, 2),
            dest: best_move_uci.substring(2, 4),
            brush: 'green',
        }
    )
    if (classification != "Best Move") {    
        shapes.push({
            orig: played_uci.substring(2, 4),  // just the square
            customSvg: {
                html: getSvg(classification),
            }
        })
    }
    chessground.setShapes(shapes);
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
    element.style.borderRadius = "6px";
    element.style.padding = "0.2em 0.6em";
    element.style.fontWeight = "700";
    element.style.fontSize = "1.1em";
    element.style.minWidth = "4.5em";
    element.style.textAlign = "center";
    element.style.width = "fit-content";
    element.style.letterSpacing = "0.02em";
    if (time_control_is_black) {
        element.style.color = "#e8e6e3";
        element.style.backgroundColor = "#1a1917";
        element.style.border = "1px solid #2e2c29";
    } else {
        element.style.color = "#1a1917";
        element.style.backgroundColor = "#e8e6e3";
        element.style.border = "1px solid #b0aea8";
    }
}

function renderEvalBar(evalCp, user_playing_as_white) {
    // Clamp eval to [-10, 10] for display (1000 centipawns)
    let evalClamped = Math.max(-1000, Math.min(1000, evalCp));
    // If user is playing as white, 100% = white wins; if black, 100% = black wins
    let percent;
    if (user_playing_as_white) {
        percent = 50 + (evalClamped / 20); // 100 = white wins
    } else {
        percent = 50 - (evalClamped / 20); // invert: positive eval = white winning = less fill from black's side
    }
    percent = Math.max(0, Math.min(100, percent));
    // Let CSS control dimensions; only update fill color direction based on player color
    const evalBarFill = document.getElementById('eval-bar-fill');
    const evalBar = document.getElementById('eval-bar');
    if (user_playing_as_white) {
        evalBar.style.backgroundColor = '#403d39';
        evalBarFill.style.background = '#ffffff';
        evalBarFill.style.position = 'absolute';
        evalBarFill.style.left = '0';
        evalBarFill.style.width = '100%';
        evalBarFill.style.bottom = '0';
    } else {
        evalBar.style.backgroundColor = '#ffffff';
        evalBarFill.style.background = '#403d39';
        evalBarFill.style.position = 'absolute';
        evalBarFill.style.left = '0';
        evalBarFill.style.width = '100%';
        evalBarFill.style.bottom = '0';
    }
    document.getElementById('eval-bar-fill').style.height = percent + "%";
    document.getElementById('eval-bar-fill').style.bottom = 0;
}

function renderEvalGraph(currentIdx) {
    const canvas = document.getElementById('eval-graph');
    if (!canvas || !entries.length) return;

    const container = canvas.parentElement;
    const width = container.clientWidth || 600;
    const height = 80;
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    const n = entries.length;
    const midY = height / 2;

    function entryToCp(entry) {
        const ev = entry.evaluation || {};
        if (ev.type === 'mate') return ev.value > 0 ? 1000 : -1000;
        if (ev.type === 'cp') return Math.max(-1000, Math.min(1000, ev.value));
        return 0;
    }

    function cpToY(cp) {
        return midY - (cp / 1000) * midY;
    }

    const points = entries.map((e, i) => ({
        x: n === 1 ? width / 2 : (i / (n - 1)) * width,
        y: cpToY(entryToCp(e))
    }));

    // Background
    ctx.fillStyle = '#262522';
    ctx.fillRect(0, 0, width, height);

    // White advantage fill (above midline)
    ctx.beginPath();
    ctx.moveTo(points[0].x, midY);
    for (const p of points) ctx.lineTo(p.x, Math.min(p.y, midY));
    ctx.lineTo(points[n - 1].x, midY);
    ctx.closePath();
    ctx.fillStyle = 'rgba(210,210,210,0.9)';
    ctx.fill();

    // Black advantage fill (below midline)
    ctx.beginPath();
    ctx.moveTo(points[0].x, midY);
    for (const p of points) ctx.lineTo(p.x, Math.max(p.y, midY));
    ctx.lineTo(points[n - 1].x, midY);
    ctx.closePath();
    ctx.fillStyle = 'rgba(70,70,70,0.9)';
    ctx.fill();

    // Midline
    ctx.strokeStyle = '#504d49';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, midY);
    ctx.lineTo(width, midY);
    ctx.stroke();

    // Current move cursor
    if (currentIdx >= 0 && currentIdx < points.length) {
        ctx.strokeStyle = 'rgba(100,180,255,0.85)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(points[currentIdx].x, 0);
        ctx.lineTo(points[currentIdx].x, height);
        ctx.stroke();
    }

    // Classification dots
    const dotColors = {
        "Blunder": "#fa412d",
        "Mistake": "#ff7769",
        "Inaccuracy": "#f7c631",
        "Missed mate": "#c3c2c1",
    };
    const userPlaysWhite = meta.user_playing_as_white;
    for (let i = 0; i < entries.length; i++) {
        const isUserMove = !!userPlaysWhite === (i % 2 === 0);
        if (!isUserMove) continue;
        const color = dotColors[entries[i].classification];
        if (color) {
            ctx.beginPath();
            ctx.arc(points[i].x, points[i].y, 4, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
        }
    }
}

function resultColor(result) {
    if (result === 'win')  return '#81b64c';
    if (result === 'loss') return '#fa412d';
    return '#888';
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
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
            // Mark this move as self-played so the move handler can ignore it.
            self_played_move_list.push(`${orig}${dest}`);
            chessground.move(orig, dest);
        } catch (e) {
            console.warn('Failed to play move', move, e);
            // If move failed, ensure we don't leave an unmatched queued move
            if (self_played_move_list.length && self_played_move_list[self_played_move_list.length - 1] === `${orig}${dest}`) {
                self_played_move_list.pop();
            }
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
    // clear any queued self-played moves
    self_played_move_list = [];
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
    // clear any queued self-played moves
    self_played_move_list = [];
}

function getPositionStats() {
    const entry = entries[move_idx];
    if (!entry || !entry.board) return;
    fen = entry.board.split(" ")[0] + " " + entry.board.split(" ")[1];
    user = meta.user;
    time_control = meta.time_control;
    playing_as_white = meta.user_playing_as_white;
    url = `/get_win_percentage_and_accuracy?fen=${encodeURIComponent(fen)}&user=${encodeURIComponent(user)}&time_control=${encodeURIComponent(time_control)}&playing_as_white=${encodeURIComponent(playing_as_white)}`;
    fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('Position stats data:', data);
            renderPositionStats(data);
        })
        .catch(error => {
            console.error('Error fetching position stats:', error);
            alert('Error fetching position stats. See console for details.');
        });
}

function renderPositionStats(data) {
    const container = document.getElementById('position-stats');
    if (!container) return;
    // Defensive defaults
    const stats = (data && data.stats) ? data.stats : { win: 0, loss: 0, draw: 0, no_games: 0, no_games_with_acc: 0 };
    const accuracy = (data && typeof data.accuracy !== 'undefined') ? data.accuracy : null;
    const noGames = stats.no_games || 0;
    const winPct = stats.win || 0;
    const lossPct = stats.loss || 0;
    const drawPct = stats.draw || 0;
    const winCount = Math.round(noGames * winPct / 100);
    const lossCount = Math.round(noGames * lossPct / 100);
    const drawCount = Math.round(noGames * drawPct / 100);
    const average_opponent_rating = data.stats.average_opponent_rating || 'N/A';
    const average_win_opponent_rating = data.stats.average_opponent_rating_per_result.win || 'N/A';
    const average_loss_opponent_rating = data.stats.average_opponent_rating_per_result.loss || 'N/A';
    const average_draw_opponent_rating = data.stats.average_opponent_rating_per_result.draw || 'N/A';
    container.innerHTML = `
        <div style="background:#262420;border:1px solid #353230;border-radius:14px;overflow:hidden;color:#d4d2d0;">

            <!-- Header -->
            <div style="display:flex;align-items:center;justify-content:space-between;padding:0.75em 1em;border-bottom:1px solid #2e2c29;">
                <span style="font-size:0.75em;font-weight:700;color:#666;letter-spacing:0.08em;text-transform:uppercase;">Position stats</span>
                <span style="font-size:0.8em;color:#888">${noGames} games &nbsp;·&nbsp; ${stats.no_games_with_acc || 0} with acc</span>
            </div>

            <!-- Key stats grid -->
            <div style="display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid #2e2c29;">
                <div style="padding:0.6em 1em;border-right:1px solid #2e2c29;">
                    <div style="font-size:0.72em;font-weight:600;color:#666;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.2em;">Your accuracy</div>
                    <div style="font-size:1.5em;font-weight:700;color:#e8e6e3;">${accuracy !== null ? accuracy + '%' : '–'}</div>
                </div>
                <div style="padding:0.6em 1em;">
                    <div style="font-size:0.72em;font-weight:600;color:#666;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.2em;">Avg opp rating</div>
                    <div style="font-size:1.5em;font-weight:700;color:#e8e6e3;">${average_opponent_rating}</div>
                </div>
            </div>

            <!-- Per-result ratings -->
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;border-bottom:1px solid #2e2c29;">
                <div style="padding:0.55em 1em;border-right:1px solid #2e2c29;">
                    <div style="font-size:0.72em;font-weight:600;color:#555;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.2em;">Win opp</div>
                    <div style="font-size:1.1em;font-weight:700;color:#81b64c;">${average_win_opponent_rating}</div>
                </div>
                <div style="padding:0.55em 1em;border-right:1px solid #2e2c29;">
                    <div style="font-size:0.72em;font-weight:600;color:#555;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.2em;">Loss opp</div>
                    <div style="font-size:1.1em;font-weight:700;color:#fa412d;">${average_loss_opponent_rating}</div>
                </div>
                <div style="padding:0.55em 1em;">
                    <div style="font-size:0.72em;font-weight:600;color:#555;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.2em;">Draw opp</div>
                    <div style="font-size:1.1em;font-weight:700;color:#888;">${average_draw_opponent_rating}</div>
                </div>
            </div>

            <!-- W/L/D bar -->
            <div style="padding:0.75em 1em;">
                <div style="height:10px;border-radius:5px;overflow:hidden;display:flex;background:#1a1917;">
                    <div style="background:#81b64c;width:${winPct}%;transition:width 0.3s;" title="Win ${winPct}%"></div>
                    <div style="background:#fa412d;width:${lossPct}%;transition:width 0.3s;" title="Loss ${lossPct}%"></div>
                    <div style="background:#484542;width:${drawPct}%;transition:width 0.3s;" title="Draw ${drawPct}%"></div>
                </div>
                <div style="display:flex;justify-content:space-between;margin-top:0.5em;font-size:0.82em;font-weight:600;">
                    <span style="color:#81b64c;">W ${winPct}% <span style="font-weight:400;color:#555;">(${winCount})</span></span>
                    <span style="color:#fa412d;">L ${lossPct}% <span style="font-weight:400;color:#555;">(${lossCount})</span></span>
                    <span style="color:#888;">D ${drawPct}% <span style="font-weight:400;color:#555;">(${drawCount})</span></span>
                </div>
            </div>

            <!-- Footer -->
            <div style="padding:0 1em 0.75em;text-align:right;">
                <button id="hide-position-stats" style="font-size:0.8em;padding:0.35em 0.8em;border-radius:6px;background:#1a1917;color:#888;border:1px solid #2e2c29;cursor:pointer;transition:background 0.15s;"
                    onmouseover="this.style.background='#33312e'" onmouseout="this.style.background='#1a1917'">Hide</button>
            </div>
        </div>`;

    const hideBtn = document.getElementById('hide-position-stats');
    if (hideBtn) hideBtn.onclick = () => { container.innerHTML = ''; };
}

function handlePieceMove(orig, dest, captured) {
    console.log('Suppress move events:', suppressMoveEvents, 'Received move:', orig, dest, 'Captured piece:', captured);
    if (suppressMoveEvents) return;
    const move = `${orig}${dest}`;
    // Use the FEN from before the move was made
    const fen = currentBoardFen;
    self_played_move_list.push(move);
    const payload = {
        move_list: self_played_move_list,
        fen: fen,
        user: meta.user || null,
    };
    console.log('Sending move to backend for analysis:', payload);
    fetch('/analyze_move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
        .then(r => r.json())
        .then(data => {
            console.log('Move analysis response:', data);
            currentBoardFen = data.board;
            setShapesForMove(data.best_move_uci, move, data.classification);
        })
        .catch(err => console.error('Error sending move to backend:', err));
}

function getResponses() {
    const entry = entries[move_idx];
    if (!entry || !entry.board) return;
    const fen = entry.board;
    const user = meta.user;
    const time_control = meta.time_control;
    const playing_as_white = meta.user_playing_as_white;
    const url = `/get_total_fens_at_depth_2?` + new URLSearchParams({
        fen,
        user,
        time_control,
        playing_as_white: playing_as_white ? '1' : '0',
        substring: fen,
    }).toString();
    fetch(url)
        .then(r => r.json())
        .then(data => renderResponses(data))
        .catch(err => {
            console.error('Error fetching responses:', err);
            alert('Error fetching responses. See console for details.');
        });
}

function renderResponses(data) {
    const container = document.getElementById('responses-stats');
    if (!container) return;
    const fens = (data && data.total_fens) ? data.total_fens : [];
    if (!fens.length) {
        container.innerHTML = `<div style="padding:0.7em 1em;color:#666;font-size:0.9em;">No responses found for this position.</div>`;
        return;
    }

    const rows = fens.map(item => {
        const move = item.move || '?';
        const s = item.stats || {};
        const games = (item.games || []).length;
        const winPct = s.win_percentage || 0;
        const lossPct = s.loss_percentage || 0;
        const drawPct = s.draw_percentage || 0;
        return `
            <div style="padding:0.65em 1em;border-bottom:1px solid #2e2c29;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4em;">
                    <span style="font-size:1em;font-weight:700;color:#e8e6e3;font-family:monospace;">${move}</span>
                    <span style="font-size:0.78em;color:#666;">${games} game${games !== 1 ? 's' : ''}</span>
                </div>
                <div style="height:8px;border-radius:4px;overflow:hidden;display:flex;background:#1a1917;margin-bottom:0.35em;">
                    <div style="background:#81b64c;width:${winPct}%;transition:width 0.3s;" title="Win ${winPct}%"></div>
                    <div style="background:#fa412d;width:${lossPct}%;transition:width 0.3s;" title="Loss ${lossPct}%"></div>
                    <div style="background:#484542;width:${drawPct}%;transition:width 0.3s;" title="Draw ${drawPct}%"></div>
                </div>
                <div style="display:flex;gap:0.8em;font-size:0.8em;font-weight:600;">
                    <span style="color:#81b64c;">W ${winPct}%</span>
                    <span style="color:#fa412d;">L ${lossPct}%</span>
                    <span style="color:#888;">D ${drawPct}%</span>
                </div>
            </div>`;
    }).join('');

    container.innerHTML = `
        <div style="background:#262420;border:1px solid #353230;border-radius:14px;overflow:hidden;color:#d4d2d0;margin-top:0.4em;">
            <div style="display:flex;align-items:center;justify-content:space-between;padding:0.75em 1em;border-bottom:1px solid #2e2c29;">
                <span style="font-size:0.75em;font-weight:700;color:#666;letter-spacing:0.08em;text-transform:uppercase;">Opponent responses</span>
                <button id="hide-responses" style="font-size:0.8em;padding:0.25em 0.7em;border-radius:6px;background:#1a1917;color:#888;border:1px solid #2e2c29;cursor:pointer;"
                    onmouseover="this.style.background='#33312e'" onmouseout="this.style.background='#1a1917'">Hide</button>
            </div>
            ${rows}
        </div>`;
    document.getElementById('hide-responses').onclick = () => { container.innerHTML = ''; };
}

document.getElementById('firstMove').onclick = () => showMove(0);
document.getElementById('playBestLine').onclick = () => togglePlayBestLine();
document.getElementById('stopBestLine').onclick = () => cancelPlayingBestLine();
document.getElementById('prev').onclick = () => showMove(move_idx - 1);
document.getElementById('next').onclick = () => showMove(move_idx + 1);
document.getElementById('lastMove').onclick = () => showMove(entries.length - 1);
document.getElementById('get-position-stats').onclick = () => getPositionStats();
document.getElementById('get-responses').onclick = () => getResponses();
document.getElementById('eval-graph').addEventListener('click', function (e) {
    if (!entries.length) return;
    const rect = this.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const idx = Math.round((x / rect.width) * (entries.length - 1));
    showMove(Math.max(0, Math.min(entries.length - 1, idx)));
});
document.addEventListener('keydown', function (event) {
    if (event.key === "ArrowLeft" && move_idx > 0) showMove(move_idx - 1);
    if (event.key === "ArrowRight" && move_idx < entries.length - 1) showMove(move_idx + 1);
    if (event.key === "ArrowDown") showMove(0);
    if (event.key === "ArrowUp") showMove(entries.length - 1);
    if (event.key === 'p') togglePlayBestLine();
    if (event.key === 's') cancelPlayingBestLine();
});