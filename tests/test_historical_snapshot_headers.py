"""P2-6: 所有历史评审/任务板/整改报告必须显式标注
“历史快照 + 当前真相源跳转”。

防漂移: 任何新增的 2026-06-XX review/remediation/audit 报告
都必须在文件前 30 行同时出现
- “历史快照”
- ``docs/CURRENT_STATE.md``
- ``ACTIVE_EXECUTION_BOARD`` 或 ``ACTIVE_REMEDIATION``
否则 CI/未来的 reviewer 会再次把它当 current truth 用。
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
REPORTS_DIR = REPO_ROOT / "reports"
ARCHIVE_2026_06_DIR = DOCS_DIR / "archive" / "2026-06-historical-snapshots"


# 每个“历史快照”文档必须满足:
# 1) 标题或前 30 行出现“历史快照”关键字
# 2) 前 30 行内出现对 CURRENT_STATE 的引用,或对 ACTIVE_REMEDIATION / ACTIVE_EXECUTION_BOARD 的引用
_REQUIRED_SNAPSHOT_HINTS = ("历史快照",)
_REQUIRED_POINTERS = (
    "CURRENT_STATE",
    "ACTIVE_REMEDIATION",
    "ACTIVE_EXECUTION_BOARD",
)


def _is_historical_snapshot_doc(path: Path) -> bool:
    """仅对历史评审/任务板类文档做快照头注校验。

    标题或首行明显表明该文档是历史快照的,
    我们才去校验它是否带真相源指针。
    """
    if not path.exists() or path.suffix != ".md":
        return False
    head = path.read_text(encoding="utf-8", errors="ignore")[:2000]
    if "历史快照" not in head:
        return False
    # 仅在文档标题/首行/2 段内同时出现 “历史快照” 才校验。
    # 普通 docs/ 设计文档不强制。
    return True


def _missing_pointers(head: str) -> list[str]:
    return [
        token
        for token in _REQUIRED_POINTERS
        if token not in head
    ]


def test_historical_audit_reports_have_snapshot_header():
    target = ARCHIVE_2026_06_DIR / "AUDIT_REPORT_2026-06-11.md"
    assert target.exists(), target
    head = target.read_text(encoding="utf-8")
    assert "历史快照" in head
    missing = _missing_pointers(head)
    assert not missing, (
        f"{target.name} 缺少真相源指针: {missing}"
    )


def test_historical_remediation_boards_have_snapshot_header():
    target = ARCHIVE_2026_06_DIR / "REMEDIATION_TASK_BOARD_2026-06-11.md"
    assert target.exists(), target
    head = target.read_text(encoding="utf-8")
    assert "历史快照" in head
    missing = _missing_pointers(head)
    assert not missing, (
        f"{target.name} 缺少真相源指针: {missing}"
    )


def test_historical_final_completion_report_has_snapshot_header():
    target = ARCHIVE_2026_06_DIR / "FINAL_COMPLETION_REPORT_2026-06-13.md"
    assert target.exists(), target
    head = target.read_text(encoding="utf-8")
    assert "历史快照" in head
    missing = _missing_pointers(head)
    assert not missing, (
        f"{target.name} 缺少真相源指针: {missing}"
    )


def test_historical_review_reports_have_snapshot_header():
    candidates = [
        REPORTS_DIR / "PROJECT_SYSTEM_REVIEW_2026-06-13.md",
        REPORTS_DIR / "PROJECT_SYSTEM_REVIEW_2026-06-14.md",
        REPORTS_DIR / "PRODUCT_PLANNING_TECH_ALIGNMENT_REVIEW_2026-06-13.md",
    ]
    for target in candidates:
        if not target.exists():
            continue
        head = target.read_text(encoding="utf-8")
        assert "历史快照" in head, f"{target.name} 缺少历史快照头注"
        missing = _missing_pointers(head)
        assert not missing, (
            f"{target.name} 缺少真相源指针: {missing}"
        )


def test_any_new_2026_snapshot_doc_with_historical_marker_carries_pointers():
    """通用规则: 任何带“历史快照”关键字的 docs/ 文档
    (除了 CURRENT_STATE / ACTIVE_* 等当前活跃板)
    都必须至少含 1 个真相源指针。

    这条规则允许未来新增历史文档, 但一旦忘了写指针,
    本测试会立刻失败。
    """
    active_names = {
        "CURRENT_STATE.md",
        "ACTIVE_REMEDIATION_2026-06-13.md",
        "ACTIVE_EXECUTION_BOARD_2026-06-13.md",
        "P0_P1_P2_REMEDIATION_PLAN_2026-06-14.md",
    }
    for path in DOCS_DIR.glob("*.md"):
        if path.name in active_names:
            continue
        if not _is_historical_snapshot_doc(path):
            continue
        head = path.read_text(encoding="utf-8")[:4000]
        if not _missing_pointers(head):
            continue
        # 历史快照类文档必须带至少 1 个真相源指针。
        assert any(token in head for token in _REQUIRED_POINTERS), (
            f"{path.name} 是历史快照, 但缺少对当前真相源的指针"
        )
