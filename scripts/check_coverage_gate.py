#!/usr/bin/env python3
"""Fail CI when coverage gates are not met.

Single source of truth for the coverage gate.
CI workflow, dev-verify, and codecov all read this file (or
the same OVERALL_MIN / CORE_MIN constants) so the gate no
longer diverges across surfaces.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Mirrors `tests/test_coverage_gate_core.py` thresholds.
OVERALL_MIN = 0.80
CORE_MIN = 1.00
CORE_FILES = (
    "skills/gaokao-spec-checker/scripts/spec_checker_v2.py",
    "skills/gaokao-college-advisor/scripts/gaokao_visual_report.py",
)
CORE_FILE_KEYS = tuple(
    path.removeprefix("skills/")
    for path in CORE_FILES
)
IGNORED_PATH_PREFIXES = (
    "tests/",
    "admin/tests/",
    "docs/",
)
IGNORED_PATH_PARTS = (
    "/tests/",
    "/docs/plans/",
    "/fixtures/",
)
PATH_PREFIXES_TO_TRIM = (
    "skills/",
)


def _normalize_path(filename: str) -> str:
    normalized = filename.replace("\\", "/")
    for prefix in PATH_PREFIXES_TO_TRIM:
        if normalized.startswith(prefix):
            return normalized[len(prefix) :]
    return normalized


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def _should_ignore(filename: str) -> bool:
    normalized = _normalize_path(filename)
    if normalized.startswith(IGNORED_PATH_PREFIXES):
        return True
    return any(part in normalized for part in IGNORED_PATH_PARTS)


def _line_count(cls: ET.Element) -> int:
    return len(cls.findall("./lines/line"))


def main(argv: list[str]) -> int:
    coverage_path = Path(argv[1]) if len(argv) > 1 else Path("coverage.xml")
    if not coverage_path.exists():
        print(f"coverage gate failed: missing file {coverage_path}", file=sys.stderr)
        return 2

    root = ET.parse(coverage_path).getroot()
    classes = root.findall(".//class")
    application_classes = [
        cls for cls in classes if not _should_ignore(cls.attrib.get("filename", ""))
    ]
    if not application_classes:
        print("coverage gate failed: no application coverage entries", file=sys.stderr)
        return 2

    class_by_filename = {
        _normalize_path(cls.attrib.get("filename", "")): float(cls.attrib["line-rate"])
        for cls in application_classes
    }
    lines_by_filename = {
        _normalize_path(cls.attrib.get("filename", "")): _line_count(cls)
        for cls in application_classes
    }

    total_lines = sum(lines_by_filename.values())
    covered_lines = sum(
        class_by_filename[name] * lines_by_filename[name]
        for name in class_by_filename
    )
    overall = covered_lines / total_lines if total_lines else 0.0

    missing = [name for name in CORE_FILE_KEYS if name not in class_by_filename]
    if missing:
        print("coverage gate failed: missing core coverage entries:", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        return 2

    core_lines = 0
    core_covered_lines = 0.0
    for name in CORE_FILE_KEYS:
        line_count = lines_by_filename[name]
        core_lines += line_count
        core_covered_lines += class_by_filename[name] * line_count

    core = core_covered_lines / core_lines if core_lines else 0.0

    failures: list[str] = []
    if overall < OVERALL_MIN:
        failures.append(
            f"overall coverage {_format_percent(overall)} < required {_format_percent(OVERALL_MIN)}"
        )
    if core < CORE_MIN:
        failures.append(
            f"core coverage {_format_percent(core)} < required {_format_percent(CORE_MIN)}"
        )

    print(
        "coverage gate summary: "
        f"overall={_format_percent(overall)}, core={_format_percent(core)}"
    )
    if failures:
        print("coverage gate failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
