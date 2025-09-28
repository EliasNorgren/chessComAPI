from analyzer import Analyzer
from flask import Flask, render_template, jsonify, request
from parser import Parser
import uuid
import threading
import copy
from entryCache import EntryCache

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session
entryCache : EntryCache = None

def calculate_entries(game_id, user, uuid, head_minus):
    print(f"Fetching review data for game ID: {game_id}, user: {user}")
    global entryCache, analyzer
    parser = Parser()
    analyze_game = parser.analyze_games_by_url(game_id, user, entryCache, uuid)
    entryCache.set_entry(uuid, analyze_game)

@app.route('/review_data')
def review_data():
    global entryCache
    new_uuid = str(uuid.uuid4())
    entryCache.set_entry(new_uuid, "loading 0") 
    game_id = request.args.get('id', default=None, type=int)
    user = request.args.get('user', default='', type=str)
    head_minus = request.args.get('head_minus', default=0, type=int)
    if user == '':
        return jsonify({"error": "User parameter is required"}), 400
    threading.Thread(target=calculate_entries, args=(game_id, user, new_uuid, head_minus)).start()
    response = {
        "uuid": str(new_uuid)
    }
    return jsonify(response)

@app.route('/get_entry_status')
def get_entry_status():
    global entryCache
    uuid_str = request.args.get('uuid', default=None, type=str)
    if not uuid_str or uuid_str == '':
        return jsonify({"error": "UUID parameter is required"}), 400
    entry = entryCache.get_entry(uuid_str)
    entry_copy = None
    if entry is not None and isinstance(entry, str) and "loading" in entry:
        entry_copy = entry
    else:
        entry_copy = copy.deepcopy(entry)
        entryCache.drop_entry(uuid_str)
    if entry_copy is None:
        return jsonify({"error": "No entry found for the given UUID"}), 404
    return jsonify(entry_copy)

@app.route('/review')
def review_page():
    return render_template('review.html')

@app.route('/board_test')
def board_test():
    return render_template('board_test.html')

@app.route('/get_unsolved_puzzle')
def get_unsolved_puzzle():
    parser = Parser()
    user = request.args.get('user', default='', type=str)
    if user == '':
        return jsonify({"error": "User parameter is required"}), 400
    puzzle = parser.get_unsolved_puzzle(user)
    if puzzle == {}:
        return jsonify({"error": "No unsolved puzzle found for the given user"}), 404
    return jsonify(puzzle.__dict__)

if __name__ == '__main__':
    entryCache = EntryCache()
    # Run on all interfaces, port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)