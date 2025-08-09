from flask import Flask, render_template_string, session, redirect, url_for, request
import chess
import chess.svg
from parser import Parser

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session

current_game_id = 1  # Default game ID, can be changed based on your logic
analyze_game = None  # Placeholder for the game analysis logic

# Replace this with your real data loading logic
def get_entries(game_id, user):
    global current_game_id, analyze_game
    if game_id == current_game_id:
        return analyze_game
    parser = Parser()
    print("asd", flush=True)
    analyze_game = parser.analyze_games_by_url(game_id, user)
    current_game_id = game_id
    return analyze_game

@app.route('/')
def index():
    print("asdasd")
    # Redirect to a default game id, e.g., 1
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
        session[f'move_idx_{game_id}'] = move_idx

    entry = entries[move_idx]
    return render_template_string('''
        <h2>Game ID: {{ game_id }} | Move {{ move_idx + 1 }} / {{ total }}</h2>
        <div style="font-size: 1.5em; margin-bottom: 10px;">
            <strong>Move:</strong> {{ entry.move }}<br>
            <strong>Classification:</strong> {{ entry.classification }}<br>
            <strong>Evaluation:</strong> {{ entry.evaluation }}<br>
            <strong>Board:</strong> {{ entry.board }}
        </div>
        <div style="max-width: 350px; margin-bottom: 20px;">
            {{ entry.svg|safe }}
        </div>
        <form method="post">
            <button name="prev" type="submit" {% if move_idx == 0 %}disabled{% endif %}>Previous</button>
            <button name="next" type="submit" {% if move_idx == total - 1 %}disabled{% endif %}>Next</button>
        </form>
    ''', entry=entry, move_idx=move_idx, total=len(entries), game_id=game_id)

if __name__ == '__main__':
    app.run(debug=True)