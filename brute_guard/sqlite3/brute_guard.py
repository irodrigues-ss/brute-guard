import threading

from typing import Optional
from sqlite3 import connect
from datetime import timedelta
from dataclasses import dataclass

from brute_guard.sqlite3.blocking import Blocking
from brute_guard.sqlite3.control import Control
from brute_guard.settings import COLUMN_IP, COLUMN_USERNAME


lock = threading.Lock()


@dataclass
class BruteGuard:
    access_expires_at: str = "+1 day"
    blocked_expires_at: str = "+1 hour"
    failure_time: str = "-10 seconds"
    accepted_consecutive_failures: int = 8
    purge_time: Optional[timedelta] = timedelta(minutes=60)
    database_url: str = "/tmp/db.sqlite"

    def __post_init__(self) -> None:
        self._connection = self._create_connection(self.database_url)

        self.control = Control(
            self._connection, self.purge_time, self.access_expires_at, self.blocked_expires_at
        )
        self.user = Blocking(
            self._connection,
            self.control,
            COLUMN_USERNAME,
            self.blocked_expires_at,
            self.failure_time,
            self.accepted_consecutive_failures,
        )

        self.ip = Blocking(
            self._connection,
            self.control,
            COLUMN_IP,
            self.blocked_expires_at,
            self.failure_time,
            self.accepted_consecutive_failures,
        )

    def _create_connection(self, database_url: str):
        conn = connect(database_url, check_same_thread=False)
        conn.execute("PRAGMA synchronous = off")
        conn.execute("PRAGMA auto_vacuum = 1")
        conn.execute("PRAGMA cache_size = 2000")
        return conn
