from datetime import datetime
import json

class FilterInfo():

    def __init__(self, user : str, user_range : 'RatingRange' = None, 
                 opponent_range : 'RatingRange' = None,
                 date_range : 'DateRange' = None,
                 time_control_range : 'TimeControl' = None,
                 rated : bool = None,
                 playing_as_white : bool = None
                 ) -> None:
        self.user = user.lower()
        self.user_rating_range = user_range
        self.opponent_rating_range = opponent_range
        self.date_range = date_range
        self.time_control_range = time_control_range
        self.rated = rated
        self.playing_as_white = playing_as_white
    
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
            
    def __str__(self):
        res = ""
        res += "user: " + self.user+ "\n"
        res += "user_rating_range: " + self.user_rating_range.start + " - " + self.user_rating_range.end+ "\n"
        res += "opponent_rating_range: " + self.opponent_rating_range.start + " - " + self.opponent_rating_range.end+ "\n"
        if self.date_range != None :
            res += "date_range: " + str(self.date_range.start_date) + " - " + str(self.date_range.end_date) + "\n"
        else :
            res += "date_range: None" + "\n"
            
        res += "time_control_range: " + self.time_control_range.lower + " - " + self.time_control_range.upper + "\n"
        res += "rated: " + str(self.rated) + "\n"
        res += "playing_as_white: " + str(self.playing_as_white) + "\n"
        return res