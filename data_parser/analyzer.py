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

    def analyze_game(self, move_list: list, user_playing_as_white: bool) :
        white_turn = True
        for move in move_list:
            if white_turn == user_playing_as_white:
                best_move = self.engine.get_top_moves(1)
            else:
                self.engine.make_moves_from_current_position([move])
                white_turn = not white_turn
                continue

            print(f'Stockfish suggests: {best_move}')
            self.engine.make_moves_from_current_position([move])
            eval = self.engine.get_evaluation()
            move_classification = self.classify_move(eval['value'], best_move[0]['Centipawn'], move, best_move[0]['Move'])
            print(f"Your move: {move}, evaluation: {eval} - {move_classification}")
            board = self.engine.get_board_visual(user_playing_as_white)
            print(board)
            input("Press Enter to continue...")
            white_turn = not white_turn

    def classify_move(self, best_eval_cp, played_eval_cp, played_move, best_move):
        
        if played_move == best_move:
            return "Best Move"

        cp_loss = abs(best_eval_cp - played_eval_cp)
        if cp_loss <= 50:
            return "Great Move"
        elif cp_loss <= 150:
            return "Inaccuracy"
        elif cp_loss <= 300:
            return "Mistake"
        else:
            return "Blunder"