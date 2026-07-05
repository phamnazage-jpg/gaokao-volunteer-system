"""schema 模块测试"""

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("GAOKAO_ORDERS_FERNET_KEY", "test-secret-for-unit-tests")

from data.orders.schema import apply_schema, get_schema_version, SCHEMA_SQL
from data.orders.intake_schema import IntakePayload


@pytest.fixture
def tmp_db():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d) / "test_orders.db"


def test_apply_schema_creates_orders_table(tmp_db):
    conn = apply_schema(tmp_db)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
        ).fetchone()
        assert row is not None
    finally:
        conn.close()


def test_apply_schema_creates_status_history_table(tmp_db):
    conn = apply_schema(tmp_db)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='order_status_history'"
        ).fetchone()
        assert row is not None
    finally:
        conn.close()


def test_apply_schema_enables_foreign_keys(tmp_db):
    conn = apply_schema(tmp_db)
    try:
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1
    finally:
        conn.close()


def test_apply_schema_is_idempotent(tmp_db):
    """重复执行 apply_schema 不报错。"""
    conn1 = apply_schema(tmp_db)
    conn1.close()
    conn2 = apply_schema(tmp_db)
    conn2.close()  # 不抛即通过


def test_apply_schema_creates_indexes(tmp_db):
    conn = apply_schema(tmp_db)
    try:
        idxs = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        ).fetchall()
        idx_names = {i[0] for i in idxs}
        assert "idx_orders_status" in idx_names
        assert "idx_orders_source" in idx_names
        assert "idx_orders_created_at" in idx_names
        assert "idx_orders_phone_hash" in idx_names
        assert "idx_status_history_order" in idx_names
    finally:
        conn.close()


def test_apply_schema_creates_parent_dir(tmp_db):
    """父目录不存在时自动创建。"""
    nested = tmp_db.parent / "subdir1" / "subdir2" / "nested.db"
    assert not nested.parent.exists()
    conn = apply_schema(nested)
    conn.close()
    assert nested.exists()


def test_check_constraint_rejects_invalid_status(tmp_db):
    """CHECK 约束拒绝非法 status 字符串。"""
    conn = apply_schema(tmp_db)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO orders
                   (id, source, service_version, amount_cents, status,
                    status_updated_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    "X1",
                    "web",
                    "basic",
                    100,
                    "INVALID_STATUS",
                    "2026-06-12T10:00:00+00:00",
                    "2026-06-12T10:00:00+00:00",
                ),
            )
    finally:
        conn.close()


def test_check_constraint_rejects_negative_amount(tmp_db):
    """CHECK 约束拒绝负金额。"""
    conn = apply_schema(tmp_db)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO orders
                   (id, source, service_version, amount_cents, status,
                    status_updated_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    "X2",
                    "web",
                    "basic",
                    -1,
                    "pending",
                    "2026-06-12T10:00:00+00:00",
                    "2026-06-12T10:00:00+00:00",
                ),
            )
    finally:
        conn.close()


def test_unique_external_id_per_source(tmp_db):
    """(source, external_id) 组合唯一。"""
    conn = apply_schema(tmp_db)
    try:
        conn.execute(
            """INSERT INTO orders
               (id, source, external_id, service_version, amount_cents, status,
                status_updated_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "A1",
                "xianyu",
                "EXT-001",
                "basic",
                100,
                "pending",
                "2026-06-12T10:00:00+00:00",
                "2026-06-12T10:00:00+00:00",
            ),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO orders
                   (id, source, external_id, service_version, amount_cents, status,
                    status_updated_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "A2",
                    "xianyu",
                    "EXT-001",
                    "basic",
                    100,
                    "pending",
                    "2026-06-12T10:00:00+00:00",
                    "2026-06-12T10:00:00+00:00",
                ),
            )
        # 不同 source 可同 external_id
        conn.execute(
            """INSERT INTO orders
               (id, source, external_id, service_version, amount_cents, status,
                status_updated_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "A3",
                "wechat",
                "EXT-001",
                "basic",
                100,
                "pending",
                "2026-06-12T10:00:00+00:00",
                "2026-06-12T10:00:00+00:00",
            ),
        )
    finally:
        conn.close()


def test_status_history_cascade_delete(tmp_db):
    """删除订单时状态历史级联删除。"""
    conn = apply_schema(tmp_db)
    try:
        conn.execute(
            """INSERT INTO orders
               (id, source, service_version, amount_cents, status,
                status_updated_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                "B1",
                "web",
                "basic",
                100,
                "pending",
                "2026-06-12T10:00:00+00:00",
                "2026-06-12T10:00:00+00:00",
            ),
        )
        conn.execute(
            """INSERT INTO order_status_history
               (order_id, from_status, to_status, actor, changed_at)
               VALUES (?, ?, ?, ?, ?)""",
            ("B1", None, "pending", "system", "2026-06-12T10:00:00+00:00"),
        )
        conn.commit()
        # 验证存在
        count = conn.execute(
            "SELECT COUNT(*) FROM order_status_history WHERE order_id = ?", ("B1",)
        ).fetchone()[0]
        assert count == 1
        # 删除订单
        conn.execute("DELETE FROM orders WHERE id = ?", ("B1",))
        conn.commit()
        # 级联删除
        count = conn.execute(
            "SELECT COUNT(*) FROM order_status_history WHERE order_id = ?", ("B1",)
        ).fetchone()[0]
        assert count == 0
    finally:
        conn.close()


def test_get_schema_version_returns_max_migration_after_apply(tmp_db):
    conn = apply_schema(tmp_db)
    try:
        assert get_schema_version(conn) == 4
    finally:
        conn.close()


def test_schema_migrations_table_records_all_migrations(tmp_db):
    conn = apply_schema(tmp_db)
    try:
        rows = conn.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version"
        ).fetchall()
        assert len(rows) == 4
        assert rows[0] == (1, "initial_schema")
        assert rows[-1] == (4, "add_portal_token_revocations")
    finally:
        conn.close()


def test_old_database_without_migrations_table_is_auto_upgraded(tmp_db):
    """Simulate a pre-T3-04 database that has a full orders table
    (created by an older version of apply_schema) but no schema_migrations table.
    apply_schema should detect it, create schema_migrations, and register all migrations."""
    import sqlite3
    from data.orders.schema import SCHEMA_SQL

    # Apply the base schema (creates orders + all indexes) but NOT schema_migrations
    # by executing only the pre-T3-04 portion of SCHEMA_SQL.
    conn = sqlite3.connect(str(tmp_db))
    conn.execute("PRAGMA foreign_keys = ON")
    old_schema = SCHEMA_SQL.split("CREATE TABLE IF NOT EXISTS schema_migrations")[0]
    conn.executescript(old_schema)
    conn.commit()
    conn.close()

    # Verify no schema_migrations table exists yet
    conn = sqlite3.connect(str(tmp_db))
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
    ).fetchone()
    assert row is None
    conn.close()

    # Now apply_schema should auto-upgrade: create schema_migrations and register all migrations
    conn = apply_schema(tmp_db)
    try:
        assert get_schema_version(conn) == 4
        rows = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()
        assert rows[0] == 4
    finally:
        conn.close()


def test_schema_sql_is_nonempty():
    assert "CREATE TABLE IF NOT EXISTS orders" in SCHEMA_SQL
    assert "CREATE TABLE IF NOT EXISTS order_status_history" in SCHEMA_SQL
    assert "CREATE TABLE IF NOT EXISTS portal_token_revocations" in SCHEMA_SQL


def test_portal_token_revocation_table_exists_after_apply(tmp_db):
    conn = apply_schema(tmp_db)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='portal_token_revocations'"
        ).fetchone()
        assert row is not None
    finally:
        conn.close()


def test_intake_payload_submit_accepts_minimal_step1_payload(tmp_db):
    payload = IntakePayload.model_validate(
        {
            "mode": "submit",
            "candidate_province": "湖南",
            "candidate_subjects": ["物理", "化学", "生物"],
            "candidate_score": 578,
            "candidate_rank": 12345,
            "consent_version": "portal-v1",
            "consent_scope": "step1",
            "privacy_accepted": True,
            "service_terms_accepted": True,
            "guardian_confirmed": True,
        }
    )

    assert payload.candidate_province == "湖南"
    assert payload.candidate_subjects == ["物理", "化学", "生物"]
    assert payload.candidate_score == 578
    assert payload.candidate_rank == 12345
