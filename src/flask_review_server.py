from flask import Flask, render_template, jsonify, request
import chess
import chess.svg
from parser import Parser

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session

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
    return render_template('review.html')

if __name__ == '__main__':
    # Run on all interfaces, port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)