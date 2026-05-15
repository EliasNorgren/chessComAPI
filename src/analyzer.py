# from stockfish import Stockfish
# from stockfish.models import Stockfish
from stockfish_fork.stockfish.models import Stockfish
import os
import chess
import chess.svg
from entryCache import EntryCache
import yaml
import sys
import shutil
import math
import socket
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class Analyzer:
    def __init__(self, chess_960 : bool = False):
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
        settings["UCI_Chess960"] = "true" if chess_960 else "false"
        print(f"\nLoaded configuration settings: {settings}")
        self.engine : Stockfish = Stockfish(path=stockfish_engine_path, parameters=settings)
        self.engine_depth = 17

    def analyze_game(self, move_list: list, user_playing_as_white: bool, entryCache: EntryCache, uuid) -> list:
        result = []
        chess_board = chess.Board()
        white_turn = True
        no_moves = len(move_list)
        current_move = 0
        terminal_columns, terminal_rows = shutil.get_terminal_size()
        print()
        for move, clock_time in move_list:
            current_move += 1
            percent = f"{(current_move / no_moves) * 100 :.2f}%"
            bars = "█" * int((current_move / no_moves) * (terminal_columns - 10))
            sys.stdout.write(f"\r{'\033[92m'}|{bars}| {percent}")
            sys.stdout.flush()
            if entryCache and uuid :
                entryCache.set_entry(uuid, f"loading {current_move + 1}/{no_moves} ({percent})")
            # Write svg to file
            uci_move = chess.Move.from_uci(move)
            if not chess_board.is_legal(uci_move):
                print(f"\nIllegal move encountered: {move} on board {chess_board.fen()}. Stopping analysis.")
                exit(1)
            san_move = chess_board.san(uci_move)
            board_fen_before_move = chess_board.fen()
            chess_board.push(uci_move)
            best_move = self.engine.get_top_moves(1, include_principal_variation=True)
            self.engine.set_depth(self.engine_depth)
            self.engine.make_moves_from_current_position([move])
            self.engine.set_depth(self.engine_depth - 1)
            eval = self.engine.get_evaluation(include_principal_variation=True)
            best_eval_cp = best_move[0]['Centipawn'] if best_move[0]['Centipawn'] is not None else best_move[0]['Mate']
            move_classification, move_score = self.classify_move(best_eval_cp=best_eval_cp,
                                                      played_eval_cp=eval['value'],
                                                      played_move=uci_move,
                                                      best_move=best_move[0]['Move'],
                                                      best_eval_got_mate=best_move[0]['Mate'] != None,
                                                      played_move_got_mate=eval['type'] == 'mate',
                                                      player_is_white=white_turn)
            best_move_uci = chess.Move.from_uci(best_move[0]['Move']) 
            white_turn = not white_turn
            
            entry = {
                "move": san_move,
                "uci_move": str(uci_move),
                "evaluation": eval,
                "classification": move_classification,
                "board": chess_board.fen(),
                "board_before_move": board_fen_before_move,
                "score": round(move_score, 2),
                "clock_time": clock_time,
                "best_move" : best_move,
                "best_move_uci": str(best_move_uci),
                "best_line": best_move[0]['Line'] if 'Line' in best_move[0] else "",
                "played_line": move + " - " + eval['line'] if 'line' in eval and eval['line'] else move
            }
            result.append(entry)
        print()
        print("\033[0m")
        return result
    
    def analyze_game_with_k8s(self, move_list: list, user_playing_as_white: bool, entryCache: EntryCache, uuid) -> list:
        infos = socket.getaddrinfo('chess-api-all.chess-api.svc.cluster.local', 5000)
        ips = list({i[4][0] for i in infos})

        starting_fen = chess.Board().fen()
        chess_board = chess.Board()
        moves_data = []
        white_turn = True
        moves_so_far = []
        for move, clock_time in move_list:
            uci_move = chess.Move.from_uci(move)
            san_move = chess_board.san(uci_move)
            board_fen_before = chess_board.fen()
            moves_so_far.append(move)
            chess_board.push(uci_move)
            moves_data.append({
                'starting_fen': starting_fen,
                'move_list': list(moves_so_far),
                'fen': board_fen_before,
                'san': san_move,
                'uci_move': str(uci_move),
                'clock_time': clock_time,
                'board_after': chess_board.fen(),
            })
            white_turn = not white_turn

        no_moves = len(moves_data)
        completed = [0]

        def post_move(index, move_data):
            ip = ips[index % len(ips)]
            payload = {'fen': move_data['starting_fen'], 'move_list': move_data['move_list']}
            resp = requests.post(f'http://{ip}:5000/analyze_move', json=payload, timeout=120)
            resp.raise_for_status()
            completed[0] += 1
            if entryCache and uuid:
                pct = f"{completed[0] / no_moves * 100:.2f}%"
                entryCache.set_entry(uuid, f"loading {completed[0]}/{no_moves} ({pct})")
            return index, resp.json()

        results = [None] * no_moves
        with ThreadPoolExecutor(max_workers=len(ips)) as executor:
            futures = {executor.submit(post_move, i, md): i for i, md in enumerate(moves_data)}
            for future in as_completed(futures):
                idx, analysis = future.result()
                results[idx] = analysis

        output = []
        for idx, analysis in enumerate(results):
            md = moves_data[idx]
            eval_ = analysis.get('evaluation', {})
            played_line = md['move'] + " - " + eval_['line'] if eval_.get('line') else md['move']
            output.append({
                "move": md['san'],
                "uci_move": md['uci_move'],
                "evaluation": eval_,
                "classification": analysis['classification'],
                "board": md['board_after'],
                "board_before_move": md['fen'],
                "score": analysis['score'],
                "clock_time": md['clock_time'],
                "best_move": analysis['best_move'],
                "best_move_uci": analysis['best_move_uci'],
                "best_line": analysis.get('best_line', ''),
                "played_line": played_line,
            })
        return output

    def analyze_position(self, initial_fen: str, move_list: list, depth: int = None) -> dict:
        effective_depth = depth if depth is not None else self.engine_depth
        played_move = move_list[-1] if move_list else None
        self.engine.set_fen_position(initial_fen)
        self.engine.make_moves_from_current_position(move_list[:-1])  # Make all moves except the last one to get the correct position before the played move
        fen_after_moves = self.engine.get_fen_position()
        chess_board = chess.Board(fen_after_moves)
        self.engine.set_depth(effective_depth)
        best_move = self.engine.get_top_moves(1, include_principal_variation=True)
        self.engine.make_moves_from_current_position([played_move])
        self.engine.set_depth(effective_depth - 1)
        eval = self.engine.get_evaluation(include_principal_variation=True)
        best_eval_cp = best_move[0]['Centipawn'] if best_move[0]['Centipawn'] is not None else best_move[0]['Mate']
        move_classification, move_score = self.classify_move(best_eval_cp=best_eval_cp,
                                                  played_eval_cp=eval['value'],
                                                  played_move=played_move,
                                                  best_move=best_move[0]['Move'],
                                                  best_eval_got_mate=best_move[0]['Mate'] != None,
                                                  played_move_got_mate=eval['type'] == 'mate',
                                                  player_is_white=chess_board.turn == chess.WHITE)
        best_move_uci = chess.Move.from_uci(best_move[0]['Move'])

        entry = {
            "evaluation": eval,
            "classification": move_classification,
            "board": chess_board.fen(),
            "score": round(move_score, 2),
            "best_move" : best_move,
            "best_move_uci": str(best_move_uci),
            "best_line": best_move[0]['Line'] if 'Line' in best_move[0] else "",
        }
        return entry         

    def classify_move(self, best_eval_cp, played_eval_cp, played_move, best_move, best_eval_got_mate, played_move_got_mate, player_is_white):
        # print(f"Classifying move: {played_move}, Best move: {best_move}, Best eval: {best_eval_cp}, Played eval: {played_eval_cp}, Player is white: {player_is_white}, Best eval got mate: {best_eval_got_mate}, Played move got mate: {played_move_got_mate}")
        # A mate exist and the player is the one winning
        if best_eval_got_mate and ((player_is_white and best_eval_cp > 0) or (not player_is_white and best_eval_cp < 0)):
            if best_eval_got_mate and str(played_move) != str(best_move) and not played_move_got_mate:
                return "Missed mate", 0.4
            elif best_eval_got_mate and str(played_move) == str(best_move):
                # Fastest way to win
                return "Best Move", 1.0
            else : #played_move_got_mate and str(played_move) == str(best_move) and best_eval_got_mate:
                # Still mating, but not the fastest way
                return "Good Move", 0.9
        # A mate exist and the player is the one losing
        elif (played_move_got_mate) and ((player_is_white and played_eval_cp < 0) or (not player_is_white and played_eval_cp > 0)):
            if str(played_move) == str(best_move):
                return "Best Move", 1.0
            elif str(played_move) != str(best_move) and played_eval_cp == best_eval_cp:
                # Best move was the same distance to mate, but not the best move
                return "Good Move", 0.9
            elif str(played_move) != str(best_move) and not best_eval_got_mate:
                # Player walked into a mate
                return "Blunder", 0.0
            else :
                return "Inaccuracy", 0.7

        if str(played_move) == str(best_move):
            return "Best Move", 1.0

        cp_loss = abs(best_eval_cp - played_eval_cp)
        move_score = math.exp(-cp_loss / 100) 
        if cp_loss <= 50:
            return "Good Move", move_score
        elif cp_loss <= 150:
            return "Inaccuracy", move_score
        elif cp_loss <= 300:
            return "Mistake", move_score
        else:
            return "Blunder", move_score

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