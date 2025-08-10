let entries = [];
let move_idx = 0;
let meta = {};
let params = new URLSearchParams(window.location.search);
let url = '/review_data?' + params.toString();
console.log("Fetching review data from:", url);
fetch(url)
    .then(response => response.json())
    .then(data => {
        entries = data.analysis;
        meta = data;
        showMove(0);
    });

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
        percent = 50 - (evalClamped / 20); // 100 = black wins
    }
    percent = Math.max(0, Math.min(100, percent));
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