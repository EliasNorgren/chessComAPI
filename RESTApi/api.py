
from sys import path
import os
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR) + "/data_parser")
# print(path)


from flask import Flask, request, jsonify
from flask_cors import CORS
from filter_info import FilterInfo
from parser import Parser

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
    

    # Process the data as needed
    # For example, printing to the console
    print(f"User: {user}")
    print(f"User Rating Range: {user_range_min} - {user_range_max}")
    print(f"Opponent Rating Range: {opponent_range_min} - {opponent_range_max}")
    print(f"Date Range: {date_range_start} - {date_range_end}")
    print(f"Time Control Range: {time_control_min} - {time_control_max}")
    print(f"Rated: {rated}")
    print(f"Playing as White: {playing_as_white}")


@app.route('/refresh', methods=['POST'])
def filter():
    data = request.get_json()  # Get the JSON data sent from the frontend
    filter_info = create_filter_info(data)
    
    # Return a response back to the frontend
    return jsonify({"message": "Filter data received successfully!"}), 200

@app.route('/update', methods=['GET'])
def updateDB():
    print("Updating DB")
    
    return jsonify({"message": "Updated DB!"}), 200
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
