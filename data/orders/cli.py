"""gaokao-order-manager CLI implementation (T4.3/T4.5)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from .dao import DuplicateOrder, OrderNotFound, OrdersDAO
from .models import Order, generate_order_id
from .state_machine import InvalidStateTransition

DEFAULT_DB_PATH = Path("data/orders.db")
_EXPORT_HEADERS = ("订单号", "渠道", "金额", "状态", "创建时间")


def _emit(payload: dict[str, Any], *, human: bool) -> None:
    if human:
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                print(f"{key}: {json.dumps(value, ensure_ascii=False, indent=2)}")
            else:
                print(f"{key}: {value}")
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _error(message: str, code: int = 1) -> int:
    print(message, file=sys.stderr)
    return code


def _serialize_order(order: Order) -> dict[str, Any]:
    return order.to_dict()


def _serialize_history(dao: OrdersDAO, order_id: str) -> list[dict[str, Any]]:
    return [asdict(item) for item in dao.get_status_history(order_id)]


def _build_order_from_args(args: argparse.Namespace) -> Order:
    return Order(
        id=generate_order_id(),
        source=args.source,
        external_id=args.external_id,
        service_version=args.service_version,
        amount_cents=args.amount_cents,
        status="pending",
        customer_name=args.customer_name,
        customer_phone=args.customer_phone,
        customer_wechat=args.customer_wechat,
        candidate_name=args.candidate_name,
        candidate_id_card=args.candidate_id_card,
        candidate_province=args.candidate_province,
        candidate_score=args.candidate_score,
        candidate_rank=args.candidate_rank,
        candidate_subjects=args.candidate_subjects or [],
        candidate_interests=args.candidate_interests,
        candidate_strong_subjects=args.candidate_strong_subjects,
        candidate_weak_subjects=args.candidate_weak_subjects,
        candidate_family=args.candidate_family,
        assigned_consultant=args.assigned_consultant,
        notes=args.note,
        tags=args.tags or [],
    )


def cmd_create(args: argparse.Namespace) -> int:
    order = _build_order_from_args(args)
    with OrdersDAO.connect(args.db) as dao:
        try:
            created = dao.create(order, actor=args.actor, reason=args.reason)
        except DuplicateOrder as exc:
            return _error(f"创建失败: {exc}")
        payload = {
            "action": "created",
            "order": _serialize_order(created),
            "history": _serialize_history(dao, created.id),
        }
    _emit(payload, human=args.human)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    with OrdersDAO.connect(args.db) as dao:
        try:
            orders = dao.list(
                status=args.status,
                source=args.source,
                limit=args.limit,
                offset=args.offset,
            )
        except ValueError as exc:
            return _error(f"查询失败: {exc}", code=2)
        payload = {
            "count": len(orders),
            "orders": [_serialize_order(order) for order in orders],
        }
    _emit(payload, human=args.human)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    with OrdersDAO.connect(args.db) as dao:
        try:
            order = dao.get(args.order_id)
        except OrderNotFound as exc:
            return _error(str(exc))
        payload = {
            "order": _serialize_order(order),
            "history": _serialize_history(dao, order.id),
        }
    _emit(payload, human=args.human)
    return 0


def _collect_updates(args: argparse.Namespace) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    field_names = (
        "external_id",
        "service_version",
        "amount_cents",
        "customer_name",
        "customer_wechat",
        "candidate_name",
        "candidate_province",
        "candidate_score",
        "candidate_rank",
        "candidate_interests",
        "candidate_strong_subjects",
        "candidate_weak_subjects",
        "candidate_family",
        "assigned_consultant",
        "plan_file",
        "audit_report",
        "pdf_path",
    )
    for name in field_names:
        value = getattr(args, name)
        if value is not None:
            updates[name] = value
    if args.note is not None:
        updates["notes"] = args.note
    if args.tags is not None:
        updates["tags"] = args.tags
    if args.candidate_subjects is not None:
        updates["candidate_subjects"] = args.candidate_subjects
    return updates


def cmd_update(args: argparse.Namespace) -> int:
    updates = _collect_updates(args)
    if not updates:
        return _error("至少指定一个可更新字段", code=2)
    with OrdersDAO.connect(args.db) as dao:
        try:
            order = dao.update(
                args.order_id, updates, actor=args.actor, reason=args.reason
            )
        except OrderNotFound as exc:
            return _error(str(exc))
        except ValueError as exc:
            return _error(f"更新失败: {exc}", code=2)
        payload = {
            "action": "updated",
            "order": _serialize_order(order),
        }
    _emit(payload, human=args.human)
    return 0


def _transition(
    dao: OrdersDAO,
    order_id: str,
    to_status: str,
    *,
    actor: str,
    reason: Optional[str],
) -> Order:
    return dao.transition_status(order_id, to_status, actor=actor, reason=reason)


def cmd_pay(args: argparse.Namespace) -> int:
    with OrdersDAO.connect(args.db) as dao:
        try:
            order = _transition(
                dao,
                args.order_id,
                "paid",
                actor=args.actor,
                reason=args.reason or "manual_pay",
            )
        except (OrderNotFound, InvalidStateTransition) as exc:
            return _error(str(exc))
        payload = {
            "action": "paid",
            "order": _serialize_order(order),
            "history": _serialize_history(dao, order.id),
        }
    _emit(payload, human=args.human)
    return 0


def cmd_deliver(args: argparse.Namespace) -> int:
    with OrdersDAO.connect(args.db) as dao:
        try:
            current = dao.get(args.order_id)
        except OrderNotFound as exc:
            return _error(str(exc))

        try:
            if current.status == "paid":
                _transition(
                    dao,
                    args.order_id,
                    "serving",
                    actor=args.actor,
                    reason=args.reason or "deliver:start_service",
                )
                order = _transition(
                    dao,
                    args.order_id,
                    "delivered",
                    actor=args.actor,
                    reason=args.reason or "deliver:done",
                )
            elif current.status == "serving":
                order = _transition(
                    dao,
                    args.order_id,
                    "delivered",
                    actor=args.actor,
                    reason=args.reason or "deliver:done",
                )
            else:
                return _error(
                    f"当前状态不允许 deliver: {current.status}；请先完成 pay 或人工推进到 serving"
                )
        except InvalidStateTransition as exc:
            return _error(str(exc))

        payload = {
            "action": "delivered",
            "order": _serialize_order(order),
            "history": _serialize_history(dao, order.id),
        }
    _emit(payload, human=args.human)
    return 0


def cmd_upgrade(args: argparse.Namespace) -> int:
    with OrdersDAO.connect(args.db) as dao:
        try:
            order = dao.upgrade_order(
                args.order_id,
                target_service_version=args.service_version,
                target_amount_cents=args.target_amount_cents,
                actor=args.actor,
                reason=args.reason,
            )
            source_order = dao.get(args.order_id)
        except (OrderNotFound, ValueError) as exc:
            return _error(str(exc), code=2)

        payload = {
            "action": "upgraded",
            "order": _serialize_order(order),
            "source_order": _serialize_order(source_order),
            "history": _serialize_history(dao, order.id),
        }
    _emit(payload, human=args.human)
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    with OrdersDAO.connect(args.db) as dao:
        by_status = dao.stats_by_status()
        by_source_rows = dao.conn.execute(
            "SELECT source, COUNT(*) AS n FROM orders GROUP BY source ORDER BY source ASC"
        ).fetchall()
        by_service_rows = dao.conn.execute(
            "SELECT service_version, COUNT(*) AS n FROM orders GROUP BY service_version ORDER BY service_version ASC"
        ).fetchall()
        payload = {
            "total_orders": dao.count(),
            "by_status": by_status,
            "by_source": {row[0]: int(row[1]) for row in by_source_rows},
            "by_service_version": {row[0]: int(row[1]) for row in by_service_rows},
        }
    _emit(payload, human=args.human)
    return 0


def _format_amount_cents(amount_cents: int) -> str:
    return f"{amount_cents / 100:.2f}"


def _export_row(order: Order) -> dict[str, str]:
    return {
        "订单号": order.id,
        "渠道": order.source,
        "金额": _format_amount_cents(order.amount_cents),
        "状态": order.status,
        "创建时间": order.created_at or "",
    }


def cmd_export(args: argparse.Namespace) -> int:
    output_path = Path(args.output)
    with OrdersDAO.connect(args.db) as dao:
        try:
            orders = dao.list(
                status=args.status,
                source=args.source,
                limit=args.limit,
                offset=0,
            )
        except ValueError as exc:
            return _error(f"导出失败: {exc}", code=2)

    rows = [_export_row(order) for order in orders]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(_EXPORT_HEADERS)
        for row in rows:
            writer.writerow([row[header] for header in _EXPORT_HEADERS])

    payload = {
        "action": "exported",
        "format": "csv",
        "output": str(output_path),
        "rows": len(rows),
    }
    _emit(payload, human=args.human)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gaokao-order-manager",
        description="高考志愿订单管理 CLI (T4.3)",
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite 数据库路径")
    parser.add_argument("--human", action="store_true", help="输出人类可读文本")
    parser.add_argument("--actor", default="order_cli", help="审计 actor")

    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="创建订单")
    create.add_argument("--source", required=True)
    create.add_argument("--external-id")
    create.add_argument("--service-version", required=True)
    create.add_argument("--amount-cents", type=int, required=True)
    create.add_argument("--customer-name")
    create.add_argument("--customer-phone")
    create.add_argument("--customer-wechat")
    create.add_argument("--candidate-name")
    create.add_argument("--candidate-id-card")
    create.add_argument("--candidate-province")
    create.add_argument("--candidate-score", type=int)
    create.add_argument("--candidate-rank", type=int)
    create.add_argument(
        "--candidate-subject", dest="candidate_subjects", action="append"
    )
    create.add_argument("--candidate-interests")
    create.add_argument("--candidate-strong-subjects")
    create.add_argument("--candidate-weak-subjects")
    create.add_argument("--candidate-family")
    create.add_argument("--assigned-consultant")
    create.add_argument("--note")
    create.add_argument("--tag", dest="tags", action="append")
    create.add_argument("--reason")
    create.set_defaults(func=cmd_create)

    list_parser = subparsers.add_parser("list", help="分页列出订单")
    list_parser.add_argument("--status")
    list_parser.add_argument("--source")
    list_parser.add_argument("--limit", type=int, default=50)
    list_parser.add_argument("--offset", type=int, default=0)
    list_parser.set_defaults(func=cmd_list)

    show = subparsers.add_parser("show", help="查看订单详情")
    show.add_argument("order_id")
    show.set_defaults(func=cmd_show)

    update = subparsers.add_parser("update", help="更新订单业务字段")
    update.add_argument("order_id")
    update.add_argument("--external-id")
    update.add_argument("--service-version")
    update.add_argument("--amount-cents", type=int)
    update.add_argument("--customer-name")
    update.add_argument("--customer-wechat")
    update.add_argument("--candidate-name")
    update.add_argument("--candidate-province")
    update.add_argument("--candidate-score", type=int)
    update.add_argument("--candidate-rank", type=int)
    update.add_argument(
        "--candidate-subject", dest="candidate_subjects", action="append"
    )
    update.add_argument("--candidate-interests")
    update.add_argument("--candidate-strong-subjects")
    update.add_argument("--candidate-weak-subjects")
    update.add_argument("--candidate-family")
    update.add_argument("--assigned-consultant")
    update.add_argument("--plan-file")
    update.add_argument("--audit-report")
    update.add_argument("--pdf-path")
    update.add_argument("--note")
    update.add_argument("--tag", dest="tags", action="append")
    update.add_argument("--reason")
    update.set_defaults(func=cmd_update)

    pay = subparsers.add_parser("pay", help="标记已支付")
    pay.add_argument("order_id")
    pay.add_argument("--reason")
    pay.set_defaults(func=cmd_pay)

    deliver = subparsers.add_parser("deliver", help="推进到已交付")
    deliver.add_argument("order_id")
    deliver.add_argument("--reason")
    deliver.set_defaults(func=cmd_deliver)

    upgrade = subparsers.add_parser("upgrade", help="创建补差价升级订单")
    upgrade.add_argument("order_id")
    upgrade.add_argument("--service-version", required=True)
    upgrade.add_argument("--target-amount-cents", type=int, required=True)
    upgrade.add_argument("--reason")
    upgrade.set_defaults(func=cmd_upgrade)

    stats = subparsers.add_parser("stats", help="查看订单统计")
    stats.set_defaults(func=cmd_stats)

    export = subparsers.add_parser("export", help="导出最小订单报表 CSV")
    export.add_argument("--output", required=True, help="输出 CSV 文件路径")
    export.add_argument("--status")
    export.add_argument("--source")
    export.add_argument("--limit", type=int, default=1000)
    export.set_defaults(func=cmd_export)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
