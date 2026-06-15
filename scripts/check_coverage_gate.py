#!/usr/bin/env python3
"""Fail CI when coverage gates are not met."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

OVERALL_MIN = 0.80
CORE_MIN = 1.00
CORE_FILES = (
    "skills/gaokao-spec-checker/scripts/spec_checker_v2.py",
    "skills/gaokao-college-advisor/scripts/gaokao_visual_report.py",
)


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def main(argv: list[str]) -> int:
    coverage_path = Path(argv[1]) if len(argv) > 1 else Path("coverage.xml")
    if not coverage_path.exists():
        print(f"coverage gate failed: missing file {coverage_path}", file=sys.stderr)
        return 2

    root = ET.parse(coverage_path).getroot()
    overall = float(root.attrib["line-rate"])

    classes = root.findall(".//class")
    class_by_filename = {
        cls.attrib.get("filename", ""): float(cls.attrib["line-rate"])
        for cls in classes
    }
    lines_by_filename = {
        cls.attrib.get("filename", ""): len(cls.findall("./lines/line"))
        for cls in classes
    }

    missing = [name for name in CORE_FILES if name not in class_by_filename]
    if missing:
        print("coverage gate failed: missing core coverage entries:", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        return 2

    covered_lines = 0.0
    total_lines = 0
    for name in CORE_FILES:
        line_count = lines_by_filename[name]
        total_lines += line_count
        covered_lines += class_by_filename[name] * line_count

    core = covered_lines / total_lines if total_lines else 0.0

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
