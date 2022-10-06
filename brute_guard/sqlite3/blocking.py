import threading

from typing import Optional
from sqlite3 import Connection
from dataclasses import dataclass

from brute_guard.sqlite3.control import Control
from brute_guard.settings import (
    AccessResult,
    Columns,
    TB_BLOCKED_LIST,
    TB_ACCESS,
)


lock = threading.Lock()


@dataclass
class Blocking:
    conn: Connection
    control: Control
    column: Columns
    blocked_expires_at: str
    failure_time: str
    failures: int

    def __post_init__(self):
        if self.column == Columns.USERNAME.value:
            self.secondary_column = Columns.IP.value
        else:
            self.secondary_column = Columns.USERNAME.value

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
        if self.column == Columns.IP.value and ip is None:
            raise ValueError("'ip' must be a valid value")

        if self.column == Columns.USERNAME.value and username is None:
            raise ValueError("'username' must be a valid value")

        access_result = AccessResult.FAIL.value

        if success:
            access_result = AccessResult.SUCCESS.value

        column_val = ip if self.column == Columns.IP.value else username
        secondary_column_val = ip if self.secondary_column == Columns.IP.value else username

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
                sql,
                (
                    self.failures,
                    self.failure_time,
                    column_val,
                ),
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

                self.conn.execute(
                    sql,
                    (
                        username,
                        ip,
                        secondary_column_val,
                        self.blocked_expires_at,
                    ),
                )

            self.conn.commit()

        if self.control.should_purge():  # control time to purge
            self.control.purge_expired()
