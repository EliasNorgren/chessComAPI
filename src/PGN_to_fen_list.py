import json
import sqlite3
import chess.pgn
from io import StringIO

# Function to extract FENs from PGN
def extract_fens(pgn_string) -> str:
    fens = []
    pgn = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn)
    board = game.board()
    fens.append(board.fen())
    for move in game.mainline_moves():
        board.push(move)
        fens.append(board.fen())
    return "&".join(fens)

def pgn_to_move_list(pgn_string: str) -> list:
    move_list = []
    pgn = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn)

    nodes = list(game.mainline())  # Convert to list first
    for node in nodes:  # skip root node (no move)
        move = node.move
        clock_time = node.clock()  # remaining time in seconds or None
        move_list.append((move.uci(), clock_time))
    return move_list