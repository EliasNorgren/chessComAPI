import sqlite3
import datetime


class WoodpeckerDB:
    def __init__(self):
        self.db_path = "SQL/chess_games.db"

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def create_set(self, user: str, name: str, rating_min: int, rating_max: int, puzzles: list) -> int:
        conn = self._conn()
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO woodpecker_sets (user, name, rating_min, rating_max, size, created_at) VALUES (?,?,?,?,?,?)",
            (user, name, rating_min, rating_max, len(puzzles), now)
        )
        set_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO woodpecker_set_puzzles (set_id, puzzle_id, fen, moves, rating, position) VALUES (?,?,?,?,?,?)",
            [(set_id, p['PuzzleId'], p['FEN'], p['Moves'], int(p['Rating']), i) for i, p in enumerate(puzzles)]
        )
        conn.commit()
        conn.close()
        return set_id

    def get_sets(self, user: str) -> list:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ws.id, ws.name, ws.rating_min, ws.rating_max, ws.size, ws.created_at,
                   COUNT(wa.id)            AS completed_count,
                   MIN(wa.duration_seconds) AS best_seconds,
                   MAX(wa.completed_at)    AS last_completed
            FROM woodpecker_sets ws
            LEFT JOIN woodpecker_attempts wa
                ON wa.set_id = ws.id AND wa.completed_at IS NOT NULL
            WHERE ws.user = ?
            GROUP BY ws.id
            ORDER BY ws.created_at DESC
        ''', (user,))
        rows = cursor.fetchall()

        # Check for active (incomplete) attempts
        result = []
        for r in rows:
            cursor.execute(
                "SELECT id FROM woodpecker_attempts WHERE set_id = ? AND completed_at IS NULL LIMIT 1",
                (r[0],)
            )
            has_active = cursor.fetchone() is not None
            result.append({
                "id": r[0], "name": r[1], "rating_min": r[2], "rating_max": r[3],
                "size": r[4], "created_at": r[5], "completed_count": r[6],
                "best_seconds": r[7], "last_completed": r[8], "has_active": has_active,
            })
        conn.close()
        return result

    def get_or_create_attempt(self, set_id: int, user: str) -> dict:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, attempt_number, started_at FROM woodpecker_attempts WHERE set_id=? AND user=? AND completed_at IS NULL ORDER BY id DESC LIMIT 1",
            (set_id, user)
        )
        row = cursor.fetchone()
        if row:
            conn.close()
            return {"attempt_id": row[0], "attempt_number": row[1], "started_at": row[2], "is_new": False}

        cursor.execute(
            "SELECT COUNT(*) FROM woodpecker_attempts WHERE set_id=? AND user=? AND completed_at IS NOT NULL",
            (set_id, user)
        )
        attempt_number = cursor.fetchone()[0] + 1
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO woodpecker_attempts (set_id, user, attempt_number, started_at) VALUES (?,?,?,?)",
            (set_id, user, attempt_number, now)
        )
        attempt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"attempt_id": attempt_id, "attempt_number": attempt_number, "started_at": now, "is_new": True}

    def get_next_puzzle(self, attempt_id: int, set_id: int) -> dict | None:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT wsp.id, wsp.puzzle_id, wsp.fen, wsp.moves, wsp.rating, wsp.position,
                   (SELECT COUNT(*) FROM woodpecker_set_puzzles WHERE set_id = ?) AS total
            FROM woodpecker_set_puzzles wsp
            WHERE wsp.set_id = ?
              AND wsp.id NOT IN (
                  SELECT set_puzzle_id FROM woodpecker_puzzle_results WHERE attempt_id = ?
              )
            ORDER BY wsp.position ASC
            LIMIT 1
        ''', (set_id, set_id, attempt_id))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "set_puzzle_id": row[0],
            "puzzle_id":     row[1],
            "fen":           row[2],
            "moves":         row[3].split(),
            "rating":        row[4],
            "position":      row[5] + 1,
            "total":         row[6],
        }

    def submit_puzzle_result(self, attempt_id: int, set_puzzle_id: int, solved: bool, time_taken: float):
        conn = self._conn()
        conn.execute(
            "INSERT INTO woodpecker_puzzle_results (attempt_id, set_puzzle_id, solved, time_taken_seconds) VALUES (?,?,?,?)",
            (attempt_id, set_puzzle_id, solved, time_taken)
        )
        conn.commit()
        conn.close()

    def complete_attempt(self, attempt_id: int):
        conn = self._conn()
        now = datetime.datetime.now().isoformat()
        conn.execute('''
            UPDATE woodpecker_attempts
            SET completed_at = ?,
                duration_seconds = (
                    SELECT CAST(ROUND(SUM(time_taken_seconds)) AS INTEGER)
                    FROM woodpecker_puzzle_results
                    WHERE attempt_id = ?
                )
            WHERE id = ?
        ''', (now, attempt_id, attempt_id))
        conn.commit()
        conn.close()

    def get_set_stats(self, set_id: int) -> dict:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT attempt_number, started_at, completed_at, duration_seconds
            FROM woodpecker_attempts
            WHERE set_id = ? AND completed_at IS NOT NULL
            ORDER BY attempt_number ASC
        ''', (set_id,))
        attempts = [
            {"attempt_number": r[0], "started_at": r[1], "completed_at": r[2], "duration_seconds": r[3]}
            for r in cursor.fetchall()
        ]
        conn.close()
        return {"set_id": set_id, "attempts": attempts}

    def delete_set(self, set_id: int, user: str) -> bool:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM woodpecker_sets WHERE id=? AND user=?", (set_id, user))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
