from datetime import timedelta
import time
import pytest

from tests.conftest import count_from
from brute_guard.sqlite3 import BruteGuard
from brute_guard.settings import TB_ACCESS, TB_BLOCKED_LIST


bg = BruteGuard(
    blocked_expires_at="+1 second",
    failure_time="-1 second",
    failures=2,
)


@pytest.fixture(scope="module", autouse=True)
def create_tables():
    bg.control.create_tables()


@pytest.fixture(autouse=True)
def setup():
    bg.control.purge_all()


def test_block_user():
    bg.user.access("fake-user", "10.1.10.10", False)
    bg.user.access("fake-user", "10.1.10.10", False)

    assert bg.user.is_blocked("fake-user") is True

    time.sleep(1)

    assert bg.user.is_blocked("fake-user") is False


def test_block_ip():
    bg.ip.access("fake-user1", "10.1.10.10", False)
    bg.ip.access("fake-user2", "10.1.10.10", False)

    assert bg.ip.is_blocked("10.1.10.10") is True

    time.sleep(1)

    assert bg.ip.is_blocked("10.1.10.10") is False


def test_block_user_with_success():
    bg.user.access("fake-user", "10.1.10.10", False)
    bg.user.access("fake-user", "10.1.10.10", True)

    assert bg.user.is_blocked("fake-user") is False

    time.sleep(2)

    bg.user.access("fake-user", "10.1.10.10", False)
    bg.user.access("fake-user", "10.1.10.10", False)

    assert bg.user.is_blocked("fake-user") is True


def test_block_ip_with_success():
    bg.ip.access("fake-user1", "10.1.10.10", False)
    bg.ip.access("fake-user2", "10.1.10.10", True)

    assert bg.ip.is_blocked("10.1.10.10") is False

    time.sleep(2)

    bg.ip.access("fake-user1", "10.1.10.10", False)
    bg.ip.access("fake-user2", "10.1.10.10", False)

    assert bg.ip.is_blocked("10.1.10.10") is True


def test_incorrect_ip_arg():
    with pytest.raises(ValueError):
        bg.ip.access("fake-user", None, success=False)


def test_incorrect_username_arg():
    with pytest.raises(ValueError):
        bg.user.access(None, "10.10.10.10", success=False)


def test_purge_expired():
    bg = BruteGuard(
        access_expires_at="+1 second",
        blocked_expires_at="+1 second",
        failure_time="-1 second",
        failures=2,
        purge_time=timedelta(seconds=2),
    )
    bg.control.drop_tables()
    bg.control.create_tables()

    bg.user.access("fake-user", "10.1.10.10", False)
    bg.user.access("fake-user", "10.1.10.10", False)

    assert bg.user.is_blocked("fake-user") is True

    assert count_from(bg._connection, TB_ACCESS) == 2
    assert count_from(bg._connection, TB_BLOCKED_LIST) == 1

    time.sleep(2)

    bg.user.access("fake-user", "10.1.10.10", True)

    assert count_from(bg._connection, TB_ACCESS) == 1
    assert count_from(bg._connection, TB_BLOCKED_LIST) == 0


def test_purge_all():
    bg = BruteGuard(
        access_expires_at="+1 second",
        blocked_expires_at="+1 second",
        failure_time="-1 second",
        failures=1,
    )
    bg.control.drop_tables()
    bg.control.create_tables()

    bg.user.access("fake-user", "10.1.10.10", False)

    assert bg.user.is_blocked("fake-user") is True

    assert count_from(bg._connection, TB_ACCESS) == 1
    assert count_from(bg._connection, TB_BLOCKED_LIST) == 1

    time.sleep(1)
    bg.control.purge_all()

    assert count_from(bg._connection, TB_ACCESS) == 0
    assert count_from(bg._connection, TB_BLOCKED_LIST) == 0
