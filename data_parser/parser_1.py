# Högsta / lägsta accuracy
# Längsta drag 
# Snabbaste drag 
# Rating trender 
# Win % för olika öppningar / white / black 
# Win % castle, king, queen, no 
# Rating över tid
# Win % för varje timme under dygnet
# Average time win, loss, draw
# FEN longest in a game that apeared atleast twice

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

    def get_most_played_players(self, filter_info : FilterInfo) -> list[tuple]:
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

        # json_game_list = [database.convert_database_entry_to_json(json_game) for json_game in res]
        # game_list = [Game(game, filter_info.user) for game in json_game_list]
        return res
    
    
    def get_games_against_player(self, filter_info : FilterInfo, user : str):
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        res = database.query(f'''
            SELECT url 
            FROM matches
            WHERE id in ({filtered_ids}) AND opponent_user = '{user}'
        ''')
        return [url_list[0] for url_list in res]
    
    def get_total_fens_substring(self, filter_info : FilterInfo, sub_string : str):
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        res = database.query(f'''
            SELECT url,archivedate,totalFens 
            FROM matches 
            WHERE id IN ({filtered_ids}) AND totalFens like '%{sub_string}%';
        ''')
        modified_res = []
        for r in res:
            fen_list = r[2].split("&")
            index = fen_list.index(sub_string)
            # Convert tuple to list to allow modification
            r_list = list(r)
            r_list[2] = index
            modified_res.append(r_list)
        
        return modified_res
    
    def get_win_percentage_per_opening(self, filter_info : FilterInfo):
        pass

parser = Parser()
dr = FilterInfo.DateRange(datetime.now() - timedelta(days=50), datetime.now())
user_range = FilterInfo.RatingRange(0, 1000)
opponent_range = FilterInfo.RatingRange(1000, 10000)
filter_info = FilterInfo("Elias661", date_range=dr, user_range=user_range)
# res = parser.get_most_played_players(filter_info)
# for game in res :
#     print(game)

# res = parser.get_games_against_player(filter_info, "camero90")
filter_info = FilterInfo("Elias661", playing_as_white=True)

res = parser.get_total_fens_substring(filter_info, "r1bqkb1r/pppp1ppp/5n2/4P3/2Bp4/5Q2/PPPP1PPP/RNB1K2R b KQkq - 0 6")


for r in res :
    print(r)