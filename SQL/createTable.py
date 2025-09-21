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

# Commit changes and close connection
conn.commit()
conn.close()
