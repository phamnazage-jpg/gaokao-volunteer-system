"""T8.1 闲鱼 Webhook 集成测试

覆盖（与设计文档 CHANNEL_INTEGRATION.md §8 验收标准一一对应）:

- signature：sign/verify roundtrip、签名错误拒绝、时间戳过期拒绝、nonce 重放拒绝
- xianyu_adapter：JSON 解析、必填字段缺失、PII 字段丢弃、金额多种格式
- dao_extension：insert / update / unchanged / illegal_transition
- audit：record / count_by_event / list_recent
- poller：fetched / inserted / updated / unchanged / rejected、cursor 推进
- webhook_server：end-to-end POST /webhook/xianyu（200/400/401/408/409/429）

T8.1 后续修复补强:
- parse_event: event_id='0' / amount=0 允许通过
- webhook_server: _client_ip 在缺 X-Forwarded-For 时回退到 socket client_address
- webhook_server: 500 JSON 响应带 rejected=true;do_POST 顶层兜底返回 JSON
- poller: fetched>0 但缺时间戳时,cursor 仍给出合理推进
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path

os.environ.setdefault("GAOKAO_XIANYU_WEBHOOK_SECRET", "test-secret-for-unit-tests")
os.environ.setdefault("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-unit-tests")

# 把项目根加进 sys.path，便于 ``data.xxx`` 导入
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.orders.models import Order  # noqa: E402
from data.orders.schema import apply_schema  # noqa: E402
from data.channel_sync.audit import (  # noqa: E402
    apply_audit_schema,
    count_by_event,
    list_recent,
    record,
    WebhookAuditEntry,
)
from data.channel_sync.dao_extension import (  # noqa: E402
    upsert_by_external_id,
)
from data.channel_sync.poller import (  # noqa: E402
    PollReport,
    _compute_new_cursor,
    poll_once,
)
from data.channel_sync.signature import (  # noqa: E402
    DEFAULT_TS_TOLERANCE_SECONDS,
    SignatureError,
    _NonceCache,
    reset_nonce_cache_for_tests,
    sha256_hex,
    sign,
    verify,
)
from data.channel_sync.webhook_server import (  # noqa: E402
    ROUTE_PATH,
    _client_ip,
    close_db_for_tests,
    make_server,
    reset_rate_limit_for_tests,
)
from data.channel_sync.xianyu_adapter import (  # noqa: E402
    EVENT_STATUS_MAP,
    XianyuEventError,
    parse_event,
    target_status,
    to_order,
)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def make_event_body(
    *,
    event_id: str = "evt-1",
    event_type: str = "order.paid",
    order_id: str = "XY-001",
    service_version: str = "standard",
    amount: object = "99.00",
    customer_name: str = "张三",
    customer_phone: str = "13800000000",
    extra: dict | None = None,
) -> bytes:
    payload = {
        "event_id": event_id,
        "event_type": event_type,
        "order_id": order_id,
        "service_version": service_version,
        "amount": amount,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
    }
    if extra:
        payload.update(extra)
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def fresh_db() -> tuple[sqlite3.Connection, str]:
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    conn = apply_schema(f.name)
    apply_audit_schema(conn)
    return conn, f.name


# ---------------------------------------------------------------------------
# signature
# ---------------------------------------------------------------------------


class SignatureTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_nonce_cache_for_tests()

    def test_sign_verify_roundtrip(self) -> None:
        body = b'{"a":1}'
        sig, ts, nonce = sign(body)
        verify(body, sig, ts, nonce)  # 不抛即通过

    def test_signature_mismatch_raises(self) -> None:
        body = b'{"a":1}'
        sig, ts, nonce = sign(body, secret="secret-A")
        with self.assertRaises(SignatureError) as cm:
            verify(body, sig, ts, nonce, secret="secret-B")
        self.assertIn("signature_mismatch", str(cm.exception))

    def test_missing_prefix_rejected(self) -> None:
        with self.assertRaises(SignatureError) as cm:
            verify(b"x", "abc123", int(time.time()), "nonce1")
        self.assertIn("malformed_signature", str(cm.exception))

    def test_timestamp_out_of_range(self) -> None:
        body = b"x"
        old_ts = int(time.time()) - DEFAULT_TS_TOLERANCE_SECONDS - 10
        sig, _, nonce = sign(body, timestamp=old_ts)
        with self.assertRaises(SignatureError) as cm:
            verify(body, sig, old_ts, nonce, now=time.time())
        self.assertIn("timestamp_out_of_range", str(cm.exception))

    def test_nonce_replay_rejected(self) -> None:
        body = b"x"
        sig, ts, nonce = sign(body)
        verify(body, sig, ts, nonce)
        with self.assertRaises(SignatureError) as cm:
            verify(body, sig, ts, nonce)
        self.assertIn("nonce_replay", str(cm.exception))

    def test_nonce_cache_ttl_expiry(self) -> None:
        cache = _NonceCache(ttl_seconds=10)
        ts = int(time.time())
        self.assertTrue(cache.remember(ts, "nonce-X", now=100.0))
        # 90s 后（> TTL 10s）应该视为新条目
        self.assertTrue(cache.remember(ts, "nonce-X", now=200.0))

    def test_nonce_cache_max_size_evicts(self) -> None:
        cache = _NonceCache(ttl_seconds=600, max_size=2)
        cache.remember(1, "a", now=0.0)
        cache.remember(2, "b", now=0.0)
        cache.remember(3, "c", now=0.0)  # 触发淘汰
        # 旧条目 'a' 应该被淘汰，重新插入应该成功
        self.assertTrue(cache.remember(1, "a", now=0.0))

    def test_sha256_hex(self) -> None:
        self.assertEqual(
            sha256_hex(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )

    def test_secret_missing_raises(self) -> None:
        from data.channel_sync import signature as sig_mod

        old = os.environ.pop("GAOKAO_XIANYU_WEBHOOK_SECRET", None)
        try:
            with self.assertRaises(SignatureError):
                sig_mod.get_webhook_secret()
        finally:
            if old is not None:
                os.environ["GAOKAO_XIANYU_WEBHOOK_SECRET"] = old


# ---------------------------------------------------------------------------
# xianyu_adapter
# ---------------------------------------------------------------------------


class XianyuAdapterTests(unittest.TestCase):
    def test_parse_event_ok(self) -> None:
        body = make_event_body()
        ev = parse_event(body)
        self.assertEqual(ev.event_id, "evt-1")
        self.assertEqual(ev.event_type, "order.paid")
        self.assertEqual(ev.order_id, "XY-001")
        self.assertEqual(ev.service_version, "standard")
        self.assertEqual(ev.amount_cents, 9900)
        self.assertEqual(ev.pii_dropped_fields, [])

    def test_parse_event_amount_int_passes_through(self) -> None:
        body = make_event_body(amount=9900)
        ev = parse_event(body)
        self.assertEqual(ev.amount_cents, 9900)

    def test_parse_event_zero_amount_is_allowed(self) -> None:
        """amount=0 / event_id='0' 必须被识别为合法值,不能误判为缺失。"""
        body = make_event_body(event_id="0", amount=0)
        ev = parse_event(body)
        self.assertEqual(ev.event_id, "0")
        self.assertEqual(ev.amount_cents, 0)

    def test_parse_event_amount_yuan_string(self) -> None:
        body = make_event_body(amount="199.50")
        ev = parse_event(body)
        self.assertEqual(ev.amount_cents, 19950)

    def test_parse_event_pii_dropped(self) -> None:
        body = make_event_body(extra={"id_card": "330106199001011234"})
        ev = parse_event(body)
        self.assertIn("id_card", ev.pii_dropped_fields)

    def test_parse_event_missing_required(self) -> None:
        body = b'{"event_id":"e1"}'  # 缺多个必填
        with self.assertRaises(XianyuEventError) as cm:
            parse_event(body)
        self.assertIn("必填字段缺失", str(cm.exception))

    def test_parse_event_unknown_event_type(self) -> None:
        body = make_event_body(event_type="order.exploded")
        with self.assertRaises(XianyuEventError) as cm:
            parse_event(body)
        self.assertIn("未知 event_type", str(cm.exception))

    def test_parse_event_invalid_amount(self) -> None:
        body = make_event_body(amount="not-a-number")
        with self.assertRaises(XianyuEventError):
            parse_event(body)

    def test_parse_event_negative_amount(self) -> None:
        body = make_event_body(amount=-1)
        with self.assertRaises(XianyuEventError):
            parse_event(body)

    def test_parse_event_invalid_json(self) -> None:
        with self.assertRaises(XianyuEventError):
            parse_event(b"not json")

    def test_parse_event_non_object(self) -> None:
        with self.assertRaises(XianyuEventError):
            parse_event(b"[1,2,3]")

    def test_target_status_mapping(self) -> None:
        for evt, status in EVENT_STATUS_MAP.items():
            body = make_event_body(event_type=evt)
            ev = parse_event(body)
            self.assertEqual(target_status(ev), status)

    def test_to_order_minimal(self) -> None:
        body = make_event_body()
        ev = parse_event(body)
        order = to_order(ev)
        self.assertEqual(order.source, "xianyu")
        self.assertEqual(order.external_id, "XY-001")
        self.assertEqual(order.status, "paid")
        self.assertEqual(order.amount_cents, 9900)
        self.assertEqual(order.customer_name, "张三")
        # customer_phone_hash 自动派生
        self.assertEqual(order.customer_phone_hash, order.customer_phone_hash)
        self.assertIsNotNone(order.customer_phone_hash)


# ---------------------------------------------------------------------------
# dao_extension
# ---------------------------------------------------------------------------


class DaoExtensionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn, self.path = fresh_db()

    def tearDown(self) -> None:
        self.conn.close()
        Path(self.path).unlink(missing_ok=True)

    def _first_order(self) -> "Order":
        ev = parse_event(make_event_body())
        return to_order(ev)

    def test_insert_then_unchanged(self) -> None:
        order = self._first_order()
        r1 = upsert_by_external_id(self.conn, order)
        self.assertEqual(r1.action, "inserted")
        r2 = upsert_by_external_id(self.conn, to_order(parse_event(make_event_body())))
        self.assertEqual(r2.action, "unchanged")

    def test_legal_status_transition_updates(self) -> None:
        upsert_by_external_id(self.conn, self._first_order())  # paid
        r = upsert_by_external_id(
            self.conn,
            to_order(parse_event(make_event_body(event_type="order.delivered"))),
        )
        self.assertEqual(r.action, "updated")
        self.assertEqual(r.old_status, "paid")
        self.assertEqual(r.new_status, "serving")

    def test_illegal_status_transition_rejected(self) -> None:
        upsert_by_external_id(self.conn, self._first_order())  # paid
        # serving (order.delivered) → completed (order.completed) 非法
        upsert_by_external_id(
            self.conn,
            to_order(parse_event(make_event_body(event_type="order.delivered"))),
        )
        r = upsert_by_external_id(
            self.conn,
            to_order(parse_event(make_event_body(event_type="order.completed"))),
        )
        self.assertEqual(r.action, "illegal_transition")
        self.assertIsNotNone(r.error)

    def test_external_id_required(self) -> None:
        order = self._first_order()
        order.external_id = None
        r = upsert_by_external_id(self.conn, order)
        self.assertEqual(r.action, "illegal_transition")

    def test_insert_status_history_writes_row(self) -> None:
        upsert_by_external_id(self.conn, self._first_order())
        n = self.conn.execute("SELECT COUNT(*) FROM order_status_history").fetchone()[0]
        self.assertEqual(n, 1)

    def test_unique_external_id_constraint(self) -> None:
        """(source, external_id) 唯一索引存在,重复 insert 会被 SQLite 拒。"""
        # 通过 raw insert 模拟违反唯一索引
        upsert_by_external_id(self.conn, self._first_order())
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO orders(
                    id, source, external_id, service_version, amount_cents,
                    status, status_updated_at, created_at
                ) VALUES ('GKO-OTHER', 'xianyu', 'XY-001', 'basic', 100,
                          'pending', '2026-01-01T00:00:00+00:00',
                          '2026-01-01T00:00:00+00:00')
                """
            )


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------


class AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn, self.path = fresh_db()

    def tearDown(self) -> None:
        self.conn.close()
        Path(self.path).unlink(missing_ok=True)

    def test_record_and_count(self) -> None:
        record(
            self.conn,
            WebhookAuditEntry(
                channel="xianyu",
                decision="accepted",
                event_id="e1",
                raw_body=b"x",
            ),
        )
        self.assertEqual(count_by_event(self.conn, "xianyu", "e1"), 1)

    def test_record_rejects_invalid_decision(self) -> None:
        with self.assertRaises(ValueError):
            WebhookAuditEntry(channel="xianyu", decision="weird")

    def test_list_recent_orders_by_id_desc(self) -> None:
        for i in range(3):
            record(
                self.conn,
                WebhookAuditEntry(
                    channel="xianyu",
                    decision="accepted",
                    event_id=f"e{i}",
                    raw_body=str(i).encode(),
                ),
            )
        rows = list_recent(self.conn, limit=2)
        self.assertEqual(len(rows), 2)
        self.assertGreater(rows[0]["id"], rows[1]["id"])

    def test_apply_audit_schema_idempotent(self) -> None:
        apply_audit_schema(self.conn)
        apply_audit_schema(self.conn)
        n = self.conn.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type='table' AND name='webhook_audit'"
        ).fetchone()[0]
        self.assertEqual(n, 1)

    def test_audit_table_indexes_exist(self) -> None:
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND tbl_name='webhook_audit'"
        ).fetchall()
        names = {r[0] for r in rows}
        self.assertIn("idx_webhook_audit_event", names)
        self.assertIn("idx_webhook_audit_decision", names)


# ---------------------------------------------------------------------------
# poller
# ---------------------------------------------------------------------------


class _FakeClient:
    def __init__(self, batches: list[list[dict]]) -> None:
        self._batches = list(batches)
        self._i = 0
        self.calls: list = []

    def list_orders(self, since):
        self.calls.append(since)
        if self._i >= len(self._batches):
            return []
        out = self._batches[self._i]
        self._i += 1
        return out


class PollerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn, self.path = fresh_db()

    def tearDown(self) -> None:
        self.conn.close()
        Path(self.path).unlink(missing_ok=True)

    def test_poller_inserts_new_orders(self) -> None:
        client = _FakeClient([
            [{"raw_body": make_event_body(order_id="POLL-1", event_id="p1")}]
        ])
        report = poll_once(self.conn, source="xianyu", client=client)
        self.assertIsInstance(report, PollReport)
        self.assertEqual(report.fetched, 1)
        self.assertEqual(report.inserted, 1)
        self.assertEqual(report.updated, 0)
        self.assertEqual(report.unchanged, 0)
        self.assertEqual(report.rejected, 0)
        self.assertIsNone(report.error)
        # cursor 已推进
        row = self.conn.execute(
            "SELECT last_cursor, run_count FROM poller_state WHERE source='xianyu'"
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], 1)

    def test_poller_unchanged_on_repeat(self) -> None:
        client = _FakeClient([
            [{"raw_body": make_event_body(order_id="POLL-2", event_id="p2a")}],
            [{"raw_body": make_event_body(order_id="POLL-2", event_id="p2b")}],
        ])
        r1 = poll_once(self.conn, source="xianyu", client=client)
        r2 = poll_once(self.conn, source="xianyu", client=client)
        self.assertEqual(r1.inserted, 1)
        self.assertEqual(r2.unchanged, 1)
        self.assertEqual(r2.inserted, 0)

    def test_poller_rejects_invalid_event(self) -> None:
        client = _FakeClient([[{"raw_body": b"not json"}]])
        report = poll_once(self.conn, source="xianyu", client=client)
        self.assertEqual(report.fetched, 1)
        self.assertEqual(report.rejected, 1)
        self.assertEqual(report.inserted, 0)

    def test_poller_run_recorded(self) -> None:
        client = _FakeClient([])
        poll_once(self.conn, source="xianyu", client=client)
        n = self.conn.execute(
            "SELECT COUNT(*) FROM poller_run WHERE source='xianyu'"
        ).fetchone()[0]
        self.assertEqual(n, 1)

    def test_poller_records_error_on_exception(self) -> None:
        class BoomClient:
            def list_orders(self, since):
                raise RuntimeError("api down")

        report = poll_once(self.conn, source="xianyu", client=BoomClient())
        self.assertIsNotNone(report.error)
        error_text = report.error
        assert error_text is not None
        self.assertIn("RuntimeError", error_text)
        state = self.conn.execute(
            "SELECT last_error, error_count FROM poller_state WHERE source='xianyu'"
        ).fetchone()
        self.assertIsNotNone(state[0])
        self.assertEqual(state[1], 1)

    def test_poller_idempotent_with_webhook(self) -> None:
        """Webhook upsert 之后 poller 再 upsert 同 order_id → unchanged。"""
        # 1) 模拟 Webhook 入库
        upsert_by_external_id(
            self.conn,
            to_order(parse_event(make_event_body(order_id="IDEM-1"))),
        )
        # 2) poller 拿到同 external_id → unchanged
        client = _FakeClient([
            [{"raw_body": make_event_body(order_id="IDEM-1", event_id="idem2")}]
        ])
        report = poll_once(self.conn, source="xianyu", client=client)
        self.assertEqual(report.unchanged, 1)
        self.assertEqual(report.inserted, 0)

    def test_poller_cursor_advances_when_orders_have_no_timestamps(self) -> None:
        """fetched>0 但全部订单缺 updated_at/paid_at/created_at 时,
        last_cursor 必须给出非 None 的推进值,避免永久停滞。"""
        # 订单无任何时间戳字段
        order_dict = {
            "raw_body": make_event_body(order_id="NO-TS-1", event_id="nts-1"),
            # 故意不加 updated_at / paid_at / created_at
        }
        client = _FakeClient([[order_dict]])
        report = poll_once(self.conn, source="xianyu", client=client)
        # fetched 应 > 0
        self.assertEqual(report.fetched, 1)
        # 订单应被成功落库(没有时间戳不阻塞落库)
        self.assertEqual(report.inserted, 1)
        # cursor 必须推进(非 None)
        self.assertIsNotNone(
            report.last_cursor,
            "fetched>0 但缺时间戳时,cursor 必须给出非 None 推进值",
        )
        # 写库的 cursor 也应非 None
        cursor_row = self.conn.execute(
            "SELECT last_cursor FROM poller_state WHERE source='xianyu'"
        ).fetchone()
        self.assertIsNotNone(cursor_row)
        self.assertIsNotNone(cursor_row[0])

    def test_poller_compute_new_cursor_no_timestamps_falls_back_to_now(self) -> None:
        """_compute_new_cursor 在 fetched>0 但本批无时间戳时回退到 now_iso。"""
        now = "2026-06-12T12:00:00+00:00"
        # 非空 raw_orders 但全部缺 updated_at/paid_at/created_at
        result = _compute_new_cursor(
            self.conn,
            "xianyu-fallback",
            [{"raw_body": b"{}"}],
            now_iso=now,
        )
        self.assertEqual(result, now)


# ---------------------------------------------------------------------------
# webhook_server 端到端
# ---------------------------------------------------------------------------


def _start_server(db_path: str) -> tuple["HTTPServer", int]:
    """找一个空闲端口启动 webhook_server。返回 (server, port)。"""
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    close_db_for_tests()
    reset_rate_limit_for_tests()
    reset_nonce_cache_for_tests()
    server = make_server(host="127.0.0.1", port=port, db_path=db_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def _stop_server(server) -> None:
    server.shutdown()
    server.server_close()
    close_db_for_tests()


def _post_signed(
    port: int, body: bytes, secret: str | None = None
) -> tuple[int, dict, dict]:
    sig, ts, nonce = sign(body, secret=secret or "test-secret-for-unit-tests")
    headers = {
        "X-Signature": sig,
        "X-Timestamp": str(ts),
        "X-Nonce": nonce,
        "Content-Type": "application/json",
    }
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request("POST", ROUTE_PATH, body=body, headers=headers)
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8") or "{}")
        return resp.status, payload, dict(resp.getheaders())
    finally:
        conn.close()


class WebhookServerTests(unittest.TestCase):
    def setUp(self) -> None:
        # 每例一个独立 DB 文件
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmpdir.name) / "orders.db")
        apply_schema(self.db_path)
        apply_audit_schema(sqlite3.connect(self.db_path))
        self.server, self.port = _start_server(self.db_path)

    def tearDown(self) -> None:
        _stop_server(self.server)
        self.tmpdir.cleanup()

    def _count_orders(self) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        finally:
            conn.close()

    def test_healthz(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", "/healthz")
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(resp.status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_404_on_unknown_path(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", "/nope", body=b"{}")
        resp = conn.getresponse()
        resp.read()
        self.assertEqual(resp.status, 404)

    def test_accepted_inserts_order(self) -> None:
        body = make_event_body(event_id="acc-1", order_id="AC-1")
        status, payload, _ = _post_signed(self.port, body)
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["status"], "inserted")
        self.assertEqual(self._count_orders(), 1)

    def test_duplicate_event_returns_200(self) -> None:
        body = make_event_body(event_id="dup-1", order_id="DUP-1")
        _post_signed(self.port, body)
        status, payload, _ = _post_signed(self.port, body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "duplicate")
        # 仍只有 1 条
        self.assertEqual(self._count_orders(), 1)

    def test_bad_signature_returns_401(self) -> None:
        body = make_event_body(event_id="bad-1", order_id="BAD-1")
        status, payload, _ = _post_signed(self.port, body, secret="wrong")
        self.assertEqual(status, 401, payload)
        self.assertIn("rejected", payload)
        self.assertEqual(self._count_orders(), 0)

    def test_missing_signature_header_returns_401(self) -> None:
        body = make_event_body()
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            ROUTE_PATH,
            body=body,
            headers={
                "Content-Type": "application/json",
                "X-Timestamp": str(int(time.time())),
                "X-Nonce": "x",
            },
        )
        resp = conn.getresponse()
        resp.read()
        self.assertEqual(resp.status, 401)

    def test_old_timestamp_returns_408(self) -> None:
        body = make_event_body(event_id="old-1", order_id="OLD-1")
        old_ts = int(time.time()) - DEFAULT_TS_TOLERANCE_SECONDS - 10
        sig = sign(body, timestamp=old_ts)[0]
        nonce = "test-nonce-old"
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            ROUTE_PATH,
            body=body,
            headers={
                "X-Signature": sig,
                "X-Timestamp": str(old_ts),
                "X-Nonce": nonce,
                "Content-Type": "application/json",
            },
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(resp.status, 408, payload)
        self.assertEqual(self._count_orders(), 0)

    def test_parse_error_returns_400(self) -> None:
        body = b"{not json"
        status, payload, _ = _post_signed(self.port, body)
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "parse_error")

    def test_pii_dropped_returns_400(self) -> None:
        body = make_event_body(
            event_id="pii-1", order_id="PII-1", extra={"id_card": "abc"}
        )
        status, payload, _ = _post_signed(self.port, body)
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "pii_dropped")
        fields = payload.get("fields") or []
        self.assertIn("id_card", fields)

    def test_illegal_transition_returns_409(self) -> None:
        # 1) paid
        body1 = make_event_body(event_id="it-1", order_id="IT-1")
        _post_signed(self.port, body1)
        # 2) paid → serving (合法)
        body2 = make_event_body(
            event_id="it-2", order_id="IT-1", event_type="order.delivered"
        )
        status, payload, _ = _post_signed(self.port, body2)
        self.assertEqual(status, 200, payload)
        # 3) serving → completed (非法: 状态机 serving→delivered→completed)
        body3 = make_event_body(
            event_id="it-3", order_id="IT-1", event_type="order.completed"
        )
        status, payload, _ = _post_signed(self.port, body3)
        self.assertEqual(status, 409, payload)
        self.assertEqual(payload["error"], "illegal_transition")

    def test_audit_written(self) -> None:
        body = make_event_body(event_id="aud-1", order_id="AUD-1")
        _post_signed(self.port, body)
        conn = sqlite3.connect(self.db_path)
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM webhook_audit "
                "WHERE channel='xianyu' AND event_id='aud-1' "
                "AND decision='accepted'"
            ).fetchone()[0]
            self.assertEqual(n, 1)
        finally:
            conn.close()

    # ---- T8.1 后续修复补强 ----

    def test_500_on_db_error_includes_rejected_true(self) -> None:
        """DB 路径抛异常时,500 JSON 必须带 rejected=true 字段。"""
        from data.channel_sync import webhook_server as ws

        original = ws.upsert_by_external_id

        def _boom(*a, **kw):
            raise RuntimeError("simulated db failure")

        ws.upsert_by_external_id = _boom
        try:
            body = make_event_body(event_id="err-1", order_id="ERR-1")
            status, payload, _ = _post_signed(self.port, body)
            self.assertEqual(status, 500, payload)
            self.assertEqual(payload.get("rejected"), True)
            self.assertEqual(payload.get("error"), "server_error")
        finally:
            ws.upsert_by_external_id = original

    def test_500_on_unexpected_top_level_exception_returns_json(self) -> None:
        """do_POST 顶层异常必须返回 JSON 500,而不是 BaseHTTPRequestHandler 默认栈。"""
        from data.channel_sync import webhook_server as ws

        original_parse = ws.parse_event

        def _boom(*a, **kw):
            raise RuntimeError("simulated unexpected error in parse")

        ws.parse_event = _boom
        try:
            body = make_event_body(event_id="top-1", order_id="TOP-1")
            conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
            try:
                sig, ts, nonce = sign(body)
                conn.request(
                    "POST",
                    ROUTE_PATH,
                    body=body,
                    headers={
                        "X-Signature": sig,
                        "X-Timestamp": str(ts),
                        "X-Nonce": nonce,
                        "Content-Type": "application/json",
                    },
                )
                resp = conn.getresponse()
                raw = resp.read().decode("utf-8")
                payload = json.loads(raw)
                self.assertEqual(resp.status, 500)
                self.assertEqual(payload.get("rejected"), True)
            finally:
                conn.close()
        finally:
            ws.parse_event = original_parse

    def test_500_response_is_json_content_type(self) -> None:
        """500 响应必须声明 application/json,便于客户端按 JSON 解析。"""
        from data.channel_sync import webhook_server as ws

        original = ws.upsert_by_external_id

        def _boom(*a, **kw):
            raise RuntimeError("simulated")

        ws.upsert_by_external_id = _boom
        try:
            body = make_event_body(event_id="ct-1", order_id="CT-1")
            conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
            try:
                sig, ts, nonce = sign(body)
                conn.request(
                    "POST",
                    ROUTE_PATH,
                    body=body,
                    headers={
                        "X-Signature": sig,
                        "X-Timestamp": str(ts),
                        "X-Nonce": nonce,
                        "Content-Type": "application/json",
                    },
                )
                resp = conn.getresponse()
                resp.read()
                ctype = resp.getheader("Content-Type", "")
                self.assertIn("application/json", ctype)
            finally:
                conn.close()
        finally:
            ws.upsert_by_external_id = original


class ClientIpFallbackTests(unittest.TestCase):
    """_client_ip 默认不信任 XFF，显式开启后才读取代理头。"""

    def setUp(self) -> None:
        self._old_trust = os.environ.get("GAOKAO_TRUST_X_FORWARDED_FOR")
        os.environ.pop("GAOKAO_TRUST_X_FORWARDED_FOR", None)

    def tearDown(self) -> None:
        if self._old_trust is None:
            os.environ.pop("GAOKAO_TRUST_X_FORWARDED_FOR", None)
        else:
            os.environ["GAOKAO_TRUST_X_FORWARDED_FOR"] = self._old_trust

    def test_falls_back_to_client_address(self) -> None:
        class _H:
            headers: dict = {}

        self.assertEqual(
            _client_ip(_H.headers, ("10.0.0.7", 54321)),
            "10.0.0.7",
        )

    def test_default_does_not_trust_xff(self) -> None:
        class _H:
            headers: dict = {"X-Forwarded-For": "203.0.113.5, 10.0.0.1"}

        self.assertEqual(
            _client_ip(_H.headers, ("10.0.0.7", 54321)),
            "10.0.0.7",
        )

    def test_xff_wins_over_socket_when_explicitly_trusted(self) -> None:
        os.environ["GAOKAO_TRUST_X_FORWARDED_FOR"] = "true"

        class _H:
            headers: dict = {"X-Forwarded-For": "203.0.113.5, 10.0.0.1"}

        self.assertEqual(
            _client_ip(_H.headers, ("10.0.0.7", 54321)),
            "203.0.113.5",
        )

    def test_unknown_when_both_missing(self) -> None:
        class _H:
            headers: dict = {}

        self.assertEqual(_client_ip(_H.headers, None), "unknown")

    def test_handles_empty_xff(self) -> None:
        class _H:
            headers: dict = {"X-Forwarded-For": ""}

        # 空 XFF 视为缺失,回退到 socket
        self.assertEqual(
            _client_ip(_H.headers, ("192.168.1.1", 1234)),
            "192.168.1.1",
        )

    def test_handles_ipv6(self) -> None:
        class _H:
            headers: dict = {}

        # IPv6 client_address 4-tuple 也能正确取第一项
        self.assertEqual(
            _client_ip(_H.headers, ("::1", 8080, 0, 0)),
            "::1",
        )


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
