"""订单状态机 (T4.1)

6 态状态机：pending → paid → serving → delivered → completed；
任何阶段可转入 refunded。completed / refunded 为终态。

非法转换抛 InvalidStateTransition；DAO 层捕获后回滚事务。
"""

from __future__ import annotations

from enum import Enum


class OrderStatus(str, Enum):
    """订单 6 态枚举（继承 str 以便直接写入 SQLite / JSON）。"""

    PENDING = "pending"
    PAID = "paid"
    SERVING = "serving"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    REFUNDED = "refunded"


TERMINAL_STATUSES: frozenset[str] = frozenset(
    {OrderStatus.COMPLETED.value, OrderStatus.REFUNDED.value}
)


# 合法状态转换：单向推进 + 任意阶段可退款
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    OrderStatus.PENDING.value: frozenset(
        {OrderStatus.PAID.value, OrderStatus.REFUNDED.value}
    ),
    OrderStatus.PAID.value: frozenset(
        {OrderStatus.SERVING.value, OrderStatus.REFUNDED.value}
    ),
    OrderStatus.SERVING.value: frozenset(
        {OrderStatus.DELIVERED.value, OrderStatus.REFUNDED.value}
    ),
    OrderStatus.DELIVERED.value: frozenset(
        {OrderStatus.COMPLETED.value, OrderStatus.REFUNDED.value}
    ),
    OrderStatus.COMPLETED.value: frozenset(),
    OrderStatus.REFUNDED.value: frozenset(),
}


class InvalidStateTransition(ValueError):
    """非法状态转换时抛出。"""


def is_known_status(status: str) -> bool:
    """判断字符串是否为已定义的 6 态之一。"""
    return status in {s.value for s in OrderStatus}


def is_terminal(status: str) -> bool:
    """判断状态是否为终态（completed / refunded）。"""
    return status in TERMINAL_STATUSES


def is_valid_transition(from_status: str, to_status: str) -> bool:
    """判断 from → to 是否为合法转换。

    - 已知状态但非法转换 → False
    - 未知状态 → False（不抛异常，DAO 层需先校验状态合法性）
    """
    if not (is_known_status(from_status) and is_known_status(to_status)):
        return False
    if from_status == to_status:
        # 相同状态视为非法（避免无意义的状态写入历史表）
        return False
    return to_status in ALLOWED_TRANSITIONS[from_status]


def assert_valid_transition(from_status: str, to_status: str) -> None:
    """校验状态转换合法性，非法时抛 InvalidStateTransition。"""
    if not is_known_status(from_status):
        raise InvalidStateTransition(f"未知起始状态: {from_status!r}")
    if not is_known_status(to_status):
        raise InvalidStateTransition(f"未知目标状态: {to_status!r}")
    if from_status == to_status:
        raise InvalidStateTransition(
            f"状态相同无需转换: {from_status!r} → {to_status!r}"
        )
    if to_status not in ALLOWED_TRANSITIONS[from_status]:
        allowed = sorted(ALLOWED_TRANSITIONS[from_status])
        raise InvalidStateTransition(
            f"非法状态转换: {from_status!r} → {to_status!r}（允许: {allowed}）"
        )


def next_states(from_status: str) -> frozenset[str]:
    """返回 from_status 的所有合法下一状态（用于前端展示）。"""
    if not is_known_status(from_status):
        return frozenset()
    return ALLOWED_TRANSITIONS[from_status]
