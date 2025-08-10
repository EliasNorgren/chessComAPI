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
from collections import defaultdict
from analyzer import Analyzer
from PGN_to_fen_list import pgn_to_move_list
from controller import DataBaseUpdater

import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import json

class Parser():

    def get_most_played_players(self, filter_info : FilterInfo) -> list[tuple]:
        database = DataBase()

        filtered_ids = database.get_filtered_ids(filter_info)
        print(f"len {len(filtered_ids)}")

        res = database.query(f'''
            SELECT opponent_user ,COUNT(*) as count
            FROM matches
            WHERE id IN ({filtered_ids})
            GROUP BY opponent_user
            HAVING count > 1
            ORDER BY count DESC;
        ''')

        json_game_list = [{"opponent":row['opponent_user'], "count":row['count']} for row in res]
        return json_game_list
    
    def __winLossOrDraw (self, result : sqlite3.Row) -> str :
        if result['user_result'] in ['win']:  
            return 'win'
        elif result['user_result'] in ['resigned', 'checkmated', 'timeout', 'abandoned'] :
            return 'loss'
        elif result['user_result'] in ['stalemate', 'insufficient', 'repetition', '50move', 'agreed', 'timevsinsufficient'] :
            return 'draw'
        else :
            for key in result.keys() :
                print(f"{key} - {result[key]}")
            print(f"Could not place result {result['user_result']} into draw, loss or win")
            exit(1)

    def __winLossOrDrawWithString (self, result : str) -> str :
        if result in ['win']:  
            return 'win'
        elif result in ['resigned', 'checkmated', 'timeout', 'abandoned'] :
            return 'loss'
        elif result in ['stalemate', 'insufficient', 'repetition', '50move', 'agreed', 'timevsinsufficient'] :
            return 'draw'
        else :
            for key in result.keys() :
                print(f"{key} - {result[key]}")
            print(f"Could not place result {result['user_result']} into draw, loss or win")
            exit(1)
    
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
            SELECT url,archivedate,totalFens, user_playing_as_white, user_result
            FROM matches 
            WHERE id IN ({filtered_ids}) AND totalFens like '%{sub_string}%';
        ''')
        modified_res = []
        for r in res:
            fen_list = r[2].split("&")
            index = 0
            for el in fen_list :
                if sub_string in el :
                    break
                index += 1         
            # Convert tuple to list to allow modification
            r_list = list(r)
            r_list[2] = index
            modified_res.append(r_list)
        response = {}
        response["games"] = modified_res

        stats = {'loss' : 0, 'win' : 0, 'draw' : 0}
        for game in modified_res :
            stats[self.__winLossOrDrawWithString(game[-1])] += 1
        
        sum = stats['draw'] + stats['loss'] + stats['win']
        stats['win_percentage'] = round((stats['win'] / sum) * 100, 2) 
        stats['loss_percentage'] = round((stats['loss'] / sum) * 100, 2) 
        stats['draw_percentage'] = round((stats['draw'] / sum) * 100, 2) 

        response['stats'] = stats
        return response
    
    def get_win_percentage_per_opening(self, filter_info : FilterInfo):
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        games = database.query(f'''
            SELECT ECO, user_result
            FROM matches
            WHERE id IN ({filtered_ids})
        ''')
        ECO = 0
        RESULT = 1
        eco_stats = defaultdict(lambda: {'win': 0, 'draw': 0, 'loss': 0, 'games':0})

        # Categorize the results
        for eco, result in games:
            if result in ['win',]:  # Assuming 'timeout' also counts as a win
                eco_stats[eco]['win'] += 1
            elif result in ['resigned', 'checkmated', 'timeout', 'abandoned']:
                eco_stats[eco]['loss'] += 1
            elif result in ['stalemate', 'insufficient', 'repetition', '50move', 'agreed', 'timevsinsufficient']:
                eco_stats[eco]['draw'] += 1
            else :
                print(f"Could not place result {result} into draw, loss or win")
            eco_stats[eco]['games'] += 1
        
        # Prepare data for plotting
        eco_codes = []
        win_counts = []
        loss_counts = []
        draw_counts = []

        for eco, stats in eco_stats.items():
            eco_codes.append(eco)
            win_counts.append(stats['win'])
            loss_counts.append(stats['loss'])
            draw_counts.append(stats['draw'])

        # Plotting
        plt.figure(figsize=(10, 6))
        bar_width = 0.2
        bar1 = plt.bar([x - bar_width for x in range(len(eco_codes))], win_counts, width=bar_width, label='Wins', color='green')
        bar2 = plt.bar(range(len(eco_codes)), loss_counts, width=bar_width, label='Losses', color='red')
        bar3 = plt.bar([x + bar_width for x in range(len(eco_codes))], draw_counts, width=bar_width, label='Draws', color='blue')

        plt.xlabel('ECO Code')
        plt.ylabel('Count')
        plt.title('Win/Loss/Draw Counts per ECO Code')
        plt.xticks(range(len(eco_codes)), eco_codes)
        plt.legend()

        # Show plot
        print("Saving plot to res.pdf")
        plt.savefig("res.pdf")

        eco_list = []
        for eco, stats in eco_stats.items():
            win_percentage = stats['win'] / stats['games'] * 100
            draw_percentage = stats['draw'] / stats['games'] * 100
            loss_percentage = stats['loss'] / stats['games'] * 100
            eco_list.append({
                'winpercentage': round(win_percentage, 2),
                'drawpercentage': round(draw_percentage, 2),
                'lossPercentage': round(loss_percentage, 2),
                'ECO': eco,
                'games': stats['games']
            })
        eco_list_sorted = sorted(eco_list, key=lambda x: x['games'], reverse=True)

        # Display the sorted list
        no_games = 0
        for item in eco_list_sorted:
            if item['games'] < 20 :
                continue
            no_games = no_games + item['games']
        return eco_list_sorted

    def get_games_by_eco(self, filter_info : FilterInfo, eco : str):
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        res = database.query(f'''
            SELECT url, archivedate, user_result
            FROM matches
            WHERE id IN ({filtered_ids}) AND ECO = "{eco}"
            ORDER BY archivedate
        ''')      
        res_dict = {}
        res_dict['games'] = []
        for game in res :
            res_dict['games'].append(f"{game[0]}, {game[1]}, {game[2]}")

        return res_dict 
    
    def get_wins_by_day_of_week(self, filter_info : FilterInfo) :
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        
        res = database.query(f'''
            SELECT *
            FROM matches
            WHERE id IN ({filtered_ids})
            ORDER BY archivedate
        ''')      

        index_to_week_day = ['mon', 'tue', 'wed', 'thu', 'fri' , 'sat', 'sun']

        stats_per_week_day = {'mon' : {}, 'tue' : {}, 'wed' : {}, 'thu' : {}, 'fri' : {}, 'sat' : {}, 'sun' : {}}
        sum = 0
        for weekday in stats_per_week_day.keys() :
            stats_per_week_day[weekday]['loss'] = 0
            stats_per_week_day[weekday]['draw'] = 0
            stats_per_week_day[weekday]['win'] = 0
            stats_per_week_day[weekday]['acc'] = 0
            stats_per_week_day[weekday]['acc_total'] = 0


            
        for game in res :
            # for key in game.keys() :
            #     print(f"{key} - {game[key]}")
            # break
            sum += 1
            archive_date = datetime.strptime(game['archiveDate'], '%Y-%m-%d %H:%M:%S')
            day_of_week = archive_date.weekday()
            stats_per_week_day[index_to_week_day[day_of_week]][self.__winLossOrDraw(game)] += 1
            acc = self.__get_accuracy(game)
            if acc != None :
                stats_per_week_day[index_to_week_day[day_of_week]]['acc'] += acc
                stats_per_week_day[index_to_week_day[day_of_week]]['acc_total'] += 1

                

        for day in index_to_week_day :
            stats_per_week_day[day]['lossPercentage'] = round((stats_per_week_day[day]['loss'] / sum) * 100, 2)
            stats_per_week_day[day]['winPercentage'] = round((stats_per_week_day[day]['win'] / sum) * 100, 2) 
            stats_per_week_day[day]['drawPercentage'] = round((stats_per_week_day[day]['draw'] / sum) * 100, 2)
            if stats_per_week_day[day]['acc_total'] != 0 :
                stats_per_week_day[day]['acc'] = round((stats_per_week_day[day]['acc'] / stats_per_week_day[day]['acc_total']) , 2)
                del(stats_per_week_day[day]['acc_total'])


        labels = index_to_week_day
        values = []
        for day in labels :
            values.append(stats_per_week_day[day]['win'])
        plt.pie(values, labels=labels, autopct='%1.1f%%')
        plt.savefig("wins_day.pdf")

        return stats_per_week_day 
    
    def get_win_percentage_and_accuracy(self, filter_info : FilterInfo) :
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        
        res = database.query(f'''
            SELECT *
            FROM matches
            WHERE id IN ({filtered_ids})
            ORDER BY archivedate
        ''')

        total_acuracy = 0
        number_of_games_with_acc = 0
        total_games = 0
        stats = {'loss' : 0, 'win' : 0, 'draw' : 0}

        for game in res :
            total_games += 1
            stats[self.__winLossOrDraw(game)] += 1
            acc = self.__get_accuracy(game)
            if  acc != None :
                total_acuracy += acc
                number_of_games_with_acc += 1
        if number_of_games_with_acc != 0 :
            acc = round((total_acuracy / number_of_games_with_acc), 2)
        else :
            acc = None
        stats["no_games"] = total_games
        stats["no_games_with_acc"] = number_of_games_with_acc
        if total_games == 0 :
            return {'accuracy' : None, 'stats' : stats}
        stats['draw'] = round((stats['draw'] / total_games) * 100 , 2) 
        stats['loss'] = round((stats['loss'] / total_games) * 100 , 2) 
        stats['win'] = round((stats['win'] / total_games) * 100 , 2) 
        return {'accuracy' : acc, 'stats' : stats}

    def __get_accuracy(self, game : dict) :
        if game['user_playing_as_white'] and game['accuracies_white'] != None :
            return game['accuracies_white']
        elif game['accuracies_black'] != None :
            return game['accuracies_black']
        return None

    def get_stats_per_day(self, filter_info : FilterInfo) :
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        
        res = database.query(f'''
            SELECT *
            FROM matches
            WHERE id IN ({filtered_ids})
            ORDER BY archivedate
        ''')
        stats_per_day = {}
        labels = []
        for game in res :
            
            archive_date = datetime.strptime(game['archiveDate'], '%Y-%m-%d %H:%M:%S').date().__str__()
            if archive_date not in stats_per_day.keys() :
                labels.append(archive_date)
                stats_per_day[archive_date] = {}
                stats_per_day[archive_date]['win'] = 0
                stats_per_day[archive_date]['loss'] = 0
                stats_per_day[archive_date]['draw'] = 0
            stats_per_day[archive_date][self.__winLossOrDraw(game)] += 1

        return stats_per_day

    def analyze_games(self, filter_info : FilterInfo, reanalyze_analyzed_games : bool):
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        games = database.query(f'''
            SELECT pgn, analysis, id, user_playing_as_white, url
            FROM matches
            WHERE id IN ({filtered_ids})        
        ''')

        analyzer = Analyzer()
        no_games = len(games)
        no_analyzed_games = 0
        print(f"Analyzing {no_games} games")
        for game in games:
            id = game['id']
            pgn = game['pgn']
            analysis = game['analysis']
            user_playing_as_white = game['user_playing_as_white']
            if not (analysis is None or reanalyze_analyzed_games):
                print(f"Game with id {id} already analyzed, skipping")

                continue
            url = game['url']
            print(f"Analyzing game {url}")
            moves = pgn_to_move_list(pgn)
            analysis = analyzer.analyze_game(moves, user_playing_as_white)
            database.update_analysis(id, analysis)
            no_analyzed_games += 1
            print(f"{(no_analyzed_games / no_games) * 100} % analyzed")

    def analyze_games_by_url(self, url : str, user: str):
        database = DataBase()
        if url != None :
            game = database.query(f'''
                SELECT pgn, analysis, id, user_playing_as_white, url, opponent_user, opponent_rating, user_rating, archiveDate
                FROM matches
                WHERE url LIKE '%{url}%' AND user = '{user}'
            ''')
            if game is None or len(game) == 0:
                print(f"No games found with url {url}, updating database for user {user}")
                DataBaseUpdater().updateDB(user)
                game = database.query(f'''
                    SELECT pgn, analysis, id, user_playing_as_white, url, opponent_user, opponent_rating, user_rating, archiveDate
                    FROM matches
                    WHERE url LIKE "%{url}%" AND user = "{user}"
                ''')
        else :
            game = database.query(f'''
                SELECT pgn, analysis, id, user_playing_as_white, url, opponent_user, opponent_rating, user_rating, archiveDate
                FROM matches
                WHERE user == "{user}" 
                ORDER BY archivedate DESC
            ''')

        if game is None or len(game) == 0:
            print(f"No games found with url {url} and user {user}")
            return

        game = game[0]  # Assuming the query returns a single game
       

        id = game['id']
        pgn = game['pgn']
        analysis = game['analysis']
        user_playing_as_white = game['user_playing_as_white']
        if analysis and analysis != "" :
            print(f"Game with id {id} already analyzed")
            return json.loads(analysis)  # Return the existing analysis if it exists
        analyzer = Analyzer()
        url = game['url']
        print(f"Analyzing game {url}")
        moves = pgn_to_move_list(pgn)
        analysis = analyzer.analyze_game(moves, user_playing_as_white)
        response = {
            "analysis": analysis,
            "opponent_user": game['opponent_user'],
            "opponent_rating": game['opponent_rating'],
            "user_rating": game['user_rating'],
            "user": user,
            "url": url,
            "archiveDate": game['archiveDate']
        }
        database.update_analysis(id, response)
        return response


# parser = Parser()
# data_range = FilterInfo.DateRange(datetime(year=2024, month=9, day=23), datetime(year=2024, month=9, day=30))
# filter_info = FilterInfo("elias661", playing_as_white = True)
# res = parser.get_most_played_players(filter_info)
# print(res)

# res = parser.get_games_by_eco(filter_info, eco="C45")

# res = parser.get_total_fens_substring(filter_info, "r1bqkbnr/pppp1ppp/8/4p3/2BnP3/5N2/PPPP1PPP/RNBQK2R")
# res = parser.get_stats_per_day(filter_info)

# print("White")
# filter_info = FilterInfo("elias661", playing_as_white = True)
# res = parser.get_win_percentage_and_accuracy(filter_info)
# for day in res :
#     print(f"{day} {res[day]}")  


# print("Black")
# filter_info = FilterInfo("elias661", playing_as_white = False)
# res = parser.get_win_percentage_and_accuracy(filter_info)
# for day in res :
#     print(f"{day} {res[day]}")  


# for r in res['games']:
#     print(r)
# print(res['stats'])

# parser.get_win_percentage_per_opening(filter_info)


