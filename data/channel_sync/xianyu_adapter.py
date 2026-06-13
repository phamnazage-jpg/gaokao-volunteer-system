"""闲鱼事件 → Order 模型适配器 (T8.1)

将 Webhook body 解析为 :class:`XianyuEvent`，再映射为内部 :class:`Order`。

设计要点:
- 仅接受设计文档 §4.1 列出的字段；其它字段（如身份证号）按 §5.5 一律丢弃
  并打上 ``pii_dropped`` 标记（写到 audit.reject_reason）
- service_version 规范化: 'audit' | 'basic' | 'standard' | 'premium'
- event_type → 状态映射见 §4.2
- 不可识别的 event_type 抛 :class:`XianyuEventError`
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from data.orders.models import Order, generate_order_id, utc_now_iso
from data.orders.state_machine import OrderStatus


# 闲鱼侧敏感字段黑名单（出现即丢弃 + 审计）
_PII_DROP_FIELDS: frozenset[str] = frozenset(
    {"id_card", "id_number", "身份证", "身份证号", "cert_no", "citizen_id"}
)

# service_version 白名单
_VALID_SERVICE_VERSIONS: frozenset[str] = frozenset(
    {"audit", "basic", "standard", "premium"}
)

# event_type → 订单状态（设计文档 §4.2）
EVENT_STATUS_MAP: dict[str, str] = {
    "order.created": OrderStatus.PENDING.value,
    "order.paid": OrderStatus.PAID.value,
    "order.delivered": OrderStatus.SERVING.value,
    "order.completed": OrderStatus.COMPLETED.value,
    "order.refunded": OrderStatus.REFUNDED.value,
}


class XianyuEventError(ValueError):
    """闲鱼事件解析或字段校验失败。"""


@dataclass
class XianyuEvent:
    """Webhook body 解析后的结构。"""

    event_id: str
    event_type: str
    order_id: str
    service_version: str
    amount_cents: int
    customer_name: str
    customer_phone: str
    customer_wechat: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_province: Optional[str] = None
    created_at: Optional[str] = None
    paid_at: Optional[str] = None
    refunded_at: Optional[str] = None

    # 解析时丢弃的 PII 字段名（用于审计 reject_reason='pii_dropped'）
    pii_dropped_fields: list[str] = field(default_factory=list)


def _coerce_amount(raw: Any) -> int:
    """把 amount 字段统一为分（int）。接受元/元字符串/数字。"""
    if isinstance(raw, int):
        return raw  # 已是分
    if isinstance(raw, float):
        return int(round(raw * 100))
    if isinstance(raw, str):
        s = raw.strip().replace("¥", "").replace("￥", "").replace(",", "")
        if not s:
            raise XianyuEventError("amount 不能为空")
        # 形如 "99.00" → 9900
        if "." in s:
            yuan = float(s)
            return int(round(yuan * 100))
        # 纯数字按元处理
        return int(s) * 100
    raise XianyuEventError(f"amount 字段类型非法: {type(raw).__name__}")


def parse_event(body: bytes | str) -> XianyuEvent:
    """解析 Webhook body 为 :class:`XianyuEvent`。

    - 必填字段缺失 → :class:`XianyuEventError`
    - PII 字段出现 → 静默丢弃并记录
    """
    if isinstance(body, bytes):
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as e:
            raise XianyuEventError(f"body 非 UTF-8: {e}") from e
    else:
        text = body
    if not text.strip():
        raise XianyuEventError("body 为空")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise XianyuEventError(f"body 非合法 JSON: {e}") from e
    if not isinstance(data, dict):
        raise XianyuEventError("body 顶层必须为对象")

    # 必填字段。注意: event_id="0" / amount=0 都是合法值,必须用 ``is None``
    # (而非 ``not``) 判定缺失,否则会被误判为 missing。
    event_id = data.get("event_id") or data.get("id")
    event_type = data.get("event_type") or data.get("type")
    order_id = data.get("order_id") or data.get("orderId")
    amount = data.get("amount")
    customer_name = data.get("customer_name")
    customer_phone = data.get("customer_phone")
    service_version = data.get("service_version") or "basic"

    missing = []
    if event_id is None or event_id == "":
        missing.append("event_id")
    if not event_type:
        missing.append("event_type")
    if not order_id:
        missing.append("order_id")
    if amount is None:
        missing.append("amount")
    if not customer_name:
        missing.append("customer_name")
    if not customer_phone:
        missing.append("customer_phone")
    if missing:
        raise XianyuEventError(f"必填字段缺失: {','.join(missing)}")

    if event_type not in EVENT_STATUS_MAP:
        raise XianyuEventError(
            f"未知 event_type: {event_type!r}; 支持: {sorted(EVENT_STATUS_MAP)}"
        )

    if service_version not in _VALID_SERVICE_VERSIONS:
        raise XianyuEventError(
            f"未知 service_version: {service_version!r}; "
            f"支持: {sorted(_VALID_SERVICE_VERSIONS)}"
        )

    # PII 字段检测（出现即记录丢弃，不抛错）
    pii_dropped: list[str] = []
    for f in _PII_DROP_FIELDS:
        if f in data and data[f]:
            pii_dropped.append(f)

    try:
        amount_cents = _coerce_amount(amount)
    except XianyuEventError:
        raise
    except Exception as e:  # 兜底
        raise XianyuEventError(f"amount 解析失败: {e}") from e

    if amount_cents < 0:
        raise XianyuEventError(f"amount 不能为负: {amount_cents}")

    return XianyuEvent(
        event_id=str(event_id),
        event_type=str(event_type),
        order_id=str(order_id),
        service_version=str(service_version),
        amount_cents=int(amount_cents),
        customer_name=str(customer_name),
        customer_phone=str(customer_phone),
        customer_wechat=data.get("customer_wechat"),
        candidate_name=data.get("candidate_name"),
        candidate_province=data.get("candidate_province"),
        created_at=data.get("created_at"),
        paid_at=data.get("paid_at"),
        refunded_at=data.get("refunded_at"),
        pii_dropped_fields=pii_dropped,
    )


def to_order(event: XianyuEvent) -> Order:
    """把 :class:`XianyuEvent` 映射为 :class:`Order`（尚未落库）。"""
    status = EVENT_STATUS_MAP[event.event_type]
    return Order(
        id=generate_order_id(),
        source="xianyu",
        external_id=event.order_id,
        service_version=event.service_version,
        amount_cents=event.amount_cents,
        status=status,
        customer_name=event.customer_name,
        customer_phone=event.customer_phone,
        customer_wechat=event.customer_wechat,
        candidate_name=event.candidate_name,
        candidate_province=event.candidate_province,
        notes=f"event_id={event.event_id}",
        created_at=event.created_at or utc_now_iso(),
        paid_at=event.paid_at,
        completed_at=(
            utc_now_iso()
            if event.event_type == "order.completed" and not event.refunded_at
            else None
        ),
    )


def target_status(event: XianyuEvent) -> str:
    """返回 :class:`XianyuEvent` 对应的目标状态。"""
    return EVENT_STATUS_MAP[event.event_type]
