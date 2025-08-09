
from sys import path
import os
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR) + "/data_parser")
sys.path.append(os.path.dirname(CURRENT_DIR) + "/database_updater")

print(path)

from flask import Flask, request, jsonify
from flask_cors import CORS
from filter_info import FilterInfo
from parser import Parser
from controller import DataBaseUpdater
import datetime
import json

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

def create_filter_info(data) -> FilterInfo :
    user = data.get('user')
    date_range_end = data.get("dateRangeEnd")
    date_range_start = data.get("dateRangeStart")
    opponent_range_max = data.get("opponentRangeMax")
    opponent_range_min = data.get("opponentRangeMin")
    playing_as_white = data.get("playingAsWhite")
    rated = data.get("rated")
    time_control_max = data.get("timeControlMax")
    time_control_min = data.get("timeControlMin")
    user_range_min = data.get("userRangeMin")
    user_range_max = data.get("userRangeMax")

    time_control_range : FilterInfo.TimeControl
    time_control_range = None
    if time_control_min != None and time_control_max != None:
        time_control_range = FilterInfo.TimeControl(time_control_min, time_control_max)

    opponent_range = None
    if opponent_range_max != None and opponent_range_min != None :
        opponent_range = FilterInfo.RatingRange(opponent_range_min, opponent_range_max)
    rating_range = None
    if user_range_min != None and user_range_max != None :
        rating_range = FilterInfo.RatingRange(user_range_min, user_range_max)

    date_range = None
    if date_range_start != None and date_range_end != None and len(date_range_start) > 0 and len(date_range_end) > 0:
        date_range = FilterInfo.DateRange(datetime.datetime.strptime(date_range_start, "%Y-%m-%d"), 
                                          datetime.datetime.strptime(date_range_end, "%Y-%m-%d"))

    filter_info = FilterInfo(user, rating_range, opponent_range, date_range, time_control_range, rated, playing_as_white)
    print(filter_info)

    return filter_info

@app.route('/refresh', methods=['POST'])
def filter():
    data = request.get_json()  # Get the JSON data sent from the frontend
    filter_info = create_filter_info(data)
    parser = Parser()
    response = {}

    games_played_against_player = parser.get_most_played_players(filter_info)
    response["games_played_against_player"] = games_played_against_player
    
    response["message"] =  "Filter data received successfully!"
    # Return a response back to the frontend
    return jsonify(response), 200

@app.route('/update', methods=['POST'])
def updateDB():
    data = request.get_json()
    user = data.get("user")
    updater = DataBaseUpdater()
    games = updater.updateDB(user)
    print(f"Updating DB {user}")
    
    return jsonify({"message": f"Updated {user} with {games} new games!"}), 200
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
