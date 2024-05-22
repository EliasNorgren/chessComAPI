from game import Game
import sqlite3


class DataBase():
    def __init__(self) -> None:
        self.database_file_path = "SQL/chess_games.db"

    
    def get_latest_game(self, user : str) -> Game :
        # Connect to the database
        conn = sqlite3.connect(self.database_file_path)
        cursor = conn.cursor()

        # Query to get the latest entry based on archiveDate
        cursor.execute('''
        SELECT * FROM matches
        ORDER BY archiveDate DESC
        LIMIT 1
        ''')

        # Fetch the result
        latest_entry = cursor.fetchone()

        if latest_entry :
            game = Game(self.__convert_database_entry_to_json(latest_entry), user)
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
                opponent_result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

            # Values to be inserted
            values = (
                game.user, game.url, game.pgn, game.time_control, game.end_time, game.rated,
                game.accuracies_white, game.accuracies_black, game.tcn, game.uuid,
                game.initial_setup, game.fen, game.time_class, game.rules,
                game.white_rating, game.white_result, game.white_id, game.white_username, game.white_uuid,
                game.black_rating, game.black_result, game.black_id, game.black_username, game.black_uuid,
                game.total_fens, game.archive_date, game.user_playing_as_white, game.user_rating, game.opponent_rating,
                game.user_result, game.opponent_result
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

    def __convert_database_entry_to_json(self, db_entry):
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
                "archive_date": db_entry[26]
            }
    
