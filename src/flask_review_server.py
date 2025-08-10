from flask import Flask, render_template_string, jsonify, request
import chess
import chess.svg
from parser import Parser

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session

classification_colors = {
    "Best Move": "#749bbf",
    "Good Move": "#81b64c",
    "Inaccuracy": "#f7c631",
    "Mistake": "#ff7769",
    "Blunder": "#fa412d"
}

# Replace this with your real data loading logic
def get_entries(game_id, user):
    parser = Parser()
    analyze_game = parser.analyze_games_by_url(game_id, user)
    return analyze_game

@app.route('/review_data')
def review_data():
    game_id = request.args.get('id', default=None, type=int)
    user = request.args.get('user', default='', type=str)
    print(f"Fetching review data for game ID: {game_id}, user: {user}")
    response = get_entries(game_id, user)
    return jsonify(response)

@app.route('/review')
def review_page():
    return render_template_string('''
        <style>
            body { background: #302e2b; color: #c3c2c1; }
            .move-info { font-size: 1.5em; margin-bottom: 10px; background: #262522; border-radius: 16px; padding: 18px; }
            .svg-board { max-width: 350px; margin: 20px auto; display: block; text-align: center; }
            .nav-btns { text-align: center; }
        </style>
        <h2 id="game-header"></h2>
        <div class="move-info" id="move-info"></div>
        <div class="svg-board" id="svg-board"></div>
        <div class="nav-btns">
            <button id="firstMove"><--<--</button>
            <button id="prev"><--</button>
            <button id="next">--></button>
            <button id="lastMove">-->-->></button>
        </div>
        <script>
            let entries = [];
            let move_idx = 0;
            let meta = {};
            // Use safe URL encoding for query string
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
            document.addEventListener('keydown', function(event) {
                if (event.key === "ArrowLeft" && move_idx > 0) showMove(move_idx - 1);
                if (event.key === "ArrowRight" && move_idx < entries.length - 1) showMove(move_idx + 1);
                if (event.key === "ArrowDown") showMove(0);
                if (event.key === "ArrowUp") showMove(entries.length - 1);
            });
        </script>
    ''')


if __name__ == '__main__':
    app.run(debug=True)