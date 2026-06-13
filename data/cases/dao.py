"""T6.5 案例管理 DAO。"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Iterator, cast

from admin.db import get_connection, utc_now_iso
from data.cases.models import CaseCategory, CaseRecord, CaseReviewStatus


class CaseNotFound(LookupError):
    """案例不存在。"""


class CasesDAO:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @classmethod
    @contextmanager
    def connect(cls, db_path: str) -> Iterator["CasesDAO"]:
        conn = get_connection(db_path)
        try:
            yield cls(conn)
        finally:
            conn.close()

    def list(
        self,
        *,
        category: str | None = None,
        review_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CaseRecord], int]:
        where = []
        params: list[object] = []
        if category is not None:
            where.append("category = ?")
            params.append(category)
        if review_status is not None:
            where.append("review_status = ?")
            params.append(review_status)
        where_sql = f" WHERE {' AND '.join(where)}" if where else ""

        total_row = self.conn.execute(
            f"SELECT COUNT(*) AS n FROM cases{where_sql}", params
        ).fetchone()
        rows = self.conn.execute(
            f"SELECT * FROM cases{where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
        total = int(total_row["n"] if total_row is not None else 0)
        return [self._from_row(row) for row in rows], total

    def get(self, case_id: int) -> CaseRecord:
        row = self.conn.execute(
            "SELECT * FROM cases WHERE id = ?", (case_id,)
        ).fetchone()
        if row is None:
            raise CaseNotFound(case_id)
        return self._from_row(row)

    def create(self, record: CaseRecord) -> CaseRecord:
        now = utc_now_iso()
        cur = self.conn.execute(
            """
            INSERT INTO cases(
                title, category, summary, content,
                review_status, review_note, reviewer, reviewed_at,
                created_at, updated_at, tags
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.title,
                record.category,
                record.summary,
                record.content,
                record.review_status,
                record.review_note,
                record.reviewer,
                record.reviewed_at,
                now,
                now,
                json.dumps(record.tags, ensure_ascii=False),
            ),
        )
        case_id = int(cur.lastrowid or 0)
        return self.get(case_id)

    def update(self, case_id: int, *, updates: dict[str, object]) -> CaseRecord:
        existing = self.get(case_id)
        merged = CaseRecord(
            id=existing.id,
            title=cast(str, updates.get("title", existing.title)),
            category=cast(CaseCategory, updates.get("category", existing.category)),
            summary=cast(str | None, updates.get("summary", existing.summary)),
            content=cast(str | None, updates.get("content", existing.content)),
            review_status=cast(
                CaseReviewStatus,
                updates.get("review_status", existing.review_status),
            ),
            review_note=cast(
                str | None, updates.get("review_note", existing.review_note)
            ),
            reviewer=cast(str | None, updates.get("reviewer", existing.reviewer)),
            reviewed_at=cast(
                str | None, updates.get("reviewed_at", existing.reviewed_at)
            ),
            created_at=existing.created_at,
            updated_at=utc_now_iso(),
            tags=cast(list[str], updates.get("tags", existing.tags)),
        )
        self.conn.execute(
            """
            UPDATE cases
            SET title = ?, category = ?, summary = ?, content = ?,
                review_status = ?, review_note = ?, reviewer = ?, reviewed_at = ?,
                updated_at = ?, tags = ?
            WHERE id = ?
            """,
            (
                merged.title,
                merged.category,
                merged.summary,
                merged.content,
                merged.review_status,
                merged.review_note,
                merged.reviewer,
                merged.reviewed_at,
                merged.updated_at,
                json.dumps(merged.tags, ensure_ascii=False),
                case_id,
            ),
        )
        return self.get(case_id)

    def delete(self, case_id: int) -> None:
        cur = self.conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
        if cur.rowcount == 0:
            raise CaseNotFound(case_id)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> CaseRecord:
        tags_raw = row["tags"] or "[]"
        tags = json.loads(tags_raw)
        if not isinstance(tags, list):
            tags = []
        return CaseRecord(
            id=int(row["id"]),
            title=row["title"],
            category=row["category"],
            summary=row["summary"],
            content=row["content"],
            review_status=row["review_status"],
            review_note=row["review_note"],
            reviewer=row["reviewer"],
            reviewed_at=row["reviewed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            tags=[str(item) for item in tags],
        )
