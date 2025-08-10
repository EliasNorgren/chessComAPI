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
    document.getElementById('move-info').innerHTML = `
        <span><strong>Move:</strong> ${entry.move}</span><br>
        <span><strong>Classification:</strong> <span style="color:${getColor(entry.classification)}">${entry.classification}</span></span><br>
        <span><strong>Evaluation:</strong> ${JSON.stringify(entry.evaluation)}</span><br>
        <span><strong>Board:</strong> ${entry.board}</span>
    `;
    document.getElementById('svg-board').innerHTML = entry.svg;
    document.getElementById('game-header').innerText =
        `Game ID: ${meta.game_id || ""} | Move ${move_idx + 1} / ${entries.length} | ${meta.archiveDate || ""} | ${meta.user || ""} (${meta.user_rating || ""}) VS ${meta.opponent_user || ""} (${meta.opponent_rating || ""})`;
    document.getElementById('prev').disabled = move_idx === 0;
    document.getElementById('firstMove').disabled = move_idx === 0;
    document.getElementById('next').disabled = move_idx === entries.length - 1;
    document.getElementById('lastMove').disabled = move_idx === entries.length - 1;
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