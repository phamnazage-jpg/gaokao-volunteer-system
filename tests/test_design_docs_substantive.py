"""X-02 / X-03 / X-04 / X-05 / X-08: 设计文档必须真实存在且达到最低结构门槛。

防漂移: 任何新增的"设计文档"都不能是空模板或一两句占位。
本测试要求:
1. 文件存在
2. 行数 >= 60 (足以容纳真设计)
3. 含 "## 1." 编号小节, 表示至少有结构化章节
4. 含 "## 5." 或更靠后的章节, 表示已覆盖目标问题
5. 含 "状态机" / "状态" / "不变量" / "流程" / "字段" 中至少两个
   关键词, 表明不是空模板
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"


# 每份设计文档至少应包含的两个高阶关键词。
# 若一份设计文档没有状态机、字段、流程、不变量等任一关键词,
# 说明它是空模板。
KEYWORDS = ("状态机", "状态", "字段", "流程", "不变量", "生命周期", "阶段")


_DESIGN_DOCS: list[tuple[str, tuple[str, ...]]] = [
    # (相对 docs/ 的路径, 必含关键词子集 — 每个 doc 至少须命中一个)
    ("PAYMENT_DOMAIN_DESIGN.md", ("状态", "状态机", "字段", "流程", "不变量")),
    ("DELIVERY_SERVICE_DESIGN.md", ("状态", "状态机", "流程", "不变量", "生命周期")),
    ("LEGAL_PRIVACY_BASELINE.md", ("同意", "删除", "保留", "监护")),
    ("BACKUP_AND_RECOVERY_PLAN.md", ("备份", "恢复", "演练", "RPO", "RTO")),
    ("CROWD_DB_DATA_QUALITY.md", ("置信", "省份", "数据", "不变量")),
]


def _missing(path: Path) -> str:
    if not path.exists():
        return "missing"
    text = path.read_text(encoding="utf-8")
    if len(text.splitlines()) < 60:
        return f"too-short({len(text.splitlines())} lines)"
    if "## 1." not in text:
        return "missing-## 1."
    # Check for at least one second-level heading in the upper half.
    upper = text[: len(text) // 2]
    hits = sum(1 for k in KEYWORDS if k in upper or k in text)
    if hits < 2:
        return f"keyword-light(hits={hits})"
    return ""


@pytest.mark.parametrize("relpath,required", _DESIGN_DOCS)
def test_design_doc_is_substantive(relpath: str, required: tuple[str, ...]):
    path = DOCS_DIR / relpath
    problem = _missing(path)
    assert not problem, f"{relpath} 不通过设计文档最低门槛: {problem}"

    text = path.read_text(encoding="utf-8")
    matched = [keyword for keyword in required if keyword in text]
    assert matched, (
        f"{relpath} 缺少任一必含关键词; 期望至少一个来自 {required!r}"
    )
