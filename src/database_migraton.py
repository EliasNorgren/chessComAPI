from database import DataBase
import sqlite3

databse = DataBase()

games : list[sqlite3.Row] = databse.query("SELECT id, analysis FROM matches")

print(len(games))
progress = 0
import json

for game in games:
    print(game.keys())
    print(f"Updating game {progress} of {len(games)}")
    progress += 1
    
    analysis_entry = json.loads(game['analysis'])  # convert from JSON string to dict
    moves = analysis_entry["analysis"]

    for move in moves:
        if "svg" in move:
            del move["svg"]

    # Convert back to JSON before saving, if your DB column is text
    databse.update_analysis(game["id"], json.dumps(analysis_entry))