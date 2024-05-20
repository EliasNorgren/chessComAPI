import datetime
import json

class Game():
    def __init__(self, game_json : dict, user : str) -> None:
        self.user : str
        self.url : str
        self.pgn : str
        self.time_control : str
        self.end_time : int
        self.rated : bool
        self.accuracies_white : float
        self.accuracies_black : float
        self.tcn : str
        self.uuid : str
        self.initial_setup : str
        self.fen : str
        self.time_class : str
        self.rules : str
        
        self.white_rating : int
        self.white_result : str
        self.white_id : str
        self.white_username : str
        self.white_uuid : str
        
        self.black_rating : int
        self.black_result : str
        self.black_id : str
        self.black_username : str
        self.black_uuid : str
        
        self.total_fens : str
        self.archive_date : datetime.datetime

        # Assignings 
        self.user = user
        self.url = game_json["url"]
        if "pgn" not in game_json:
            print("PGN not set for game")
            self.pgn = None
            self.total_fens = None
        else:
            self.pgn = game_json["pgn"]
        self.time_control = game_json["time_control"]
        self.end_time = game_json["end_time"]
        self.rated = game_json["rated"]

        if "accuracies" in game_json :
            self.accuracies_white = game_json["accuracies"]["white"]
            self.accuracies_black = game_json["accuracies"]["black"]
        else :
            self.accuracies_white = None
            self.accuracies_black = None

        self.tcn = game_json["tcn"]
        self.uuid = game_json["uuid"]
        self.initial_setup = game_json["initial_setup"]
        self.fen = game_json["fen"]
        self.time_class = game_json["time_class"]
        self.rules = game_json["rules"]
        
        # White player
        self.white_rating = game_json["white"]["rating"]
        self.white_result = game_json["white"]["result"]
        self.white_id = game_json["white"]["@id"]
        self.white_username = game_json["white"]["username"]
        self.white_uuid = game_json["white"]["uuid"]
        
        # Black player
        self.black_rating = game_json["black"]["rating"]
        self.black_result = game_json["black"]["result"]
        self.black_id = game_json["black"]["@id"]
        self.black_username = game_json["black"]["username"]
        self.black_uuid = game_json["black"]["uuid"]
        
        # Convert UNIX timestamp to datetime object
        self.archive_date = datetime.datetime.fromtimestamp(game_json["end_time"])