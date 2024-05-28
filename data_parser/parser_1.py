# Högsta / lägsta accuracy
# Längsta drag 
# Snabbaste drag 
# Rating trender 
# Win % för olika öppningar / white / black 
# Win % castle, king, queen, no 
# Rating över tid
# Win % för varje timme under dygnet / dag
# Average time win, loss, draw
# FEN longest in a game that apeared atleast twice
# WIN % för position

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
            SELECT url, user_result 
            FROM matches
            WHERE id in ({filtered_ids}) AND opponent_user = '{user}'
        ''')
        return [f"{url_list[0]} {url_list[1]}" for url_list in res]
    
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
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        pass
parser = Parser()
dr = FilterInfo.DateRange(datetime.now() - timedelta(days=50), datetime.now())
user_range = FilterInfo.RatingRange(0, 1000)
opponent_range = FilterInfo.RatingRange(1000, 10000)
filter_info = FilterInfo("Elias661", date_range=dr, user_range=user_range)
filter_info = FilterInfo("amraub")
res = parser.get_most_played_players(filter_info)
for game in res :
    print(game)

# res = parser.get_games_against_player(filter_info, "Elias661")

# for game in res :
#     print(game)


res = parser.get_total_fens_substring(filter_info, "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3")

for r in res :
    print(r)

filter_info = FilterInfo("Elias661")
parser.get_win_percentage_per_opening(filter_info)
