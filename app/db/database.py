import sqlite3
from pathlib import Path
from typing import Optional, Iterable

from app.config import DB_PATH, BASE_DIR


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wallpapers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drive_file_id TEXT UNIQUE,
                file_name TEXT NOT NULL,
                local_path TEXT NOT NULL UNIQUE,
                file_size_bytes INTEGER DEFAULT 0,
                downloaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used_at TEXT,
                used_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'unused'
            )
            """
        )
        self.conn.commit()

    def add_wallpaper(
        self,
        file_name: str,
        local_path: str,
        file_size_bytes: int,
        drive_file_id: Optional[str] = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT OR IGNORE INTO wallpapers
            (drive_file_id, file_name, local_path, file_size_bytes)
            VALUES (?, ?, ?, ?)
            """,
            (drive_file_id, file_name, local_path, file_size_bytes),
        )
        self.conn.commit()

    def get_next_wallpaper(self) -> Optional[sqlite3.Row]:
        row = self.conn.execute(
            """
            SELECT * FROM wallpapers
            WHERE status = 'unused'
            ORDER BY downloaded_at ASC
            LIMIT 1
            """
        ).fetchone()
        if row:
            return row

        return self.conn.execute(
            """
            SELECT * FROM wallpapers
            ORDER BY used_count ASC, last_used_at ASC
            LIMIT 1
            """
        ).fetchone()

    def mark_used(self, wallpaper_id: int) -> None:
        self.conn.execute(
            """
            UPDATE wallpapers
            SET used_count = used_count + 1,
                last_used_at = CURRENT_TIMESTAMP,
                status = 'used'
            WHERE id = ?
            """,
            (wallpaper_id,),
        )
        self.conn.commit()

    def count_unused(self) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM wallpapers WHERE status = 'unused'"
        ).fetchone()[0]

    def count_all(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM wallpapers").fetchone()[0]

    def total_cache_bytes(self) -> int:
        return self.conn.execute(
            "SELECT COALESCE(SUM(file_size_bytes), 0) FROM wallpapers"
        ).fetchone()[0]

    def get_old_used_wallpapers(self) -> Iterable[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT * FROM wallpapers
            WHERE status = 'used'
            ORDER BY last_used_at ASC
            """
        ).fetchall()

    def delete_wallpaper(self, wallpaper_id: int) -> None:
        self.conn.execute("DELETE FROM wallpapers WHERE id = ?", (wallpaper_id,))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
