import sys
import os

root_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)))
SQL_path = os.path.join(root_dir, "SQL")
database_updater_path = os.path.join(root_dir, "database_updater")
sys.path.append(SQL_path)
sys.path.append(database_updater_path)

from game import Game
from PGN_to_fen_list import extract_fens
from database import DataBase
from api import API

import json

def updateDB(user : str):
    user = user.lower()
    data_base = DataBase()
    latest_game = data_base.get_latest_game(user)

    api = API()
    
    monthly_archive = api.get_monthly_archive(user)
    for month_url in monthly_archive :
        if latest_game_date_is_after_month_url(latest_game, month_url):
            continue 
        print(month_url)
        games = api.get_games_from_month(month_url)    
        for json_game in games :

            game = Game(json_game, user)
            if game.pgn :
                fens = extract_fens(game.pgn)
                game.total_fens = fens

            data_base.insert_game(game)
            

    # print(latest_game.archive_date)

def latest_game_date_is_after_month_url(latest_game: Game, month_url: str):
    pass

updateDB("Elias661")