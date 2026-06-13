"""gaokao-audit 审核报告生成器。"""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Callable
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .audit_service import AuditResult, AuditService


def _load_weasyprint_html():
    return import_module("weasyprint").HTML


class ReportGenerator:
    """将 AuditResult 渲染为 HTML / PDF 报告。"""

    def __init__(
        self,
        *,
        audit_service: AuditService | None = None,
        template_name: str = "audit_report.html",
        now_text: Callable[[], str] | None = None,
        report_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.audit_service = audit_service or AuditService()
        self.template_name = template_name
        self.now_text = now_text or (lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.report_id_factory = report_id_factory or self._default_report_id
        self.template_dir = Path(__file__).resolve().parent.parent / "templates"
        self._environment = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_html(
        self,
        result: AuditResult,
        *,
        audit_time: str | None = None,
        report_id: str | None = None,
    ) -> str:
        payload = self.build_payload(result, audit_time=audit_time, report_id=report_id)
        template = self._environment.get_template(self.template_name)
        return template.render(**payload)

    def generate_html(
        self,
        result: AuditResult,
        output_path: str,
        *,
        audit_time: str | None = None,
        report_id: str | None = None,
    ) -> str:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            self.render_html(result, audit_time=audit_time, report_id=report_id),
            encoding="utf-8",
        )
        return str(target)

    def generate_pdf(
        self,
        result: AuditResult,
        output_path: str,
        *,
        audit_time: str | None = None,
        report_id: str | None = None,
    ) -> str:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        html = self.render_html(result, audit_time=audit_time, report_id=report_id)
        html_cls = _load_weasyprint_html()
        html_cls(string=html, base_url=str(self.template_dir)).write_pdf(str(target))
        return str(target)

    def build_payload(
        self,
        result: AuditResult,
        *,
        audit_time: str | None = None,
        report_id: str | None = None,
    ) -> dict:
        return self.audit_service.build_report_payload(
            result,
            audit_time=audit_time or self.now_text(),
            report_id=report_id or self.report_id_factory(),
        )

    def _default_report_id(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"AUDIT-{stamp}-{uuid4().hex[:6].upper()}"
