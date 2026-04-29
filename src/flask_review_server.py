from analyzer import Analyzer
from flask import Flask, render_template, jsonify, request
from parser import Parser
import uuid
import threading
import copy
import socket
from entryCache import EntryCache
from database import DataBase
from filter_info import FilterInfo
from woodpecker_db import WoodpeckerDB
from woodpecker_csv import sample_puzzles

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
        "uuid": str(new_uuid),
        "hostname": socket.gethostname()
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

@app.route('/get_unsolved_puzzle_personal')
def get_unsolved_puzzle():
    parser = Parser()
    user = request.args.get('user', default='', type=str)
    if user == '':
        return jsonify({"error": "User parameter is required"}), 400
    puzzle = parser.get_unsolved_puzzle(user)
    if puzzle == {}:
        return jsonify({"error": "No unsolved puzzle found for the given user"}), 404
    return jsonify(puzzle.__dict__)

@app.route('/set_puzzle_solved', methods=['POST'])
def set_puzzle_solved():
    database = DataBase()
    data = request.json
    puzzle_id = data.get('puzzle_id', '')
    if puzzle_id == '':
        return jsonify({"error": "User and puzzle_id parameters are required"}), 400
    success = database.mark_puzzle_as_solved(puzzle_id)
    if not success:
        return jsonify({"error": "Failed to mark puzzle as solved"}), 500
    return jsonify({"status": "success"})

@app.route('/puzzle')
def puzzle_page():
    return render_template('puzzle.html')

@app.route('/get_win_percentage_and_accuracy')
def get_win_percentage_and_accuracy():
    parser = Parser()
    fen = request.args.get('fen', default='', type=str)
    if fen == '':
        return jsonify({"error": "FEN parameter is required"}), 400
    user = request.args.get('user', default='', type=str)
    if user == '':
        return jsonify({"error": "User parameter is required"}), 400
    time_control = request.args.get('time_control', default='', type=int)
    if time_control == '':
        return jsonify({"error": "time_control parameter is required"}), 400
    playing_as_white_str = request.args.get('playing_as_white', default=None, type=str)
    playing_as_white = None
    if playing_as_white_str is not None:
        playing_as_white = playing_as_white_str == "1"

    filter_info = FilterInfo(user)
    filter_info.playing_as_white = playing_as_white
    filter_info.fen_appeared = fen
    filter_info.time_class = FilterInfo.TimeClass().time_in_seconds(time_control)    

    stats = parser.get_win_percentage_and_accuracy(filter_info)
    print(f"Stats for user {user} and FEN {fen}: {stats}")
    return jsonify(stats)

@app.route('/analyze_move', methods=['POST'])
def analyze_move():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    analyzer = Analyzer()
    fen = data.get('fen', '')
    move_list = data.get('move_list', [])
    if fen == '' or not move_list:
        return jsonify({"error": "FEN and move_list parameters are required"}), 400
    result = analyzer.analyze_position(fen, move_list)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/get_total_fens_at_depth_2', methods=['GET'])
def get_total_fens_at_depth_2():
    # Curl example: curl -G http://localhost:5000/get_total_fens_at_depth_2 --data-urlencode "user=someuser" --data-urlencode "time_control=300" --data-urlencode "playing_as_white=1" --data-urlencode "substring=some_substring"
    # Required parameters: user, time_control, playing_as_white, substring 
    substring = request.args.get('substring', default='', type=str)
    user = request.args.get('user', default='', type=str)
    if user == '':
        return jsonify({"error": "User parameter is required"}), 400
    time_control = request.args.get('time_control', default='', type=int)
    if time_control == '':
        return jsonify({"error": "time_control parameter is required"}), 400
    playing_as_white_str = request.args.get('playing_as_white', default=None, type=str)
    if playing_as_white_str is not None:
        playing_as_white = playing_as_white_str == "1"
    else:
        return jsonify({"error": "playing_as_white parameter is required"}), 400
    filter_info = FilterInfo(user)
    filter_info.playing_as_white = playing_as_white
    filter_info.time_class = FilterInfo.TimeClass().time_in_seconds(time_control)
    parser = Parser()
    total_fens = parser.get_total_fens_at_depth_2(filter_info, substring)

    return jsonify({"total_fens": total_fens})

@app.route('/woodpecker')
def woodpecker_page():
    return render_template('woodpecker.html')

@app.route('/woodpecker/puzzle')
def woodpecker_puzzle_page():
    return render_template('woodpecker_puzzle.html')

@app.route('/woodpecker/api/create_set', methods=['POST'])
def woodpecker_create_set():
    data = request.json or {}
    user       = data.get('user', '')
    name       = data.get('name', '')
    rating_min = int(data.get('rating_min', 1000))
    rating_max = int(data.get('rating_max', 1500))
    count      = min(int(data.get('count', 1000)), 2000)
    if not user or not name:
        return jsonify({"error": "user and name are required"}), 400
    puzzles = sample_puzzles(rating_min, rating_max, count)
    if not puzzles:
        return jsonify({"error": "No puzzles found in that rating range"}), 404
    db = WoodpeckerDB()
    set_id = db.create_set(user, name, rating_min, rating_max, puzzles)
    return jsonify({"set_id": set_id, "count": len(puzzles)})

@app.route('/woodpecker/api/sets')
def woodpecker_get_sets():
    user = request.args.get('user', '')
    if not user:
        return jsonify({"error": "user is required"}), 400
    return jsonify(WoodpeckerDB().get_sets(user))

@app.route('/woodpecker/api/set/<int:set_id>/start', methods=['POST'])
def woodpecker_start_attempt(set_id):
    data = request.json or {}
    user = data.get('user', '')
    if not user:
        return jsonify({"error": "user is required"}), 400
    return jsonify(WoodpeckerDB().get_or_create_attempt(set_id, user))

@app.route('/woodpecker/api/attempt/<int:attempt_id>/next')
def woodpecker_next_puzzle(attempt_id):
    set_id = request.args.get('set_id', type=int)
    if not set_id:
        return jsonify({"error": "set_id is required"}), 400
    puzzle = WoodpeckerDB().get_next_puzzle(attempt_id, set_id)
    if puzzle is None:
        return jsonify({"done": True})
    return jsonify(puzzle)

@app.route('/woodpecker/api/attempt/<int:attempt_id>/result', methods=['POST'])
def woodpecker_puzzle_result(attempt_id):
    data = request.json or {}
    set_puzzle_id = data.get('set_puzzle_id')
    if set_puzzle_id is None:
        return jsonify({"error": "set_puzzle_id is required"}), 400
    WoodpeckerDB().submit_puzzle_result(
        attempt_id, set_puzzle_id,
        bool(data.get('solved', False)),
        float(data.get('time_taken_seconds', 0))
    )
    return jsonify({"status": "ok"})

@app.route('/woodpecker/api/attempt/<int:attempt_id>/complete', methods=['POST'])
def woodpecker_complete_attempt(attempt_id):
    WoodpeckerDB().complete_attempt(attempt_id)
    return jsonify({"status": "ok"})

@app.route('/woodpecker/api/set/<int:set_id>/stats')
def woodpecker_set_stats(set_id):
    return jsonify(WoodpeckerDB().get_set_stats(set_id))

@app.route('/woodpecker/api/set/<int:set_id>', methods=['DELETE'])
def woodpecker_delete_set(set_id):
    data = request.json or {}
    user = data.get('user', '')
    if not user:
        return jsonify({"error": "user is required"}), 400
    deleted = WoodpeckerDB().delete_set(set_id, user)
    if not deleted:
        return jsonify({"error": "Set not found or not owned by user"}), 404
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Start the review Flask server')
    parser.add_argument('--debug', '-d', action='store_true', help='Run server in debug mode')
    parser.add_argument('--port', '-p', type=int, help='Port to listen on (overrides PORT/FLASK_PORT env vars)')
    args = parser.parse_args()

    entryCache = EntryCache()
    # Determine debug mode: CLI flag takes precedence, then FLASK_DEBUG env var
    debug_mode = args.debug or os.environ.get('FLASK_DEBUG', '0') in ('1', 'true', 'True')
    # Determine port: CLI arg takes precedence, then PORT env, then FLASK_PORT, then default 5000
    if args.port is not None:
        port = args.port
    else:
        port = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', '5000')))
    # Run on all interfaces
    app.run(debug=debug_mode, host='0.0.0.0', port=port)