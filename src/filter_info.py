from datetime import datetime
import json

class FilterInfo():
    class RatingRange():
        def __init__(self, start : int, end : int) -> None:
            self.start = start
            self.end = end

    class DateRange():
        def __init__(self, start_date : datetime, end_date : datetime) -> None:
            self.start_date = start_date
            self.end_date = end_date

    class TimeControl():
        
        def __init__(self, lower : int, upper : int) -> None:
            self.lower = lower
            self.upper = upper
            
    class TimeClass():
        BULLET = "bullet"
        BLITZ = "blitz"
        RAPID = "rapid"
        DAILY = "classical"

    def __init__(self, user : str, user_range : RatingRange = None, 
                 opponent_range : RatingRange = None,
                 date_range : DateRange = None,
                 time_control_range : 'TimeControl' = None,
                 rated : bool = None,
                 playing_as_white : bool = None,
                 time_class : TimeClass = None,
                 fen_appeared : str = None
                 ) -> None:
        self.user = user.lower()
        self.user_rating_range = user_range
        self.opponent_rating_range = opponent_range
        self.date_range = date_range
        self.time_control_range = time_control_range
        self.rated = rated
        self.playing_as_white = playing_as_white
        self.time_class = time_class
        self.fen_appeared = fen_appeared

    def __str__(self):
        res = "\n"
        res += "user: " + self.user + "\n"
        if self.user_rating_range is not None:
            res += "user_rating_range: " + str(self.user_rating_range.start) + " - " + str(self.user_rating_range.end) + "\n"
        else:
            res += "user_rating_range: None\n"
        if self.opponent_rating_range is not None:
            res += "opponent_rating_range: " + str(self.opponent_rating_range.start) + " - " + str(self.opponent_rating_range.end) + "\n"
        else:
            res += "opponent_rating_range: None\n"
        if self.date_range is not None:
            res += "date_range: " + str(self.date_range.start_date) + " - " + str(self.date_range.end_date) + "\n"
        else:
            res += "date_range: None\n"
        if self.time_control_range is not None:
            res += "time_control_range: " + str(self.time_control_range.lower) + " - " + str(self.time_control_range.upper) + "\n"
        else:
            res += "time_control_range: None\n"
        res += "rated: " + str(self.rated) + "\n"
        res += "playing_as_white: " + str(self.playing_as_white) + "\n"
        if self.time_class is not None :
            res += "time_class: " + str(self.time_class) + "\n"
        if self.fen_appeared is not None:
            res += "fen_appeared: " + str(self.fen_appeared) + "\n"
        return res