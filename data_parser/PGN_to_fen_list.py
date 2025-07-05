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
