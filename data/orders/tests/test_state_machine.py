"""state_machine 模块测试"""

import pytest

from data.orders.state_machine import (
    OrderStatus,
    TERMINAL_STATUSES,
    is_known_status,
    is_terminal,
    is_valid_transition,
    assert_valid_transition,
    next_states,
    InvalidStateTransition,
)


# -------- 6 态枚举存在性 --------


def test_all_six_statuses_defined():
    assert {s.value for s in OrderStatus} == {
        "pending",
        "paid",
        "serving",
        "delivered",
        "completed",
        "refunded",
    }


# -------- 终态判定 --------


def test_terminal_statuses_are_completed_and_refunded():
    assert TERMINAL_STATUSES == frozenset({"completed", "refunded"})


def test_is_terminal_true_for_terminals():
    assert is_terminal("completed") is True
    assert is_terminal("refunded") is True


def test_is_terminal_false_for_non_terminals():
    for s in ("pending", "paid", "serving", "delivered"):
        assert is_terminal(s) is False


def test_is_terminal_false_for_unknown():
    assert is_terminal("not_a_status") is False


# -------- 合法转换 --------


@pytest.mark.parametrize(
    "from_,to",
    [
        ("pending", "paid"),
        ("paid", "serving"),
        ("serving", "delivered"),
        ("delivered", "completed"),
        ("pending", "refunded"),
        ("paid", "refunded"),
        ("serving", "refunded"),
        ("delivered", "refunded"),
    ],
)
def test_valid_transitions(from_, to):
    assert is_valid_transition(from_, to) is True
    # assert_valid_transition 不抛
    assert_valid_transition(from_, to)


# -------- 非法转换 --------


@pytest.mark.parametrize(
    "from_,to",
    [
        # 倒退
        ("paid", "pending"),
        ("serving", "paid"),
        ("delivered", "serving"),
        ("completed", "delivered"),
        # 跨级跳跃
        ("pending", "serving"),
        ("pending", "delivered"),
        ("pending", "completed"),
        ("paid", "delivered"),
        ("paid", "completed"),
        # 终态之后
        ("completed", "refunded"),
        ("refunded", "pending"),
        ("refunded", "paid"),
        # 相同状态
        ("pending", "pending"),
        ("paid", "paid"),
    ],
)
def test_invalid_transitions(from_, to):
    assert is_valid_transition(from_, to) is False
    with pytest.raises(InvalidStateTransition):
        assert_valid_transition(from_, to)


# -------- 未知状态 --------


def test_unknown_from_status_returns_false():
    assert is_valid_transition("unknown", "paid") is False


def test_unknown_to_status_returns_false():
    assert is_valid_transition("pending", "unknown") is False


def test_assert_unknown_from_raises():
    with pytest.raises(InvalidStateTransition):
        assert_valid_transition("foo", "paid")


def test_assert_unknown_to_raises():
    with pytest.raises(InvalidStateTransition):
        assert_valid_transition("pending", "foo")


# -------- next_states --------


def test_next_states_for_pending():
    assert next_states("pending") == frozenset({"paid", "refunded"})


def test_next_states_for_completed_is_empty():
    assert next_states("completed") == frozenset()


def test_next_states_for_refunded_is_empty():
    assert next_states("refunded") == frozenset()


def test_next_states_for_unknown_is_empty():
    assert next_states("xxx") == frozenset()


# -------- is_known_status --------


def test_is_known_status():
    for s in ("pending", "paid", "serving", "delivered", "completed", "refunded"):
        assert is_known_status(s) is True
    assert is_known_status("xxx") is False
    assert is_known_status("") is False


# -------- 完整业务路径 --------


def test_full_happy_path():
    """完整业务路径 pending → paid → serving → delivered → completed。"""
    path = ["pending", "paid", "serving", "delivered", "completed"]
    for i in range(len(path) - 1):
        assert_valid_transition(path[i], path[i + 1])


def test_refund_path_from_any_non_terminal():
    """任意非终态可退款。"""
    for s in ("pending", "paid", "serving", "delivered"):
        assert_valid_transition(s, "refunded")


def test_cannot_transition_from_terminal():
    """终态之后任何转换都非法。"""
    with pytest.raises(InvalidStateTransition):
        assert_valid_transition("completed", "paid")
    with pytest.raises(InvalidStateTransition):
        assert_valid_transition("refunded", "paid")
