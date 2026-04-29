from game import Game
from PGN_to_fen_list import extract_fens
from database import DataBase
from api import API

class DataBaseUpdater :

    def updateDB(self, user : str):
        print(f"Updating user {user}")
        user = user.lower()
        database = DataBase()
        latest_game = database.get_latest_game(user)
        api = API()
        monthly_archive = api.get_monthly_archive(user)
        inserted_games = 0

        for month_url in monthly_archive :
            if latest_game != None and self.latest_game_date_is_after_month_url(latest_game, month_url):
                continue 
            print(f"Fetching and analyzing games from {'/'.join(month_url.split('/')[-2:])}")
            games = api.get_games_from_month(month_url)    
            for json_game in games :
                game = Game(json_game, user)
                if latest_game != None and game.is_before(latest_game) or game == latest_game:
                    continue
                if game.user_result == 'kingofthehill' :
                    continue
                if game.pgn :
                    fens = extract_fens(game.pgn)
                    game.total_fens = fens

                database.insert_game(game)
                inserted_games += 1
                
        print(f"{inserted_games} new games to {user}!")
        return inserted_games

    def latest_game_date_is_after_month_url(self, latest_game: Game, month_url: str):
        month_url_year = int(month_url.split("/")[-2])
        month_url_month = int(month_url.split("/")[-1])
        if latest_game.archive_date.year > month_url_year :
            return True
        if latest_game.archive_date.year == month_url_year and month_url_month < latest_game.archive_date.month :
            return True
        return False