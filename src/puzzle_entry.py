class PuzzleEntry:
    def __init__(self, 
                    fen: str, 
                    best_move_uci: str, 
                    best_move_san: str, 
                    user_move_uci: str, 
                    user_move_san: str,
                    classification: str,
                    centipawn_best_move: int,
                    mate_in_best_move: int,
                    user_playing_as_white: bool,
                    game_id: int,
                    solution_line: str,
                    puzzle_id: int = -1):

        # Example dict
        # {'fen': 'rn1qkb1r/pp3ppp/3p1n2/2p1p2b/4P2P/2PP1P2/PP2N1P1/RNBQKB1R w KQkq - 0 7',
        # 'best_move': 
        #       {'Move': 'g2g4', 'Centipawn': 204, 'Mate': None, 
        #           'Line': 'g2g4 f6g4 d1a4 b8c6 f3g4 h5g4 c1g5 d8d7 e2g3 h7h6 g5e3 g7g6 f1e2 f8e7 h4h5 g4e2 g3e2 d7g4 e3f2 e8c8 b1d2'}, 
        # 'best_move_uci': 'g2g4',
        # 'user_move':
        # 'g3',
        # 'user_move_uci': 'g2g3',
        # 'classification': 'Blunder',
        # 'game_id': 147}

        self.fen : str = fen
        self.best_move_uci : str = best_move_uci
        self.best_move_san : str = best_move_san
        self.user_move_uci : str = user_move_uci
        self.user_move_san : str = user_move_san
        self.classification : str = classification
        self.centipawn_best_move : int = centipawn_best_move
        self.mate_in_best_move : int = mate_in_best_move
        self.game_id : int = game_id
        self.user_playing_as_white : bool = user_playing_as_white
        self.solved : bool = False  # To be set later based on user interaction
        self.solution_line : str = solution_line
        self.puzzle_id : int = puzzle_id  # Database ID, -1 if not set
    
    def __str__(self):
        return f"\nPuzzleEntry(fen={self.fen}, best_move_uci={self.best_move_uci}, best_move_san={self.best_move_san}, user_move_uci={self.user_move_uci}, user_move_san={self.user_move_san}, classification={self.classification}, centipawn_best_move={self.centipawn_best_move}, mate_in_best_move={self.mate_in_best_move}, user_playing_as_white={self.user_playing_as_white}, game_id={self.game_id}, solved={self.solved}, solution_line={self.solution_line})\n"