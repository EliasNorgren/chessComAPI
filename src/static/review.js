let entries = [];
let move_idx = 0;
let meta = {};

const circle = document.getElementById('progress-ring');
const radius = circle.r.baseVal.value;
const circumference = 2 * Math.PI * radius;

circle.style.strokeDasharray = `${circumference} ${circumference}`;
circle.style.strokeDashoffset = circumference;

function setProgress(percent) {
    const offset = circumference - (percent / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    document.getElementById('loading-text').textContent = `${percent}%`;
}

// setProgress(50)

async function loadReviewData() {
    document.getElementById('svg-board').style.display = 'none';
    document.getElementById('eval-bar').style.display = 'none';

    let url = '/review_data?' + new URLSearchParams(window.location.search).toString();
    console.log("Fetching review data from:", url);
    const initialResponse = await fetch(url);
    const initialData = await initialResponse.json();
    console.log("Received review data:", initialData);
    uuid = initialData.uuid;

    loading = true;
    attempts = 0;

    while (loading && attempts < 60) {
        console.log("Waiting for review data to load... Attempt:", attempts + 1);
        try {
            const statusResponse = await fetch(`/get_entry_status?uuid=${uuid}`);
            const statusData = await statusResponse.json();
            console.log("Received status:", statusData);
            if (statusData.error) {
                console.error("Error fetching status:", statusData.error);
                break; // Exit loop on error
            }
            if (typeof statusData == "string" && statusData.includes("loading")) {

                let progressPercent = 0;
                if (!statusData.includes('loading 0')) {
                    progressPercent = statusData.substring(statusData.indexOf('(') + 1, statusData.indexOf(')') - 1);
                    progressPercent = parseInt(progressPercent, 10);
                }
                console.log("Progress percent:", progressPercent);
                setProgress(progressPercent);
                document.getElementById('loading-container').style.display = 'block';
                await sleep(2000);
                attempts++;
            } else {
                setProgress(100);
                document.getElementById('loading-container').style.display = 'none';
                document.getElementById('svg-board').style.display = '';
                document.getElementById('eval-bar').style.display = '';
                entries = statusData.analysis;
                meta = statusData;
                showMove(0);
                loading = false; // stop the loop
            }
        } catch (error) {
            console.error("Error fetching review data:", error);
            attempts++;
        }
    }

    if (attempts >= 60) {
        console.warn("Reached max attempts, stopping load.");
    }
}

loadReviewData();

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showMove(idx) {
    move_idx = idx;
    let entry = entries[move_idx];
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
    <span><strong>Accuracy:</strong> White ${meta.white_accuracy} % - Black ${meta.black_accuracy} %</span>
    `;
    document.getElementById('svg-board').innerHTML = entry.svg;
    document.getElementById('game-header').innerText =
        `Game ID: ${meta.game_id || ""} | Move ${move_idx + 1} / ${entries.length} | ${meta.archiveDate || ""} | ${meta.user || ""} (${meta.user_rating || ""}) VS ${meta.opponent_user || ""} (${meta.opponent_rating || ""})`;
    document.getElementById('prev').disabled = move_idx === 0;
    document.getElementById('firstMove').disabled = move_idx === 0;
    document.getElementById('next').disabled = move_idx === entries.length - 1;
    document.getElementById('lastMove').disabled = move_idx === entries.length - 1;

    let user_playing_as_white = meta.user_playing_as_white;
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
        evalBarStyle.height = '50vw';
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
        evalBarFillStyle.height = '50vw';
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
        "Blunder": "#fa412d"
    };
    return colors[classification] || "#c3c2c1";
}

document.getElementById('firstMove').onclick = () => showMove(0);
document.getElementById('prev').onclick = () => showMove(move_idx - 1);
document.getElementById('next').onclick = () => showMove(move_idx + 1);
document.getElementById('lastMove').onclick = () => showMove(entries.length - 1);
document.addEventListener('keydown', function (event) {
    if (event.key === "ArrowLeft" && move_idx > 0) showMove(move_idx - 1);
    if (event.key === "ArrowRight" && move_idx < entries.length - 1) showMove(move_idx + 1);
    if (event.key === "ArrowDown") showMove(0);
    if (event.key === "ArrowUp") showMove(entries.length - 1);
});