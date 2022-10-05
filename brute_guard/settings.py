from enum import Enum


class AccessResult(Enum):
    SUCCESS = "success"
    FAIL = "fail"


TB_ACCESS = "access"
TB_BLOCKED_LIST = "blocked"

COLUMN_USERNAME = "username"
COLUMN_IP = "ip"