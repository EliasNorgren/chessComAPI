# from stockfish import Stockfish
# from stockfish.models import Stockfish
from stockfish_fork.stockfish.models import Stockfish
import os
import chess
import chess.svg
from entryCache import EntryCache
import yaml

class Analyzer:
    def __init__(self):
        print("Initializing Analyzer with Stockfish engine...")
        self.classification_colors = {
            "Best Move": "#749bbf",
            "Good Move": "#81b64c",
            "Inaccuracy": "#f7c631",
            "Mistake": "#ff7769",
            "Blunder": "#fa412d"
        }
        stockfish_engine_path = os.getenv("STOCKFISH_ENGINE_PATH")
        print(f"Using Stockfish engine at: {stockfish_engine_path}")
        if not stockfish_engine_path:
            raise ValueError("STOCKFISH_ENGINE_PATH environment variable is not set.")
        
        with open("cfg/stockfish_settings.yaml", "r") as config_file:
            config = yaml.safe_load(config_file)
        settings = config.get("stockfish_settings", {})
        print(f"Loaded configuration settings: {settings}")
        
        self.engine : Stockfish = Stockfish(path=stockfish_engine_path, parameters=settings)
        self.engine_depth = 17

    def analyze_game(self, move_list: list, user_playing_as_white: bool, entryCache: EntryCache, uuid) -> list:
        orientation = chess.WHITE if user_playing_as_white else chess.BLACK
        result = []
        chess_board = chess.Board()
        white_turn = True
        no_moves = len(move_list)
        current_move = 0
        for move, clock_time in move_list:
            # print(f"Analyzing move {current_move + 1}/{no_moves}: {move} (Clock: {clock_time})")
            progress = f"{current_move / no_moves * 100:.2f}%"
            print(progress)
            if entryCache and uuid :
                entryCache.set_entry(uuid, f"loading {current_move + 1}/{no_moves} ({progress})")
            current_move += 1
            # Write svg to file
            uci_move = chess.Move.from_uci(move)
            san_move = chess_board.san(uci_move)
            board_fen_before_move = chess_board.fen()
            chess_board.push(uci_move)
            best_move = self.engine.get_top_moves(1, include_principal_variation=True)
            self.engine.set_depth(self.engine_depth)
            self.engine.make_moves_from_current_position([move])
            self.engine.set_depth(self.engine_depth - 1)
            eval = self.engine.get_evaluation(include_principal_variation=True)
            best_eval_cp = best_move[0]['Centipawn'] if best_move[0]['Centipawn'] is not None else best_move[0]['Mate']
            move_classification = self.classify_move(best_eval_cp=best_eval_cp,
                                                      played_eval_cp=eval['value'],
                                                      played_move=uci_move,
                                                      best_move=best_move[0]['Move'],
                                                      best_eval_got_mate=best_move[0]['Mate'] != None,
                                                      played_move_got_mate=eval['type'] == 'mate',
                                                      player_is_white=white_turn)
            arrows = []
            best_move_uci = chess.Move.from_uci(best_move[0]['Move']) 
            if move_classification != "Best Move":
                arrows = [chess.svg.Arrow(best_move_uci.from_square, best_move_uci.to_square, color="#008612AC")]
            fill = dict.fromkeys([uci_move.from_square, uci_move.to_square], self.classification_colors.get(move_classification, "#48ff00"))
            colors = {
                "square light": "#ebecd0",
                "square dark": "#739552",
            }
            svg = chess.svg.board(chess_board, size=400, orientation=orientation, fill=fill, arrows=arrows, colors=colors)
            white_turn = not white_turn
            
            entry = {
                "move": san_move,
                "uci_move": str(uci_move),
                "evaluation": eval,
                "classification": move_classification,
                "svg": svg,
                "board": chess_board.fen(),
                "board_before_move": board_fen_before_move,
                "score": self.classification_to_score(move_classification),
                "clock_time": clock_time,
                "best_move" : best_move,
                "best_move_uci": str(best_move_uci),
                "best_line": best_move[0]['Line'] if 'Line' in best_move[0] else "",
                "played_line": move + " - " + eval['line'] if 'line' in eval and eval['line'] else move
            }
            result.append(entry)
        return result
            

    def classify_move(self, best_eval_cp, played_eval_cp, played_move, best_move, best_eval_got_mate, played_move_got_mate, player_is_white):
        # print(f"Classifying move: {played_move}, Best move: {best_move}, Best eval: {best_eval_cp}, Played eval: {played_eval_cp}, Player is white: {player_is_white}, Best eval got mate: {best_eval_got_mate}, Played move got mate: {played_move_got_mate}")
        # A mate exist and the player is the one winning
        if best_eval_got_mate and ((player_is_white and best_eval_cp > 0) or (not player_is_white and best_eval_cp < 0)):
            if best_eval_got_mate and str(played_move) != str(best_move) and not played_move_got_mate:
                return "Missed mate"
            elif best_eval_got_mate and str(played_move) == str(best_move):
                # Fastest way to win
                return "Best Move"
            else : #played_move_got_mate and str(played_move) == str(best_move) and best_eval_got_mate:
                # Still mating, but not the fastest way
                return "Good Move"
        # A mate exist and the player is the one losing
        elif (played_move_got_mate) and ((player_is_white and played_eval_cp < 0) or (not player_is_white and played_eval_cp > 0)):
            if str(played_move) == str(best_move):
                return "Best Move"
            elif str(played_move) != str(best_move) and played_eval_cp == best_eval_cp:
                # Best move was the same distance to mate, but not the best move
                return "Good Move"
            elif str(played_move) != str(best_move) and not best_eval_got_mate:
                # Player walked into a mate
                return "Blunder"
            else :
                return "Inaccuracy"

        if str(played_move) == str(best_move):
            return "Best Move"

        cp_loss = abs(best_eval_cp - played_eval_cp)
        if cp_loss <= 50:
            return "Good Move"
        elif cp_loss <= 150:
            return "Inaccuracy"
        elif cp_loss <= 300:
            return "Mistake"
        else:
            return "Blunder"

    def classification_to_score(self, classification):
        classification_scores = {
            "Best Move": 1.0,
            "Good Move": 0.9,
            "Inaccuracy": 0.7,
            "Mistake": 0.4,
            "Blunder": 0.0,
            "Missed mate": 0.4
        }
        return classification_scores.get(classification, 0.0)
    
    def close_engine(self):
        self.engine.send_quit_command()