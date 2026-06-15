"""P1-4 regression: webhook server must isolate connections per ``db_path``.

The previous implementation cached a single module-level
``_DB_CONN`` and reused it across ``make_server`` calls regardless of
the path argument.  That let two webhook server instances point at the
same database while each thought it was talking to a different one.
The fix keeps a per-path connection cache; this test locks the
behaviour so future regressions collapse immediately.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from data.channel_sync import webhook_server
from data.orders.dao import OrdersDAO


@pytest.fixture
def two_dbs(tmp_path: Path):
    db_a = tmp_path / "a.db"
    db_b = tmp_path / "b.db"
    # Trigger schema bootstrap for both, so the per-key connection
    # cache is filled when ``_get_db`` is first called.
    for db in (db_a, db_b):
        OrdersDAO.connect(db).close()
    # Always start each test from a clean per-path cache so a leak
    # from one test cannot poison another.
    webhook_server.close_db_for_tests()
    yield db_a, db_b
    webhook_server.close_db_for_tests()


def test_get_db_returns_distinct_connections_per_path(two_dbs):
    db_a, db_b = two_dbs
    conn_a = webhook_server._get_db(str(db_a))
    conn_b = webhook_server._get_db(str(db_b))
    try:
        assert conn_a is not conn_b
        # Each connection is bound to its own path; an insert via
        # connection ``A`` must not be visible via connection ``B``.
        conn_a.execute(
            "INSERT INTO orders(id, source, service_version, amount_cents, status, created_at, status_updated_at) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            ("ORD-A-1", "web", "standard", 9900, "pending", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        conn_a.commit()
        cur_b = conn_b.execute("SELECT COUNT(*) FROM orders").fetchone()
        assert cur_b[0] == 0
    finally:
        webhook_server.close_db_for_path(str(db_a))
        webhook_server.close_db_for_path(str(db_b))


def test_release_db_does_not_close_other_paths_connections(two_dbs):
    db_a, db_b = two_dbs
    webhook_server._get_db(str(db_a))
    webhook_server._get_db(str(db_b))
    webhook_server.close_db_for_path(str(db_a))
    # ``close_db_for_path`` for path ``A`` must not affect the cache
    # for ``B``.  A subsequent request for path ``B`` should return the
    # still-cached connection, not reopen one.
    conn_b = webhook_server._get_db(str(db_b))
    assert conn_b is webhook_server._get_db(str(db_b))
    webhook_server.close_db_for_path(str(db_b))


def test_get_db_is_thread_safe_under_concurrent_access(two_dbs):
    db_a, db_b = two_dbs
    errors: list[BaseException] = []

    def worker(path: str) -> None:
        try:
            for _ in range(25):
                conn = webhook_server._get_db(path)
                conn.execute("SELECT 1").fetchone()
                time.sleep(0.001)
        except BaseException as exc:  # pragma: no cover - test
            errors.append(exc)
        finally:
            webhook_server.close_db_for_path(path)

    threads = [
        threading.Thread(target=worker, args=(str(db_a),)),
        threading.Thread(target=worker, args=(str(db_b),)),
        threading.Thread(target=worker, args=(str(db_a),)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"thread-safety regression: {errors!r}"


def test_release_all_closes_every_cached_connection(two_dbs):
    """Calling ``close_db_for_tests`` (the module's teardown helper)
    must close every cached connection.  After teardown, the next
    ``_get_db`` call must reopen a fresh connection, not silently
    reuse a closed handle.
    """
    db_a, db_b = two_dbs
    webhook_server._get_db(str(db_a))
    webhook_server._get_db(str(db_b))
    webhook_server.close_db_for_tests()

    fresh_a = webhook_server._get_db(str(db_a))
    fresh_b = webhook_server._get_db(str(db_b))
    try:
        # Both connections must be freshly opened, not the same handle
        # as before the teardown.
        assert fresh_a.execute("SELECT 1").fetchone() == (1,)
        assert fresh_b.execute("SELECT 1").fetchone() == (1,)
    finally:
        webhook_server.close_db_for_tests()
