"""gaokao-audit 命令行入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .audit_service import AuditService
from .report_generator import ReportGenerator

_ALLOWED_FORMATS = ("text", "pdf_text", "screenshot_ocr")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI 志愿方案审核工具")
    parser.add_argument("input", help="方案文件路径")
    parser.add_argument(
        "-o",
        "--output",
        help="PDF 输出路径，默认与输入文件同目录同名 .pdf",
    )
    parser.add_argument(
        "-f",
        "--format",
        default="text",
        choices=_ALLOWED_FORMATS,
        help="输入格式",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="额外输出审核结果 JSON",
    )
    return parser


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}.audit.pdf")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    input_path = Path(args.input).expanduser().resolve()

    if not input_path.exists() or not input_path.is_file():
        print(f"❌ 文件不存在: {input_path}", file=sys.stderr)
        return 1

    plan_text = input_path.read_text(encoding="utf-8")
    audit_service = AuditService()
    result = audit_service.audit(plan_text, format=args.format)

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else default_output_path(input_path)
    )
    pdf_path = ReportGenerator(audit_service=audit_service).generate_pdf(
        result,
        str(output_path),
    )

    print(f"输入文件: {input_path}")
    print(f"省份: {result.province or '未识别'}")
    print(f"综合评分: {result.overall_score}/100")
    print(f"PDF报告: {pdf_path}")

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
