from flask import Flask, render_template_string, session, redirect, url_for, request
import chess
import chess.svg
from parser import Parser

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session

current_game_id = 1  # Default game ID, can be changed based on your logic
analyze_game = None  # Placeholder for the game analysis logic

classification_colors = {
    "Best Move": "#749bbf",
    "Good Move": "#81b64c",
    "Inaccuracy": "#f7c631",
    "Mistake": "#ff7769",
    "Blunder": "#fa412d"
}

# Replace this with your real data loading logic
def get_entries(game_id, user):
    global current_game_id, analyze_game
    if game_id == current_game_id:
        return analyze_game
    parser = Parser()
    analyze_game = parser.analyze_games_by_url(game_id, user)
    current_game_id = game_id
    return analyze_game

@app.route('/')
def index():
    return redirect(url_for('review_move', id=1))

@app.route('/review', methods=['GET', 'POST'])
def review_move():
    game_id = request.args.get('id', default=1, type=int)
    user = request.args.get('user', default='', type=str)  # Replace with actual user logic
    entries = get_entries(game_id, user)
    if not entries:
        return "No entries found for this game ID.", 404
    move_idx = session.get(f'move_idx_{game_id}', 0)

    if request.method == 'POST':
        if 'next' in request.form and move_idx < len(entries) - 1:
            move_idx += 1
        elif 'prev' in request.form and move_idx > 0:
            move_idx -= 1
        elif 'firstMove' in request.form:
            move_idx = 0
        elif 'lastMove' in request.form:
            move_idx = len(entries) - 1
        session[f'move_idx_{game_id}'] = move_idx

    entry = entries[move_idx]
    return render_template_string('''
        <style>
            body {
                background: #302e2b;
            }
        </style>
        <h2>Game ID: {{ game_id }} | Move {{ move_idx + 1 }} / {{ total }}</h2>
        <div style="font-size: 1.5em; margin-bottom: 10px; background: #262522; border-radius: 16px; padding: 18px;">
            <span style="color:#c3c2c1"><strong>Move:</strong> {{ entry.move }}</span><br>
            <span style="color:#c3c2c1"><strong>Classification: </strong></span><span style="color: {{ classification_color }};">{{ entry.classification }}</span><br>
            <span style="color:#c3c2c1"><strong>Evaluation:</strong> {{ entry.evaluation }}</span><br>
            <span style="color:#c3c2c1"><strong>Board:</strong> {{ entry.board }}</span>
        </div>
        <div style="max-width: 350px; margin: 20px auto; display: block; text-align: center;">
            {{ entry.svg|safe }}
        </div>
        <form method="post" style="text-align: center;">
            <button name="firstMove" type="submit""><--<--</button>
            <button name="prev" type="submit" {% if move_idx == 0 %}disabled{% endif %}><--</button>
            <button name="next" type="submit" {% if move_idx == total - 1 %}disabled{% endif %}>--></button>
            <button name="lastMove" type="submit">-->-->></button>
        </form>
        <script>
            document.addEventListener('keydown', function(event) {
                if (event.key === "ArrowLeft") {
                    document.querySelector('button[name="prev"]').click();
                }
                if (event.key === "ArrowRight") {
                    document.querySelector('button[name="next"]').click();
                }
            });
        </script>
    ''', entry=entry, move_idx=move_idx, total=len(entries), game_id=game_id, classification_color=classification_colors.get(entry["classification"], "#c3c2c1"),)

if __name__ == '__main__':
    app.run(debug=True)