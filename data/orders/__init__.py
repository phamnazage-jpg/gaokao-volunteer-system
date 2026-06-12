"""订单数据模块 (T4.1 + T4.2)

提供：
- SQLite schema（AES-256 加密字段 + 6 态状态机 + 审计表）
- Fernet 加密/解密/索引哈希派生
- 6 态订单状态机
- ``Order`` dataclass + 加密/脱敏序列化
- ``OrdersDAO`` 完整 CRUD + 事务 + 状态机守护（**T4.2**）

下游使用
--------

```python
import os
os.environ["GAOKAO_ORDERS_FERNET_KEY"] = "your-secret-here"

from data.orders import (
    # schema
    apply_schema,
    # crypto
    encrypt, decrypt, hash_for_index,
    # state machine
    assert_valid_transition, OrderStatus,
    # models
    Order, generate_order_id,
    # DAO (T4.2)
    OrdersDAO, UpsertResult, StatusChange,
    OrderNotFound, DuplicateOrder,
)
```
"""

from .crypto import (
    ENV_KEY_NAME,
    EncryptionError,
    MissingEncryptionKey,
    constant_time_equals,
    decrypt,
    derive_key,
    encrypt,
    get_fernet,
    hash_for_index,
)
from .dao import (
    DuplicateOrder,
    OrderNotFound,
    OrdersDAO,
    StatusChange,
    UpsertResult,
)
from .models import (
    DecryptPolicy,
    Order,
    generate_order_id,
    utc_now_iso,
)
from .schema import SCHEMA_SQL, apply_schema, get_schema_version
from .state_machine import (
    ALLOWED_TRANSITIONS,
    InvalidStateTransition,
    OrderStatus,
    TERMINAL_STATUSES,
    assert_valid_transition,
    is_known_status,
    is_terminal,
    is_valid_transition,
    next_states,
)

__all__ = [
    # schema
    "SCHEMA_SQL",
    "apply_schema",
    "get_schema_version",
    # crypto
    "ENV_KEY_NAME",
    "EncryptionError",
    "MissingEncryptionKey",
    "constant_time_equals",
    "decrypt",
    "derive_key",
    "encrypt",
    "get_fernet",
    "hash_for_index",
    # state machine
    "ALLOWED_TRANSITIONS",
    "InvalidStateTransition",
    "OrderStatus",
    "TERMINAL_STATUSES",
    "assert_valid_transition",
    "is_known_status",
    "is_terminal",
    "is_valid_transition",
    "next_states",
    # models
    "DecryptPolicy",
    "Order",
    "generate_order_id",
    "utc_now_iso",
    # DAO
    "DuplicateOrder",
    "OrderNotFound",
    "OrdersDAO",
    "StatusChange",
    "UpsertResult",
]
