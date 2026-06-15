"""用户端 Web 自助订单创建流程（T12.3）。"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from data.orders.dao import OrdersDAO
from data.orders.models import Order, generate_order_id


ServiceVersion = Literal["audit", "basic", "standard", "premium"]
_SERVICE_PRICES: dict[ServiceVersion, int] = {
    "audit": 4900,
    "basic": 4900,
    "standard": 9900,
    "premium": 19900,
}


def service_price_for(service_version: ServiceVersion) -> int:
    return _SERVICE_PRICES[service_version]


class PublicOrderCreate(BaseModel):
    service_version: ServiceVersion
    amount_cents: int = Field(ge=0)
    customer_name: str = Field(min_length=1)
    customer_phone: Optional[str] = None
    customer_wechat: Optional[str] = None
    customer_email: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_province: str = Field(min_length=1)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _require_contact_channel(self) -> "PublicOrderCreate":
        if not self.customer_phone and not self.customer_wechat:
            raise ValueError("customer_phone / customer_wechat 至少填写一个")
        expected_amount = service_price_for(self.service_version)
        if self.amount_cents != expected_amount:
            raise ValueError("amount_cents 与套餐价格不一致")
        return self


class PublicOrderCreated(BaseModel):
    order_id: str
    source: str
    status: str
    service_version: str
    amount_cents: int
    next_step: str


def create_public_order(dao: OrdersDAO, request: PublicOrderCreate) -> Order:
    order = Order(
        id=generate_order_id(),
        source="web",
        service_version=request.service_version,
        amount_cents=service_price_for(request.service_version),
        status="pending",
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        customer_wechat=request.customer_wechat,
        customer_email=request.customer_email,
        candidate_name=request.candidate_name,
        candidate_province=request.candidate_province,
        notes=request.notes,
        tags=["web-self-service", f"package:{request.service_version}"],
    )
    return dao.create(order, actor="public_web", reason="public_create")


def to_created_payload(order: Order) -> PublicOrderCreated:
    return PublicOrderCreated(
        order_id=order.id,
        source=order.source,
        status=order.status,
        service_version=order.service_version,
        amount_cents=order.amount_cents,
        next_step="payment",
    )
