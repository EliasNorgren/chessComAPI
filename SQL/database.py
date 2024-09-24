from game import Game
import sqlite3
from filter_info import FilterInfo
import datetime

class DataBase():
    def __init__(self) -> None:
        self.database_file_path = "SQL/chess_games.db"

    def get_filtered_ids(self, filter_info : FilterInfo) -> str:
        
        ids = self.get_all_ids(filter_info)
        if filter_info.date_range == None :
            filter_info.date_range = FilterInfo.DateRange(datetime.datetime.min, datetime.datetime.max)
        query = f'''
            SELECT id FROM matches WHERE 
                archiveDate > ? AND archiveDate < ? 
                AND id IN ({ids})
        '''
        params = (filter_info.date_range.start_date, filter_info.date_range.end_date)
        ids = self.do_filter_query(query, params)

        if filter_info.user_rating_range != None :
            query = f'''
                SELECT id FROM matches
                WHERE user_rating > ? AND user_rating < ? 
                AND id in({ids})
            '''
            params = (filter_info.user_rating_range.start, filter_info.user_rating_range.end)
            ids = self.do_filter_query(query, params)

        if filter_info.opponent_rating_range != None :
            query = f'''
                SELECT id FROM matches
                WHERE opponent_rating > ? AND opponent_rating < ? 
                AND id in({ids})
            '''
            params = (filter_info.opponent_rating_range.start, filter_info.opponent_rating_range.end)
            ids = self.do_filter_query(query, params)

        if filter_info.playing_as_white != None :
            query = f'''
                SELECT id FROM matches
                WHERE user_playing_as_white = ? 
                AND id in({ids})
            '''
            params = (filter_info.playing_as_white,)
            ids = self.do_filter_query(query, params)            

        if filter_info.rated != None :
            query = f'''
                SELECT id FROM matches
                WHERE rated = ? 
                AND id in({ids})
            '''
            params = (filter_info.rated,)
            ids = self.do_filter_query(query, params)       

        return ids

    def get_all_ids(self, filter_info : FilterInfo) :
        conn = sqlite3.connect(self.database_file_path)
        cursor = conn.cursor()
        query = f'''
            SELECT id FROM matches WHERE user = "{filter_info.user}"
        '''
        cursor.execute(query)
        results = cursor.fetchall()
        ids = [item[0] for item in results]
        ids_str = ','.join(map(str, ids))
        return ids_str

    def do_filter_query(self, query : str, params) :
        
        conn = sqlite3.connect(self.database_file_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        ids = [item[0] for item in results]
        ids_str = ','.join(map(str, ids))
        return ids_str

    def query(self, query_string: str):
        conn = sqlite3.connect(self.database_file_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        results = None
        try:
            cursor.execute(query_string)  # Execute the query
            results = cursor.fetchall()   # Fetch all the results
        except sqlite3.Error as e:
            print(f"Error querying: {e}, {query_string}")
        finally:
            conn.close()  # Ensure the connection is closed
            return results  # Return the results
    
    def get_latest_game(self, user : str) -> Game :
        # Connect to the database
        conn = sqlite3.connect(self.database_file_path)
        cursor = conn.cursor()

        # Query to get the latest entry based on archiveDate
        cursor.execute(f'''
        SELECT * FROM matches
        WHERE user = '{user}'
        ORDER BY archiveDate DESC
        LIMIT 1
        ''')

        # Fetch the result
        latest_entry = cursor.fetchone()

        if latest_entry :
            game = Game(self.convert_database_entry_to_json(latest_entry), user)
            conn.close()
            return game

        # Close the connection
        conn.close()

        # Return the result
        return None
    
    def insert_game(self, game : Game) :
        conn = sqlite3.connect(self.database_file_path)
        cursor = conn.cursor()

        try:
            # SQL INSERT statement
            insert_statement = '''
            INSERT INTO matches (
                user, url, pgn, time_control, end_time, rated, accuracies_white, accuracies_black,
                tcn, uuid, initial_setup, fen, time_class, rules,
                white_rating, white_result, white_id, white_username, white_uuid,
                black_rating, black_result, black_id, black_username, black_uuid,
                totalFens, archiveDate, user_playing_as_white, user_rating, opponent_rating, user_result, 
                opponent_result, opponent_user, ECO, ECOurl
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

            # Values to be inserted
            values = (
                game.user, game.url, game.pgn, game.time_control, game.end_time, game.rated,
                game.accuracies_white, game.accuracies_black, game.tcn, game.uuid,
                game.initial_setup, game.fen, game.time_class, game.rules,
                game.white_rating, game.white_result, game.white_id, game.white_username, game.white_uuid,
                game.black_rating, game.black_result, game.black_id, game.black_username, game.black_uuid,
                game.total_fens, game.archive_date, game.user_playing_as_white, game.user_rating, game.opponent_rating,
                game.user_result, game.opponent_result, game.opponent_user, game.ECO, game.ECOurl
            )

            # Execute the INSERT statement
            cursor.execute(insert_statement, values)

            # Commit changes to the database
            conn.commit()
            # print("Game inserted successfully.")

        except sqlite3.Error as e:
            print(f"Error inserting game: {e}")
            print(game)
        except sqlite3.IntegrityError:
            print("Game with the same uuid already exists. Skipping insertion.")

        finally:
            # Close the connection
            conn.close()

    def convert_database_entry_to_json(self, db_entry):
        return {
            "url": db_entry[2],
            "pgn": db_entry[3],
            "time_control": db_entry[4],
            "end_time": db_entry[5],
            "rated": db_entry[6],
            "accuracies": {
                "white": db_entry[7],
                "black": db_entry[8]
            },
            "tcn": db_entry[9],
            "uuid": db_entry[10],
            "initial_setup": db_entry[11],
            "fen": db_entry[12],
            "time_class": db_entry[13],
            "rules": db_entry[14],
            "white": {
                "rating": db_entry[15],
                "result": db_entry[16],
                "@id": db_entry[17],
                "username": db_entry[18],
                "uuid": db_entry[19]
            },
            "black": {
                "rating": db_entry[20],
                "result": db_entry[21],
                "@id": db_entry[22],
                "username": db_entry[23],
                "uuid": db_entry[24]
            },
            "total_fens": db_entry[25],
            "archive_date": db_entry[26],
            "user_playing_as_white": db_entry[27],
            "user_rating": db_entry[28],
            "opponent_rating": db_entry[29],
            "user_result": db_entry[30],
            "opponent_result": db_entry[31],
            "opponent_user": db_entry[32]
        }
    
