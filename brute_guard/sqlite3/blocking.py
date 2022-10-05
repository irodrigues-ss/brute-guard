import threading

from typing import Optional, Any
from dataclasses import dataclass

from brute_guard.settings import (
    AccessResult, TB_BLOCKED_LIST, TB_ACCESS,
    COLUMN_IP, COLUMN_USERNAME
)
from brute_guard.sqlite3.control import Control

lock = threading.Lock()


@dataclass
class Blocking:
    conn: Any
    control: Control
    column: str
    blocked_expires_at: str
    failure_time: str
    accepted_consecutive_failures: int

    def __post_init__(self):
        if self.column == COLUMN_USERNAME:
            self.secondary_column = COLUMN_IP
        else:
            self.secondary_column = COLUMN_USERNAME

    def is_blocked(self, target: str) -> bool:
        # target: username or ip

        sql = f"""
        SELECT
            ip,
            username,
            expires_at,
            'blocked' as status
        FROM
            {TB_BLOCKED_LIST}
        WHERE
            {self.column} = ? AND current_timestamp < expires_at
        """
        with lock:
            cur = self.conn.execute(sql, (target,))
            return bool(cur.fetchone())

    def access(self, username: Optional[str], ip: Optional[str], success: bool):
        if self.column == COLUMN_IP and ip is None:
            raise ValueError("'ip' must be a valid value")

        if self.column == COLUMN_USERNAME and username is None:
            raise ValueError("'username' must be a valid value")

        access_result = AccessResult.FAIL.value

        if success:
            access_result = AccessResult.SUCCESS.value

        with lock:
            sql = f"""
            INSERT INTO {TB_ACCESS}(ip, username, access) VALUES (?, ?, ?)
            """
            self.conn.execute(sql, (ip, username, access_result))

            sql = f"""
            SELECT
                {self.column},
                CASE
                    WHEN COUNT(*) >= ? AND INSTR(GROUP_CONCAT(access), 'success') = 0
                        THEN 'deny'
                    ELSE 'allow'
                END AS status
            FROM
                {TB_ACCESS}
            WHERE
                created_at >= datetime(current_timestamp, ?) -- can be '-10 minute' that means the last 10 minutes
                AND {self.column} = ?
            GROUP BY
                {self.column}
            """
            cur = self.conn.execute(
                sql, (self.accepted_consecutive_failures, self.failure_time, username)
            )
            row = cur.fetchone()

            if row and row[-1] == "deny":
                sql = f"""
                INSERT INTO
                    {TB_BLOCKED_LIST}(username, ip) VALUES (?, ?)
                ON CONFLICT({self.column})
                    DO UPDATE
                        SET {self.secondary_column} = ?,
                        created_at = current_timestamp,
                        expires_at = datetime(current_timestamp, ?);
                """
                set_val = ip if self.secondary_column == COLUMN_IP else username

                self.conn.execute(
                    sql,
                    (
                        username,
                        ip,
                        set_val,
                        self.blocked_expires_at,
                    ),
                )

            self.conn.commit()

        if self.control.should_purge():  # control time to purge
            self.control.purge_expired()
