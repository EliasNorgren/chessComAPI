from stockfish import Stockfish
import os

class Analyzer:
    def __init__(self):
        stockfish_engine_path = os.getenv("STOCKFISH_ENGINE_PATH")
        print(f"Using Stockfish engine at: {stockfish_engine_path}")
        if not stockfish_engine_path:
            raise ValueError("STOCKFISH_ENGINE_PATH environment variable is not set.")
        
        settings = {
            "Debug Log File": "",
            "Contempt": 0,
            "Min Split Depth": 0,
            "Threads": 4, # More threads will make the engine stronger, but should be kept at less than the number of logical processors on your computer.
            "Ponder": "false",
            "Hash": 2048, # Default size is 16 MB. It's recommended that you increase this value, but keep it as some power of 2. E.g., if you're fine using 2 GB of RAM, set Hash to 2048 (11th power of 2).
            "MultiPV": 1,
            "Skill Level": 20,
            "Move Overhead": 10,
            "Minimum Thinking Time": 10,
            "Slow Mover": 100,
            "UCI_Chess960": "false",
            "UCI_LimitStrength": "false",
            "UCI_Elo": 1350,  # Default Elo rating for the engine.
        }

        self.engine = Stockfish(path=stockfish_engine_path, parameters=settings)

    def analyze_game(self, move_list):
        moves = ["f4"]
        best_move = self.engine.get_top_moves(5)
        print(f"Best move for position: {best_move}")
        self.engine.set_position(moves)

analyzer = Analyzer()
analyzer.analyze_game("PGN data here")  # Replace with actual PGN data