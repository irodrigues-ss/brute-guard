from enum import Enum


class AccessResult(Enum):
    SUCCESS = "success"
    FAIL = "fail"


class Columns(Enum):
    IP = "ip"
    USERNAME = "username"


TB_ACCESS = "access"
TB_BLOCKED_LIST = "blocked"
