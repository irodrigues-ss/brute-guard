import pytest
import time

from brute_guard.settings import TB_ACCESS, TB_BLOCKED_LIST
from brute_guard.sqlite3 import BruteGuard


pbfa = BruteGuard(
    blocked_expires_at="+1 second", failure_time="-1 second", accepted_consecutive_failures=2
)


@pytest.fixture(scope="module", autouse=True)
def create_tables():
    pbfa.control.create_tables()


@pytest.fixture(autouse=True)
def setup():
    pbfa.control.purge_all()


def count_from(conn, tb_name: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) FROM {tb_name}")
    return cur.fetchone()[0]


@pytest.mark.usefixtures("create_tables")
def test_block_user():
    pbfa.user.access("fake-user", "10.1.10.10", False)
    pbfa.user.access("fake-user", "10.1.10.10", False)

    assert pbfa.user.is_blocked("fake-user") is True

    time.sleep(1)

    assert pbfa.user.is_blocked("fake-user") is False


@pytest.mark.usefixtures("create_tables")
def test_block_user_with_sucess():
    pbfa.user.access("fake-user", "10.1.10.10", False)
    pbfa.user.access("fake-user", "10.1.10.10", True)

    assert pbfa.user.is_blocked("fake-user") is False

    time.sleep(2)

    pbfa.user.access("fake-user", "10.1.10.10", False)
    pbfa.user.access("fake-user", "10.1.10.10", False)

    assert pbfa.user.is_blocked("fake-user") is True


def test_purge_expired():
    pbfa = BruteGuard(
        access_expires_at="+1 second",
        blocked_expires_at="+1 second",
        failure_time="-1 second",
        accepted_consecutive_failures=2,
    )
    pbfa.control.drop_tables()
    pbfa.control.create_tables()

    pbfa.user.access("fake-user", "10.1.10.10", False)
    pbfa.user.access("fake-user", "10.1.10.10", False)

    assert pbfa.user.is_blocked("fake-user") is True

    assert count_from(pbfa._connection, TB_ACCESS) == 2
    assert count_from(pbfa._connection, TB_BLOCKED_LIST) == 1

    time.sleep(2)

    pbfa.control.purge_expired()

    assert count_from(pbfa._connection, TB_ACCESS) == 0
    assert count_from(pbfa._connection, TB_BLOCKED_LIST) == 0
