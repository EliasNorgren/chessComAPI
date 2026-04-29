import csv
import random

LICHESS_CSV_PATH = "SQL/lichess_db_puzzle.csv"


def sample_puzzles(rating_min: int, rating_max: int, count: int) -> list:
    """One-pass reservoir sampling over the Lichess CSV. O(count) memory."""
    reservoir = []
    seen = 0
    with open(LICHESS_CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rating = int(row['Rating'])
            except (ValueError, KeyError):
                continue
            if rating_min <= rating <= rating_max:
                seen += 1
                if len(reservoir) < count:
                    reservoir.append(row)
                else:
                    j = random.randint(0, seen - 1)
                    if j < count:
                        reservoir[j] = row
    random.shuffle(reservoir)
    return reservoir
