# Get games against player
# Del av position på brädet som uppståt 
# FEN som uppståt 
# Högsta / lägsta accuracy
# Längsta drag 
# Snabbaste drag 
# Rating trender 
# Win % för olika öppningar / white / black 
# Win % castle, king, queen, no 
# Rating över tid
# Win % för varje timme under dygnet
# Average time win, loss, draw

import os
import sys
from datetime import datetime, timedelta
root_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)))
SQL_path = os.path.join(root_dir, "SQL")
database_updater_path = os.path.join(root_dir, "database_updater")
sys.path.append(SQL_path)
sys.path.append(database_updater_path)

from filter_info import FilterInfo
from database import DataBase
from game import Game

class Parser():

    def get_most_played_players(self, filter_info : FilterInfo) -> list[Game]:
        database = DataBase()

        filtered_ids = database.get_filtered_ids(filter_info)

        res = database.query(f'''
            SELECT opponent_user ,COUNT(*) as count
            FROM matches
            WHERE id IN ({filtered_ids})
            GROUP BY opponent_user
            HAVING count > 1
            ORDER BY count DESC;
        ''')
        print(res)
        exit()
        # json_game_list = [database.convert_database_entry_to_json(json_game) for json_game in res]
        # game_list = [Game(game, filter_info.user) for game in json_game_list]
        return game_list
    
    



parser = Parser()
dr = FilterInfo.DateRange(datetime.now() - timedelta(days=5), datetime.now())
user_range = FilterInfo.RatingRange(0, 1000)
filter_info = FilterInfo("Elias661", date_range=dr, user_range=user_range)
res = parser.get_most_played_players(filter_info)
for game in res :
    print(game)