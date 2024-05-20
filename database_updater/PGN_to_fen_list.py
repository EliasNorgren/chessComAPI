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


json_data = '''
{
  "url": "https://www.chess.com/game/live/109944083045",
  "pgn": "[Event \\"Live Chess\\"]\\n[Site \\"Chess.com\\"]\\n[Date \\"2024.05.20\\"]\\n[Round \\"-\\"]\\n[White \\"Elias661\\"]\\n[Black \\"vlady_dykyi\\"]\\n[Result \\"0-1\\"]\\n[CurrentPosition \\"6k1/5pp1/2p5/3b2P1/7P/2r3K1/8/q7 w - -\\"]\\n[Timezone \\"UTC\\"]\\n[ECO \\"B40\\"]\\n[ECOUrl \\"https://www.chess.com/openings/Sicilian-Defense-Marshall-Counterattack\\"]\\n[UTCDate \\"2024.05.20\\"]\\n[UTCTime \\"11:38:25\\"]\\n[WhiteElo \\"849\\"]\\n[BlackElo \\"883\\"]\\n[TimeControl \\"60\\"]\\n[Termination \\"vlady_dykyi won on time\\"]\\n[StartTime \\"11:38:25\\"]\\n[EndDate \\"2024.05.20\\"]\\n[EndTime \\"11:40:45\\"]\\n[Link \\"https://www.chess.com/game/live/109944083045\\"]\\n\\n1. e4 {[%clk 0:01:00]} 1... c5 {[%clk 0:01:00]} 2. Nf3 {[%clk 0:00:59.7]} 2... e6 {[%clk 0:00:59.8]} 3. d4 {[%clk 0:00:59.2]} 3... d5 {[%clk 0:00:59.7]} 4. dxc5 {[%clk 0:00:57.9]} 4... Bxc5 {[%clk 0:00:59.5]} 5. exd5 {[%clk 0:00:57.1]} 5... exd5 {[%clk 0:00:59.3]} 6. Nc3 {[%clk 0:00:55.6]} 6... Nf6 {[%clk 0:00:59.2]} 7. Bg5 {[%clk 0:00:52.9]} 7... Be6 {[%clk 0:00:56.3]} 8. Bb5+ {[%clk 0:00:50.3]} 8... Nc6 {[%clk 0:00:54.3]} 9. O-O {[%clk 0:00:49]} 9... O-O {[%clk 0:00:53.2]} 10. Re1 {[%clk 0:00:47]} 10... d4 {[%clk 0:00:52]} 11. Bxc6 {[%clk 0:00:43.4]} 11... bxc6 {[%clk 0:00:50.8]} 12. Nxd4 {[%clk 0:00:42.3]} 12... Bxd4 {[%clk 0:00:49]} 13. Ne2 {[%clk 0:00:38.8]} 13... Bxf2+ {[%clk 0:00:44.8]} 14. Kxf2 {[%clk 0:00:38]} 14... Ng4+ {[%clk 0:00:44]} 15. Kg1 {[%clk 0:00:36.4]} 15... Qxg5 {[%clk 0:00:43.3]} 16. Ng3 {[%clk 0:00:31.9]} 16... Qh6 {[%clk 0:00:39.3]} 17. h3 {[%clk 0:00:28.1]} 17... Ne3 {[%clk 0:00:34.8]} 18. Rxe3 {[%clk 0:00:26.4]} 18... Qxe3+ {[%clk 0:00:33.4]} 19. Kh2 {[%clk 0:00:24.8]} 19... Rfd8 {[%clk 0:00:30.1]} 20. Qf1 {[%clk 0:00:22.4]} 20... h5 {[%clk 0:00:23.7]} 21. Nxh5 {[%clk 0:00:20]} 21... Qe5+ {[%clk 0:00:21.2]} 22. Ng3 {[%clk 0:00:18.7]} 22... Rd2 {[%clk 0:00:18.9]} 23. c3 {[%clk 0:00:16.4]} 23... Rxb2 {[%clk 0:00:17.7]} 24. a4 {[%clk 0:00:15]} 24... a5 {[%clk 0:00:15.4]} 25. Re1 {[%clk 0:00:13.7]} 25... Qd5 {[%clk 0:00:11.7]} 26. Rd1 {[%clk 0:00:12.3]} 26... Qc4 {[%clk 0:00:09.1]} 27. Rc1 {[%clk 0:00:10.9]} 27... Qxf1 {[%clk 0:00:07.9]} 28. Rxf1 {[%clk 0:00:09.8]} 28... Rb3 {[%clk 0:00:07.8]} 29. Ne2 {[%clk 0:00:08.7]} 29... Rxc3 {[%clk 0:00:07.7]} 30. Nxc3 {[%clk 0:00:08]} 30... Bc4 {[%clk 0:00:06.8]} 31. Ne4 {[%clk 0:00:07.7]} 31... Re8 {[%clk 0:00:06.1]} 32. Rc1 {[%clk 0:00:06.7]} 32... Rxe4 {[%clk 0:00:05.1]} 33. Rd1 {[%clk 0:00:05.1]} 33... Bd5 {[%clk 0:00:05]} 34. Re1 {[%clk 0:00:03.8]} 34... Rxe1 {[%clk 0:00:03.7]} 35. Kg3 {[%clk 0:00:03.1]} 35... Ra1 {[%clk 0:00:03.5]} 36. Kh4 {[%clk 0:00:02.5]} 36... Rxa4+ {[%clk 0:00:03.4]} 37. g4 {[%clk 0:00:02]} 37... Rc4 {[%clk 0:00:03.3]} 38. Kg3 {[%clk 0:00:01.5]} 38... a4 {[%clk 0:00:03.2]} 39. h4 {[%clk 0:00:01.4]} 39... a3 {[%clk 0:00:03.1]} 40. Kh3 {[%clk 0:00:01.3]} 40... a2 {[%clk 0:00:03]} 41. g5 {[%clk 0:00:01.2]} 41... a1=Q {[%clk 0:00:02.9]} 42. Kg3 {[%clk 0:00:00.1]} 42... Rc3+ {[%clk 0:00:01]} 0-1\\n",
  "time_control": "60",
  "end_time": 1716205245,
  "rated": true,
  "accuracies": {
    "white": 65.56,
    "black": 69.15
  },
  "tcn": "mCYIgv0SlBZJBI9ICJSJbs!TcM6SfH5Qeg8!feJBHQXQvBIBsmBngnTEng7MmwMVpxEueuVugp97df3NwNuKNw7lksljiyWGaeKJedJAdcAfcfjrwmrsmsSAsC48fc8CcdAJdeCepweawFayoEyAFwGyxFyqwxqiEMi~xwAs",
  "uuid": "79676399-169d-11ef-be4f-6cfe544c0428",
  "initial_setup": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "fen": "6k1/5pp1/2p5/3b2P1/7P/2r3K1/8/q7 w - -",
  "time_class": "bullet",
  "rules": "chess",
  "white": {
    "rating": 849,
    "result": "timeout",
    "@id": "https://api.chess.com/pub/player/elias661",
    "username": "Elias661",
    "uuid": "5c945792-2aa4-11eb-895a-27b3d128e5ea"
  },
  "black": {
    "rating": 883,
    "result": "win",
    "@id": "https://api.chess.com/pub/player/vlady_dykyi",
    "username": "vlady_dykyi",
    "uuid": "015e96e6-0a25-11ed-8b57-49558506db70"
  }
}
'''

# json_data = json.loads(json_data)
# pgn = json_data["pgn"]
# fens = extract_fens(pgn)
# print(fens)