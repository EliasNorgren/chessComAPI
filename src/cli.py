from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime
from analyzer import Analyzer
from filter_info import FilterInfo
from parser import Parser
from controller import DataBaseUpdater
import json

def str2bool(v):
    print(f"Converting {v} to boolean")
    if isinstance(v, bool):
        print(f"Value is already a boolean: {v}")
        return v
    if v.lower() in ("yes", "true", "t", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "0"):
        return False
    else:
        raise ArgumentTypeError("Boolean value expected.")

def main():
    parser = ArgumentParser(description="ChessCom CLI Tool")
    parser.add_argument("user", type=str, help="Username for filtering games")
    parser.add_argument("--rated", type=str2bool, nargs="?", const=None, help="Filter for rated games (true/false)")
    parser.add_argument("--playing_as_white", type=str2bool, nargs="?", const=None, help="Filter for games played as white (true/false)")
    parser.add_argument("--start_date", type=str, help="Start date for filtering games (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, help="End date for filtering games (YYYY-MM-DD)")
    parser.add_argument("--update_database", action="store_true", help="Update the database with new games for the user")
    parser.add_argument("--time_class", type=str, choices=[FilterInfo.TimeClass.BULLET, FilterInfo.TimeClass.BLITZ, FilterInfo.TimeClass.RAPID, FilterInfo.TimeClass.DAILY], help="Filter by time class (bullet, blitz, rapid, classical)")
    parser.add_argument("--fen_appeared", type=str, help="Filter for games where a specific FEN appeared")

    # Subparsers for each get method
    subparsers = parser.add_subparsers(dest="command", required=True, help="Parser method to call")

    # Add subcommands for each get method
    subparsers.add_parser("get_most_played_players")
    subparsers.add_parser("get_win_percentage_and_accuracy")
    subparsers.add_parser("get_stats_per_day")
    subparsers.add_parser("get_win_percentage_per_opening")
    subparsers.add_parser("get_wins_by_day_of_week")
    subparsers.add_parser("get_blunders")
    subparsers.add_parser("analyze_games_for_user")

    eco_parser = subparsers.add_parser("get_games_by_eco")
    eco_parser.add_argument("--eco", type=str, required=True, help="ECO code")

    get_games_against_player_parser = subparsers.add_parser("get_games_against_player")
    get_games_against_player_parser.add_argument("--opponent", type=str, required=True, help="Opponent username")

    get_total_fens_substring_parser = subparsers.add_parser("get_total_fens_substring")
    get_total_fens_substring_parser.add_argument("--substring", type=str, required=True, help="Get games where this FEN occured")

    # analyze_games_parser = subparsers.add_parser("analyze_games")
    # analyze_games_parser.add_argument("--reanalyze_analyzed_games", action="store_true", help="Reanalyze already analyzed games")

    args = parser.parse_args()
    print(f"Parsed arguments: {args}")
    # If update_database is set, update the database for the user
    if args.update_database:
        
        updater = DataBaseUpdater()
        games = updater.updateDB(args.user)
        print(f"Updated {args.user} with {games} new games!")

    # Create FilterInfo instance
    date_range = None
    start_date = None
    end_date = None
    if args.start_date :
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    if args.end_date :
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    date_range = FilterInfo.DateRange(start_date, end_date)

    filter_info = FilterInfo(
        user=args.user,
        rated=args.rated,
        playing_as_white=args.playing_as_white,
        date_range=date_range,
        time_class=args.time_class if args.time_class else None,
        fen_appeared=args.fen_appeared if args.fen_appeared else None
    )
    parser_obj = Parser()

    # Map subcommand to method and call dynamically
    if args.command == "get_most_played_players":
        result = parser_obj.get_most_played_players(filter_info)
    elif args.command == "get_win_percentage_and_accuracy":
        result = parser_obj.get_win_percentage_and_accuracy(filter_info)
    elif args.command == "get_stats_per_day":
        result = parser_obj.get_stats_per_day(filter_info)
    elif args.command == "get_games_by_eco":
        result = parser_obj.get_games_by_eco(filter_info, eco=args.eco)
    elif args.command == "get_games_against_player":
        if not hasattr(args, 'opponent'):
            parser.error("The 'get_games_against_player' command requires the --opponent argument")
        result = parser_obj.get_games_against_player(filter_info, user=args.opponent)
    elif args.command == "get_total_fens_substring":
        if not hasattr(args, 'substring'):
            parser.error("The 'get_total_fens_substring' command requires the --substring argument")
        result = parser_obj.get_total_fens_substring(filter_info, sub_string=args.substring)
    elif args.command == "get_win_percentage_per_opening":
        result = parser_obj.get_win_percentage_per_opening(filter_info)
    elif args.command == "get_wins_by_day_of_week":
        result = parser_obj.get_wins_by_day_of_week(filter_info)
    # elif args.command == "analyze_games":
        # result = parser_obj.analyze_games(filter_info, reanalyze_analyzed_games=args.reanalyze_analyzed_games)
    elif args.command == "get_blunders" :
        result = parser_obj.get_blunders(filter_info)
    elif args.command == "analyze_games_for_user" :
        analyzer = Analyzer()
        result = parser_obj.analyze_games_for_user(filter_info, analyzer)
    else:
        parser.error("Unknown command")

    print(json.dumps(result, indent=4))

if __name__ == "__main__":
    main()