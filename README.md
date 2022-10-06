# BruteGuard

- A Lightweight tool for preventing Brute Force Attacks.

## Features

- [Introduction](#introduction)
- [sqlite3](#sqlite3)
    - [Examples](#examples)
        - [Block IPs](#block-ips)
        - [Block usernames](#block-usernames)
    - [Attributes](#attributes)
    - [Default configs](#default-configurations)
- [Control object](#control-object)

## Introduction

- The goal of this tool is to block IPs or usernames that try to access some resource and fail consecutively in a time range.
 
- Currently this tool support the follow databases: 
    - [sqlite3](https://www.sqlite.org/docs.html)


### SQLite3

Block brute force attacks using sqlite3 under the hood.

#### Examples

##### Block IPs

- Below is an example that blocks a specific IP that fails 4 times (```failures```) consecutively in an interval of 1 second (```failure_time```). Each blocked IP will be blocked by 1 second (```blocked_expires_at```):

```python
import time

from brute_guard.sqlite3 import BruteGuard

bg = BruteGuard(
    blocked_expires_at="+1 second",
    failure_time="-1 second",
    failures=4,
    database_url="/tmp/bg.sqlite"
)
bg.control.create_tables() # Create table if exists

attacker_ip = "10.10.10.10"

# Registering fail access
bg.ip.access("fake-user1", attacker_ip, success=False)
bg.ip.access("fake-user2", attacker_ip, success=False)
bg.ip.access("some-user", attacker_ip, success=False)
bg.ip.access("some-user", attacker_ip, success=False)


if bg.ip.is_blocked(attacker_ip):
    print(f'"{attacker_ip}" is blocked.')

print("Sleeping 1 second")
time.sleep(1)


if bg.ip.is_blocked(attacker_ip) is False:
    print(f'"{attacker_ip}" is allow.')
```

##### Block usernames

- Below is an example that blocks a specific username that fails 3 times (```failures```) consecutively in an interval of 2 seconds (```failure_time```). Each blocked IP will be blocked by 2 seconds (```blocked_expires_at```):

```python
import time

from brute_guard.sqlite3 import BruteGuard

bg = BruteGuard(
    blocked_expires_at="+2 second",
    failure_time="-2 second",
    failures=3,
    database_url="/tmp/bg.sqlite"
)
bg.control.create_tables() # Create table if exists

username = "some.username"

# Registering fail access
bg.user.access(username, "3.10.24.4", success=False)
bg.user.access(username, "3.10.12.4", success=False)
bg.user.access(username, "4.15.10.4", success=False)


if bg.user.is_blocked(username):
    print(f'"{username}" is blocked.')


print("Sleeping 2 second")
time.sleep(2)


if bg.user.is_blocked(username) is False:
    print(f'"{username}" is allow.')
```


### Attributes

```python
@dataclass
class BruteGuard:
    access_expires_at: str = "+1 day"
    blocked_expires_at: str = "+1 hour"
    failure_time: str = "-10 second"
    failures: int = 8
    purge_time: Optional[timedelta] = timedelta(minutes=60)
    database_url: str = "/tmp/db.sqlite"
```

- **access_expires_at**: Time value for to expire access data using SQLite3 [Modifiers](https://www.sqlite.org/lang_datefunc.html) pattern. You must use a plus signal because the record will expire in the future.
    - Examples: "+1 day" | "+2 day" | etc.

- **blocked_expires_at**: Time value for to expire access data using SQLite3 [Modifiers](https://www.sqlite.org/lang_datefunc.html) pattern. You must use a plus signal because the record will expire in the future.
    - Examples: "+1 hour" | "+4 hour" | etc.

- **failures**: The amount of accepted consecutive failures. 

- **failure_time**: Time interval for verifying the consecutive failures.
    - Examples: "-5 second" | "-10 second" | etc.

- **purge_time**: Define time to purge expired data.
    - If you use this configuration in the next **access** will be executed a delete (with vacuum) of expired data.
    - To disable this expiration, set **purge_time** to **None**.

- **database_url**: Connection string for use in ```connect``` function. There is no any treatment in this value before passing to connect function, so, you can use any value accepted by  [connect](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect) function.
    - We recommend that you use a database in a file.
    - We do not recommend that you use a memory database because if you start a multiprocessing application each process will have a different database.

**Note**: **failures** and **failure_time** defines the following: If an IP (or username) fails consecutively **failures** times in the last **failure_time** (interval time) this IP will be blocked.


#### Default configurations

- [*synchronous = off*](https://www.sqlite.org/pragma.html#pragma_synchronous)
- [*auto_vacuum = 1*](https://www.sqlite.org/pragma.html#pragma_auto_vacuum)
- [*cache_size = 2000*](https://www.sqlite.org/pragma.html#pragma_cache_size)

### Control object

- This object is used to control some operations in the database.

```python
from brute_guard.sqlite3 import BruteGuard

bg = BruteGuard()
bg.control.create_tables()
bg.control.drop_tables()
bg.control.purge_all()
bg.control.purge_expired()
```
- **create_tables**: Create ```access``` table and ```blocked``` table if not exist.
- **drop_tables**: Drop ```access``` table and ```blocked``` table if exist.
- **purge_all**: Purge all data from ```access``` table and ```blocked``` table.
- **purge_expired**: Purge all expired data from ```access``` table and ```blocked``` table.