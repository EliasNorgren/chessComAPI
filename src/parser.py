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
from collections import defaultdict
from analyzer import Analyzer
from PGN_to_fen_list import pgn_to_move_list
from controller import DataBaseUpdater
from entryCache import EntryCache
from puzzle_entry import PuzzleEntry
from game import Game

import chess.pgn
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import time
import json
import numpy as np
from sklearn.linear_model import LinearRegression

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
    
    def get_total_fens_at_depth_2(self, filter_info : FilterInfo, sub_string : str):
        board = chess.Board(sub_string)
        res = []
        for move in board.legal_moves :
            board.push(move)
            fen = board.fen().split(' ')[0]
            print(f"Checking FEN: {fen}")
            entry = self.get_total_fens_substring(filter_info, fen)
            print(f"Found {len(entry['games'])} games with FEN {fen}")
            if len(entry["games"]) > 0 :
                entry["move"] = move.uci() 
                res.append(entry)
            board.pop()
        res.sort(key=lambda x: len(x['games']), reverse=True)
        # Create graphs: win/draw/loss ratio per suggested move
        try:
            if len(res) > 0:
                labels = [entry.get('move', '') for entry in res]
                win_vals = []
                loss_vals = []
                draw_vals = []
                # raw counts for frequency annotation
                win_counts = []
                loss_counts = []
                draw_counts = []
                for entry in res:
                    stats = entry.get('stats', {})
                    w = stats.get('win', 0)
                    l = stats.get('loss', 0)
                    d = stats.get('draw', 0)
                    total = w + l + d
                    if total > 0:
                        win_vals.append(round((w / total) * 100, 2))
                        loss_vals.append(round((l / total) * 100, 2))
                        draw_vals.append(round((d / total) * 100, 2))
                        win_counts.append(w)
                        loss_counts.append(l)
                        draw_counts.append(d)
                    else:
                        win_vals.append(0)
                        loss_vals.append(0)
                        draw_vals.append(0)
                        win_counts.append(0)
                        loss_counts.append(0)
                        draw_counts.append(0)

                x = list(range(len(labels)))
                bar_width = 0.25
                figsize = (max(8, len(labels) * 0.6), 6)
                plt.figure(figsize=figsize)
                plt.bar([i - bar_width for i in x], win_vals, width=bar_width, label='Win %', color='green')
                plt.bar(x, loss_vals, width=bar_width, label='Loss %', color='red')
                plt.bar([i + bar_width for i in x], draw_vals, width=bar_width, label='Draw %', color='blue')
                plt.xlabel('Move (UCI)')
                plt.ylabel('Percentage (%)')
                plt.title(f'Win/Draw/Loss % for moves from FEN {sub_string}')
                plt.xticks(x, labels, rotation=45, ha='right')
                plt.legend()
                plt.tight_layout()
                # annotate bars with raw frequency counts BEFORE saving so they appear in the file
                try:
                    left_x = [i - bar_width for i in x]
                    mid_x = x
                    right_x = [i + bar_width for i in x]
                    max_pct = max(win_vals + loss_vals + draw_vals) if (win_vals + loss_vals + draw_vals) else 0
                    y_offset = max(0.5, max_pct * 0.02)
                    for idx, xi in enumerate(left_x):
                        val = win_vals[idx] if idx < len(win_vals) else 0
                        cnt = win_counts[idx] if idx < len(win_counts) else 0
                        plt.text(xi, val + y_offset, str(cnt), ha='center', va='bottom', fontsize=8)
                    for idx, xi in enumerate(mid_x):
                        val = loss_vals[idx] if idx < len(loss_vals) else 0
                        cnt = loss_counts[idx] if idx < len(loss_counts) else 0
                        plt.text(xi, val + y_offset, str(cnt), ha='center', va='bottom', fontsize=8)
                    for idx, xi in enumerate(right_x):
                        val = draw_vals[idx] if idx < len(draw_vals) else 0
                        cnt = draw_counts[idx] if idx < len(draw_counts) else 0
                        plt.text(xi, val + y_offset, str(cnt), ha='center', va='bottom', fontsize=8)
                except Exception:
                    pass
                out_fname = f"total_fens_depth2_winloss_{len(labels)}moves.pdf"
                print(f"Saving move win/draw/loss chart to {out_fname}")
                plt.savefig(out_fname)
                plt.close()
        except Exception as e:
            print(f"Could not create plots for get_total_fens_at_depth_2: {e}")

        return res


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
        if sum == 0 :
            response['stats'] = stats
            return response
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
        
        res = database.query_games(f'''
            SELECT *
            FROM matches
            WHERE id IN ({filtered_ids})
            ORDER BY archivedate
        ''')

        total_acuracy = 0
        number_of_games_with_acc = 0
        total_games = 0
        stats = {'loss' : 0, 'win' : 0, 'draw' : 0}
        total_opponent_rating = 0
        opponent_rating_stats = {'win' : 0, 'loss' : 0, 'draw' : 0}

        for game in res :
            total_games += 1
            win_loss_draw = game.winLossOrDraw()
            stats[win_loss_draw] += 1
            opponent_rating_stats[win_loss_draw] += game.opponent_rating
            acc = game.get_accuracy()
            if  acc != None :
                total_acuracy += acc
                number_of_games_with_acc += 1
            total_opponent_rating += game.opponent_rating
        if number_of_games_with_acc != 0 :
            acc = round((total_acuracy / number_of_games_with_acc), 2)
        else :
            acc = None
        stats["no_games"] = total_games
        stats["no_games_with_acc"] = number_of_games_with_acc
        if total_games == 0 :
            return {'accuracy' : None, 'stats' : stats}
        
        opponent_rating_stats['win'] = round((opponent_rating_stats['win'] / stats['win']) , 2) if stats['win'] != 0 else 0
        opponent_rating_stats['loss'] = round((opponent_rating_stats['loss'] / stats['loss']) , 2) if stats['loss'] != 0 else 0
        opponent_rating_stats['draw'] = round((opponent_rating_stats['draw'] / stats['draw']) , 2) if stats['draw'] != 0 else 0
        stats['draw'] = round((stats['draw'] / total_games) * 100 , 2) 
        stats['loss'] = round((stats['loss'] / total_games) * 100 , 2) 
        stats['win'] = round((stats['win'] / total_games) * 100 , 2)
        stats['average_opponent_rating'] = round((total_opponent_rating / total_games), 2)
        stats['average_opponent_rating_per_result'] = opponent_rating_stats
        return {'accuracy' : acc, 'stats' : stats}

   # Deprecated
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

    # def analyze_games(self, filter_info : FilterInfo, reanalyze_analyzed_games : bool):
    #     database = DataBase()
    #     filtered_ids = database.get_filtered_ids(filter_info)
    #     games = database.query(f'''
    #         SELECT pgn, analysis, id, user_playing_as_white, url
    #         FROM matches
    #         WHERE id IN ({filtered_ids})        
    #     ''')

    #     analyzer = Analyzer()
    #     no_games = len(games)
    #     no_analyzed_games = 0
    #     print(f"Analyzing {no_games} games")
    #     for game in games:
    #         id = game['id']
    #         pgn = game['pgn']
    #         analysis = game['analysis']
    #         user_playing_as_white = game['user_playing_as_white']
    #         if not (analysis is None or reanalyze_analyzed_games):
    #             print(f"Game with id {id} already analyzed, skipping")

    #             continue
    #         url = game['url']
    #         print(f"Analyzing game {url}")
    #         moves = pgn_to_move_list(pgn)
    #         analysis = analyzer.analyze_game(moves, user_playing_as_white)
    #         database.update_analysis(id, analysis)
    #         no_analyzed_games += 1
    #         print(f"{(no_analyzed_games / no_games) * 100} % analyzed")

    def analyze_games_by_url(self, url : str, user: str, entryCache: EntryCache, uuid : str) -> dict:
        database = DataBase()
        if url != None :
            game = database.query(f'''
                SELECT pgn, analysis, id, user_playing_as_white, url, opponent_user, opponent_rating, user_rating, archiveDate, time_control, user_result, opponent_result, puzzles_calculated
                FROM matches
                WHERE url LIKE '%{url}%' AND user = '{user}'
            ''')
            if game is None or len(game) == 0:
                print(f"No games found with url {url}, updating database for user {user}")
                DataBaseUpdater().updateDB(user)
                game = database.query(f'''
                    SELECT pgn, analysis, id, user_playing_as_white, url, opponent_user, opponent_rating, user_rating, archiveDate, time_control, user_result, opponent_result, puzzles_calculated
                    FROM matches
                    WHERE url LIKE "%{url}%" AND user = "{user}"
                ''')
        else :
            print(f"No url provided, fetching latest game for user {user}")
            DataBaseUpdater().updateDB(user)
            game = database.query(f'''
                SELECT pgn, analysis, id, user_playing_as_white, url, opponent_user, opponent_rating, user_rating, archiveDate, time_control, user_result, opponent_result, puzzles_calculated
                FROM matches
                WHERE user == "{user}" 
                ORDER BY archivedate DESC
            ''')

        if game is None or len(game) == 0:
            print(f"No games found with url {url} and user {user}")
            return

        game = game[0]  # Assuming the query returns a single game
        return self.analyze_game(game, database, user, entryCache, uuid)

    def analyze_game(self, game, database: DataBase, user : str, 
                     entryCache : EntryCache = None, uuid = None) -> dict:
        id = game['id']
        pgn = game['pgn']
        analysis = game['analysis']
        user_playing_as_white = game['user_playing_as_white']
        if analysis and analysis != "" :
            if not game['puzzles_calculated'] :
                print(f"Game with id {id} already analyzed, adding puzzles to db")
                self.add_puzzles_to_db(json.loads(analysis), id, database)
            else :
                print(f"Game with id {id} already analyzed")
            return json.loads(analysis)  # Return the existing analysis if it exists
        chess_960_mode = chess.pgn.read_game(StringIO(pgn)).headers.get("Variant", "") == "Chess960"
        analyzer = Analyzer(chess_960_mode)
        url = game['url']
        print(f"Analyzing game {url}")
        moves = pgn_to_move_list(pgn)
        time_control = game['time_control']
        if '+' in time_control:
            time_control = time_control.split('+')[0]
        time_control = int(time_control)
        analysis = analyzer.analyze_game(moves, user_playing_as_white, entryCache, uuid)
        white_accuracy, black_accuracy, classification_frequency = self.average_accuracy(analysis)
        user_time, user_total_score, opponent_time, opponent_total_score = self.compute_total_times(analysis, time_control, user_playing_as_white)
        response = {
            "analysis": analysis,
            "opponent_user": game['opponent_user'],
            "opponent_rating": game['opponent_rating'],
            "user_rating": game['user_rating'],
            "user": user,
            "url": url,
            "archiveDate": game['archiveDate'],
            "user_playing_as_white": user_playing_as_white,
            "white_accuracy": white_accuracy,
            "black_accuracy": black_accuracy,
            "classification_frequency": classification_frequency,
            "time_control": time_control,
            "user_result": game["user_result"],
            "opponent_result": game["opponent_result"],
            "user_time": user_time,
            "opponent_time": opponent_time,
            "user_total_score": user_total_score,
            "opponent_total_score": opponent_total_score,
            "user_score_per_min": 0 if user_time <= 0 else round(user_total_score / (user_time / 60), 2),
            "opponent_score_per_min": 0 if opponent_time <= 0 else round(opponent_total_score / (opponent_time / 60), 2)
        }
        database.update_analysis(id, response)
        self.add_puzzles_to_db(response, id, database)
        analyzer.close_engine()
        return response

    def compute_total_times(self, analysis, time_control, user_playing_as_white) :
        white_time = 0
        black_time = 0
        black_total_score = 0
        white_total_score = 0
        white_turn = True
        for move in analysis :
            move_time = move["clock_time"]
            move_score = move["score"]
            if white_turn :
                white_time = time_control - move_time
                white_total_score += move_score 
            else :
                black_time = time_control - move_time
                black_total_score += move_score
            white_turn = not white_turn
        white_time = round(white_time, 2)
        black_time = round(black_time, 2)
        white_total_score = round(white_total_score, 2)
        black_total_score = round(black_total_score, 2)
        if user_playing_as_white :
            return white_time, white_total_score, black_time, black_total_score
        else :
            return black_time, black_total_score, white_time, white_total_score


    def average_accuracy(self, analysis) -> (float, float, dict):  # type: ignore
        classification_frequency = {
            "white" : {
                    "Best Move": 0,
                    "Good Move": 0,
                    "Inaccuracy": 0,
                    "Mistake": 0,
                    "Blunder": 0,
                    "Missed mate": 0
            },
            "black" : {
                    "Best Move": 0,
                    "Good Move": 0,
                    "Inaccuracy": 0,
                    "Mistake": 0,
                    "Blunder": 0,
                    "Missed mate": 0
            }
        }
        
        white_total_acc = 0
        black_total_acc = 0
        white_no_moves = 0
        black_no_moves = 0
        white_turn = True

        for move in analysis:
            turn = "white" if white_turn else "black"
            if move.get('classification') is not None and move['classification'] in classification_frequency[turn]:
                classification_frequency[turn][move['classification']] += 1
            else :
                classification_frequency[turn]['Other'] = classification_frequency.get('Other', 0) + 1

            if 'score' in move and move['score'] is not None:
                if white_turn:
                    white_total_acc += move['score']
                    white_no_moves += 1
                else:
                    black_total_acc += move['score']
                    black_no_moves += 1
            white_turn = not white_turn

        # Calculate averages
        white_acc = round((white_total_acc * 100) / white_no_moves, 2) if white_no_moves > 0 else 0.0
        black_acc = round((black_total_acc * 100) / black_no_moves, 2) if black_no_moves > 0 else 0.0

        return white_acc, black_acc, classification_frequency
    
    def get_blunders(self, filter_info: FilterInfo) -> list[dict]:
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        

        games_with_blunders = database.query(f'''
            SELECT analysis
            FROM matches
            WHERE id IN ({filtered_ids}) AND
            analysis LIKE "%blunder%"     
        ''')
        result = []
        for game in games_with_blunders :
            meta_data = json.loads(game["analysis"])
            user_playing_as_white = meta_data["user_playing_as_white"]
            analysis = meta_data['analysis']
            user_turn = user_playing_as_white
            for move in analysis :
                move : dict
                if not user_turn :
                    user_turn = not user_turn
                    continue
                classification = move["classification"]
                if classification == "Missed mate"  :
                    result.append({
                        "user_move": move["move"],
                        "user_move_uci": move["uci_move"],
                        "board_fen": move["board"],
                        "board_before_move": move["board_before_move"],
                        "best_move": move["best_move"][0],
                        "best_move_uci": move["best_move_uci"],
                    })
                user_turn = not user_turn
        return result
    
    def analyze_games_for_user(self, filter_info: FilterInfo, analyzer: Analyzer) :
        user = filter_info.user
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        games = database.query(f'''
            SELECT pgn, analysis, id, user_playing_as_white, url, opponent_user, opponent_rating, user_rating, archiveDate, time_control, user_result, opponent_result, initial_setup, puzzles_calculated
            FROM matches
            WHERE id IN ({filtered_ids}) AND
            (analysis == "" OR puzzles_calculated == 0)
            ORDER BY archiveDate DESC
        ''')
        len_before = len(games)
        games = list(filter(lambda game : not (game["pgn"] == None or game["pgn"] == ""), games))
        no_games = len(games)
        if len_before != no_games :
            print(f"Removed {len_before - no_games} games that missed the PGN column.")
        len_before = len(games)
        games = list(filter(lambda game : not chess.pgn.read_game(StringIO(game["pgn"])).headers.get("Variant", "") == "Chess960", games))
        no_games = len(games)
        if len_before != no_games :
            print(f"Removed {len_before - no_games} games that were chess960.")
        len_before = len(games)
        games = list(filter(lambda game: self.has_all_32_pieces(game["initial_setup"]), games))
        no_games = len(games)
        if len_before != no_games :
            print(f"Removed {len_before - no_games} games that did not have all 32 pieces in the initial position.")

        done = 0
        time_taken = 0
        for game in games :
            print(f"Analyzing game from {game["archiveDate"]}")
            start_time = time.time()
            self.analyze_game(game, database, user, analyzer)
            time_taken += time.time() - start_time
            done += 1
            avg_time = round(time_taken / done, 2)
            time_remaining = round(((no_games - done) * avg_time) / 60, 2)
            print(f"Progress: {done} / {no_games} - Average time per game {avg_time} seconds.")
            print(f"Estimated time remaining: {time_remaining} minutes: {(datetime.now() + timedelta(minutes=time_remaining)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"DB size: {database.get_db_size()} MB")

    def has_all_32_pieces(self, fen: str) -> bool:
        """
        Check if a FEN string has exactly 32 pieces on the board.

        Args:
            fen (str): The FEN string.

        Returns:
            bool: True if there are 32 pieces, False otherwise.
        """
        # First field of FEN describes the board
        if fen is None or fen == "" :
            return False
        board = fen.split()[0]
        # Count all letters (pieces) -> ignore digits and slashes
        piece_count = sum(1 for c in board if c.isalpha())
        return piece_count == 32
    
    def add_puzzles_to_db(self, game_analysis_entry : dict, game_id : int, database : DataBase):
        puzzles = []
        user_playing_as_white = game_analysis_entry['user_playing_as_white']
        white_turn = True
        last_move = None
        for move in game_analysis_entry['analysis']:
            
            if (white_turn and not user_playing_as_white) or (not white_turn and user_playing_as_white) :
                white_turn = not white_turn
                continue
            if not (move.get('classification') in ['Blunder', 'Missed mate']):
                white_turn = not white_turn
                continue

            mate_in_best_move = None
            if last_move and move['classification'] == "Missed mate":
                mate_in_best_move = move['best_move'][0].get('Mate', None)
 
            puzzle = PuzzleEntry(
                fen=move['board_before_move'],
                best_move_uci=move['best_move'][0]['Move'],
                best_move_san=None,
                user_move_san=move['move'],
                user_move_uci=move['uci_move'],
                classification=move['classification'],
                centipawn_best_move=move['best_move'][0]['Centipawn'],
                mate_in_best_move=mate_in_best_move,
                user_playing_as_white=user_playing_as_white,
                game_id=game_id,
                solution_line=move['best_move'][0]['Line']
            )
            puzzles.append(puzzle)
            last_move = move
            white_turn = not white_turn

        if puzzles :
            if database.insert_puzzles(puzzles) :
                database.set_matches_puzzles_calculated(game_id, True)
                print(f"Inserted {len(puzzles)} puzzles for game id {game_id}")
        else :
            database.set_matches_puzzles_calculated(game_id, True)
            print(f"No puzzles found for game id {game_id}")

    def get_unsolved_puzzle(self, user: str) -> dict :
        database = DataBase()
        puzzle : PuzzleEntry = database.get_unsolved_puzzle(user)
        if puzzle is None :
            return {}
        return puzzle
    
    def update_rating_accuracy_regression_parameters(self, filter_info : FilterInfo) :
        database = DataBase()
        filtered_ids = database.get_filtered_ids(filter_info)
        games = database.query_games(f'''
            SELECT * from matches
            WHERE id IN ({filtered_ids}) AND
            analysis IS NOT NULL AND
            analysis != ""
        ''')
        x = []
        y = []
        for game in games :
            analysis = game.analysis
            user_playing_as_white = analysis['user_playing_as_white']
            if user_playing_as_white :
                opponent_accuracy = analysis['black_accuracy']
            else :
                opponent_accuracy = analysis['white_accuracy']
            opponent_rating = game.opponent_rating
            x.append(opponent_rating)
            y.append(opponent_accuracy)
            if opponent_accuracy < 20 :
                print(f"Game {game.url} has opponent accuracy {opponent_accuracy} and opponent rating {opponent_rating}")
        if len(x) == 0 :
            print("No games with analysis found for the given filter, cannot update regression parameters.")
            return
       
        # Perform linear regression
        X = np.array(x).reshape(-1, 1)
        y = np.array(y)
        model = LinearRegression()
        model.fit(X, y)
        slope = model.coef_[0]
        intercept = model.intercept_
        print(f"Updated regression parameters: slope = {slope}, intercept = {intercept}")
       
        # Create a graph of opponent rating vs opponent accuracy and save it to a file
        plt.figure(figsize=(10, 6))
        plt.scatter(x, y, alpha=0.5)
        plt.plot(X, model.predict(X), color='red')  # Regression line
        plt.xlabel('Opponent Rating')
        plt.ylabel('Opponent Accuracy')
        plt.title('Opponent Rating vs Opponent Accuracy')
        plt.savefig('rating_accuracy_regression.pdf')
        plt.close()


            


# database = DataBase()
# game_row_analysis = json.loads(database.get_game_by_id(8716)['analysis'])
# print(type(game_row_analysis))
# parser = Parser()
# filter_info = FilterInfo(user=None)
# parser.update_rating_accuracy_regression_parameters(filter_info)
# parser.add_puzzles_to_db(game_row_analysis, 8716, database)