import threading

from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlite3 import Connection

from brute_guard.settings import TB_ACCESS, TB_BLOCKED_LIST


lock = threading.Lock()


@dataclass
class Control:
    conn: Connection
    purge_time: Optional[timedelta]
    access_expires_at: str
    blocked_expires_at: str

    def __post_init__(self):
        if self.purge_time:
            self.next_purge = datetime.now() + self.purge_time

    def should_purge(self) -> bool:
        if self.purge_time and datetime.now() >= self.next_purge:
            self.next_purge = self.next_purge + self.purge_time
            return True

        return False

    def create_tables(self):
        sql = f"""
        CREATE TABLE IF NOT EXISTS {TB_ACCESS}(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            username TEXT,
            access TEXT, -- success / fail
            created_at TIMESTAMP DEFAULT (datetime(current_timestamp)),
            expires_at TIMESTAMP DEFAULT (datetime(current_timestamp, '{self.access_expires_at}'))
        );
        """
        self.conn.execute(sql)

        sql = f"""
        CREATE TABLE IF NOT EXISTS {TB_BLOCKED_LIST}(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT UNIQUE,
            username TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT (datetime(current_timestamp)),
            expires_at TIMESTAMP DEFAULT (datetime(current_timestamp, '{self.blocked_expires_at}'))
        )
        """
        self.conn.execute(sql)
        self.conn.commit()

    def drop_tables(self):
        with lock:
            self.conn.execute(f"""DROP TABLE IF EXISTS {TB_ACCESS};""")
            self.conn.execute(f"""DROP TABLE IF EXISTS {TB_BLOCKED_LIST};""")
            self.conn.commit()

    def purge_all(self):
        with lock:
            self.conn.execute(f"""DELETE FROM {TB_ACCESS};""")
            self.conn.execute(f"""DELETE FROM {TB_BLOCKED_LIST};""")
            self.conn.commit()

    def purge_expired(self):
        with lock:
            self.conn.execute(f"""DELETE FROM {TB_ACCESS} WHERE current_timestamp > expires_at;""")
            self.conn.execute(
                f"""DELETE FROM {TB_BLOCKED_LIST} WHERE current_timestamp > expires_at;"""
            )
            self.conn.commit()
