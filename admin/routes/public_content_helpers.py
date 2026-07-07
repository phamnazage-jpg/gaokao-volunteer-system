"""Shared helpers for public content/data pages."""

from __future__ import annotations

from html import escape


def render_trust_banner_html(
    *,
    province: str,
    official_source: str,
    last_updated: str,
    scope: str,
    confidence_label: str,
    boundary_note: str,
) -> str:
    return (
        '<div class="trust-banner">'
        f'<p class="meta">可信度说明：官方来源：{escape(official_source)} · 更新时间：{escape(last_updated or "未公布")}</p>'
        f'<p class="meta">适用范围：{escape(scope)} · 适用省份：{escape(province)} · 置信等级：{escape(confidence_label)}</p>'
        f'<p class="meta">{escape(boundary_note)}</p>'
        "</div>"
    )


def public_supported_provinces() -> set[str]:
    return {
        "北京",
        "天津",
        "上海",
        "重庆",
        "河北",
        "河南",
        "山东",
        "山西",
        "陕西",
        "辽宁",
        "吉林",
        "黑龙江",
        "江苏",
        "浙江",
        "安徽",
        "福建",
        "江西",
        "湖北",
        "湖南",
        "广东",
        "海南",
        "四川",
        "贵州",
        "云南",
        "甘肃",
        "青海",
        "新疆",
    }


