import sqlite3

# Connect to the database (creates the file if it doesn't exist)
conn = sqlite3.connect('SQL/chess_games.db')
cursor = conn.cursor()

# Create matches table
cursor.execute('''
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    url TEXT,
    pgn TEXT,
    time_control TEXT,
    end_time INTEGER,
    rated BOOLEAN,
    accuracies_white REAL,
    accuracies_black REAL,
    tcn TEXT,
    uuid TEXT,
    initial_setup TEXT,
    fen TEXT,
    time_class TEXT,
    rules TEXT,
    white_rating INTEGER,
    white_result TEXT,
    white_id TEXT,
    white_username TEXT,
    white_uuid TEXT,
    black_rating INTEGER,
    black_result TEXT,
    black_id TEXT,
    black_username TEXT,
    black_uuid TEXT,
    totalFens TEXT,
    archiveDate DATE,
    user_playing_as_white BOOLEAN,
    user_rating INTEGER,
    opponent_rating INTEGER,
    user_result TEXT,
    opponent_result TEXT,
    opponent_user TEXT,
    ECO TEXT,
    ECOurl TEXT,
    analysis TEXT,
    puzzles_calculated BOOLEAN DEFAULT 0
)
''')

cursor.execute('''

CREATE TABLE IF NOT EXISTS puzzles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fen TEXT NOT NULL,
    best_move_uci TEXT NOT NULL,
    best_move_san TEXT,
    user_move_uci TEXT NOT NULL,
    user_move_san TEXT NOT NULL,
    classification TEXT NOT NULL,
    centipawn_best_move INTEGER,
    mate_in_best_move INTEGER,
    user_playing_as_white BOOLEAN NOT NULL,
    game_id INTEGER NOT NULL,
    solution_line TEXT,
    solved BOOLEAN DEFAULT 0,

    FOREIGN KEY(game_id) REFERENCES matches(id) ON DELETE CASCADE
);

''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS woodpecker_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    name TEXT NOT NULL,
    rating_min INTEGER NOT NULL,
    rating_max INTEGER NOT NULL,
    size INTEGER NOT NULL,
    created_at TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS woodpecker_set_puzzles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_id INTEGER NOT NULL,
    puzzle_id TEXT NOT NULL,
    fen TEXT NOT NULL,
    moves TEXT NOT NULL,
    rating INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY(set_id) REFERENCES woodpecker_sets(id) ON DELETE CASCADE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS woodpecker_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_id INTEGER NOT NULL,
    user TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    duration_seconds INTEGER,
    FOREIGN KEY(set_id) REFERENCES woodpecker_sets(id) ON DELETE CASCADE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS woodpecker_puzzle_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    set_puzzle_id INTEGER NOT NULL,
    solved BOOLEAN NOT NULL,
    time_taken_seconds REAL,
    FOREIGN KEY(attempt_id) REFERENCES woodpecker_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY(set_puzzle_id) REFERENCES woodpecker_set_puzzles(id) ON DELETE CASCADE
)
''')

# Commit changes and close connection
conn.commit()
conn.close()
