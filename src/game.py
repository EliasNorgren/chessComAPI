import datetime
import json
import copy
import chess.pgn
from io import StringIO

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
            print("PGN not set for game (Ignoring to insert this value)")
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

        self.user_playing_as_white : bool
        self.user_rating : int
        self.opponent_rating : int
        self.user_result : str
        self.opponent_result : str
        self.opponent_user : str
        if game_json["white"]["username"].lower() == user :
            self.user_playing_as_white = True
            self.user_rating =  game_json["white"]["rating"]
            self.opponent_rating = game_json["black"]["rating"]
            self.user_result = game_json["white"]["result"]
            self.opponent_result = game_json["black"]["result"]
            self.opponent_user = game_json["black"]["username"]
        elif game_json["black"]["username"].lower() == user :
            self.user_playing_as_white = False
            self.user_rating = game_json["black"]["rating"]
            self.opponent_rating = game_json["white"]["rating"]
            self.user_result = game_json["black"]["result"]
            self.opponent_result = game_json["white"]["result"]
            self.opponent_user = game_json["white"]["username"]
        else :
            print("Error user not found playing as either black or white")
            print(json.dumps(game_json, indent=2))
            exit(0)

        self.ECO : str = None
        self.ECOurl : str = None
        
        if self.pgn != None :       
            gamePGN = chess.pgn.read_game(StringIO(game_json["pgn"]))
            if gamePGN and "ECO" in gamePGN.headers :
                self.ECO = gamePGN.headers["ECO"]
            if gamePGN and "ECOUrl" in gamePGN.headers :
                self.ECOurl = gamePGN.headers["ECOUrl"]
        
        try:
            self.analysis : dict = json.loads(game_json["analysis"]) if "analysis" in game_json else None
        except json.JSONDecodeError:
            print("Error: " + game_json["analysis"])
            self.analysis = None
        self.puzzles_calculated : bool = game_json["puzzles_calculated"] if "puzzles_calculated" in game_json else None

    def __str__(self) -> str:
        selfCopy = copy.deepcopy(self)
        selfCopy.archive_date = str(selfCopy.archive_date)
        return json.dumps(selfCopy.__dict__, indent=4)
    
    def is_before(self, otherGame : 'Game') -> bool :
        if self.archive_date < otherGame.archive_date :
            return True
        return False
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Game):
            return NotImplemented
        
        return (
            self.uuid == other.uuid and
            self.url == other.url and
            self.user == other.user and
            self.end_time == other.end_time and
            self.white_username == other.white_username and
            self.black_username == other.black_username
        )
    
    def winLossOrDraw (self) -> str :
        if self.user_result in ['win']:  
            return 'win'
        elif self.user_result in ['resigned', 'checkmated', 'timeout', 'abandoned'] :
            return 'loss'
        elif self.user_result in ['stalemate', 'insufficient', 'repetition', '50move', 'agreed', 'timevsinsufficient'] :
            return 'draw'
        else :
            print(f"Could not place result {self.user_result} into draw, loss or win")
            exit(1)

    def get_accuracy(self) :
        if self.user_playing_as_white and self.accuracies_white != None :
            return self.accuracies_white
        elif self.accuracies_black != None :
            return self.accuracies_black
        return None