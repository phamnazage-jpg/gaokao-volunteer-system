"""T7.5 分享页 WebUI 纯函数与默认文件加载器。"""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path
from typing import Any, Iterable, Optional

from data.share.short_link import (
    STATUS_EXPIRED,
    STATUS_NOT_FOUND,
    STATUS_PASSWORD_REQUIRED,
    STATUS_PASSWORD_WRONG,
    STATUS_REVOKED,
)

_STATUS_META = {
    STATUS_NOT_FOUND: (404, "分享链接不存在", "请确认链接是否完整，或联系龙老师重新生成。"),
    STATUS_REVOKED: (410, "分享已撤销", "该分享链接已被撤销，无法继续访问。"),
    STATUS_EXPIRED: (410, "分享已过期", "该分享链接已经过期，请联系龙老师重新分享。"),
    STATUS_PASSWORD_REQUIRED: (401, "需要访问密码", "该分享页已加密，请输入访问密码继续查看。"),
    STATUS_PASSWORD_WRONG: (401, "密码错误", "密码不正确，请重新输入。"),
}


def load_report_from_directory(report_id: str, report_dir: str | Path) -> Optional[dict[str, Any]]:
    """从目录加载 ``{report_id}.json`` 报告。不存在或格式错误时返回 None。"""
    if not report_id:
        return None
    if re.fullmatch(r"[A-Za-z0-9._-]+", report_id) is None:
        return None
    if report_id.startswith(".") or ".." in report_id:
        return None
    base_dir = Path(report_dir).resolve()
    path = (base_dir / f"{report_id}.json").resolve()
    if base_dir not in path.parents:
        return None
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def status_code_for_result(result: dict[str, Any]) -> int:
    status = str(result.get("status") or "")
    if status == "ok":
        return 200
    return _STATUS_META.get(status, (400, "访问失败", "分享页当前不可用。"))[0]


def render_share_page(result: dict[str, Any], *, password: str | None = None) -> str:
    status = str(result.get("status") or "")
    if status != "ok":
        return _render_status_page(status, code=str(result.get("code") or ""), password=password)
    return _render_ok_page(result)


def _render_status_page(status: str, *, code: str, password: str | None) -> str:
    _, title, message = _STATUS_META.get(status, (400, "访问失败", "分享页当前不可用。"))
    error_block = ""
    form_block = ""
    if status == STATUS_PASSWORD_WRONG:
        error_block = '<p class="error">密码错误，请重新输入。</p>'
    if status in {STATUS_PASSWORD_REQUIRED, STATUS_PASSWORD_WRONG}:
        form_block = f"""
        <form class="password-form" method="get" action="/s/{escape(code)}">
          <label for="pwd">访问密码</label>
          <input id="pwd" name="pwd" type="password" autocomplete="current-password" placeholder="请输入访问密码" />
          <button type="submit">进入分享页</button>
        </form>
        """
    return _page_shell(
        title,
        f"""
        <section class="hero compact">
          <span class="badge badge-warn">分享访问</span>
          <h1>{escape(title)}</h1>
          <p class="lead">{escape(message)}</p>
          {error_block}
          {form_block}
        </section>
        """,
    )


def _render_ok_page(result: dict[str, Any]) -> str:
    rendered = result.get("rendered") or {}
    payload = rendered.get("payload") or {}
    policy = rendered.get("policy") or {}
    permission = str(rendered.get("permission") or payload.get("permission") or "read")

    title = _pick_first(payload, "title") or "高考志愿填报方案"
    summary = _pick_first(payload, "summary") or "微信内打开也能直接查看，支持手机端快速浏览。"
    candidate_name = _pick_first(payload, "candidate_name", "customer_name", "student_name", "name")
    score = payload.get("score")
    rank = payload.get("rank")
    province = payload.get("province")
    year = payload.get("year")
    report_id = payload.get("report_id") or result.get("report_id")
    share_url = payload.get("share_url") or result.get("url")

    info_cards = []
    if candidate_name:
        info_cards.append(_metric_card("考生", str(candidate_name)))
    if score is not None:
        info_cards.append(_metric_card("分数", str(score)))
    if rank is not None:
        info_cards.append(_metric_card("位次", _format_number(rank)))
    if province or year:
        info_cards.append(_metric_card("地区/年份", " / ".join([str(x) for x in (province, year) if x])))
    info_cards_html = "".join(info_cards) if info_cards else _metric_card("状态", "已授权查看")

    recommendations = _render_recommendations(payload.get("recommendations"))
    volunteers = _render_volunteers(payload.get("volunteers"))
    permission_hint = _permission_hint(permission, policy)

    limited_block = ""
    if permission == "read":
        limited_block = """
        <section class="panel notice">
          <h2>分享信息受限</h2>
          <p>当前链接只开放最小信息展示，完整方案需更高权限或联系龙老师。</p>
        </section>
        """

    report_meta = []
    if report_id:
        report_meta.append(f"报告ID：{escape(str(report_id))}")
    if share_url:
        report_meta.append(f"分享链接：<code>{escape(str(share_url))}</code>")
    report_meta_html = "<br />".join(report_meta) if report_meta else "公开分享页"

    copy_button = ""
    if share_url:
        copy_button = f'<button type="button" id="copy-share-btn" class="ghost" data-share-url="{escape(str(share_url))}">复制链接</button>'

    body = f"""
    <section class="hero">
      <span class="badge">龙老师 · 高考志愿填报方案</span>
      <h1>{escape(str(title))}</h1>
      <p class="lead">{escape(str(summary))}</p>
      <p class="meta">{permission_hint}</p>
      <div class="hero-actions">{copy_button}</div>
    </section>

    <section class="grid metrics">{info_cards_html}</section>

    {limited_block}

    {recommendations}
    {volunteers}

    <section class="panel footer-panel">
      <h2>分享说明</h2>
      <p>{report_meta_html}</p>
      <p class="subtle">微信内打开也能直接查看，无需额外 App。</p>
    </section>
    <script>
      (function () {{
        const copyShareButton = document.getElementById('copy-share-btn');
        if (!copyShareButton) return;
        copyShareButton.addEventListener('click', async function () {{
          const url = copyShareButton.dataset.shareUrl || '';
          try {{
            if (navigator.clipboard && navigator.clipboard.writeText) {{
              await navigator.clipboard.writeText(url);
              alert('链接已复制');
              return;
            }}
          }} catch (err) {{}}
          window.prompt('请手动复制链接', url);
        }});
      }})();
    </script>
    """
    return _page_shell(str(title), body)


def _pick_first(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return value
    return None


def _render_recommendations(items: Any) -> str:
    rows = []
    for item in _take_dicts(items, limit=3):
        school = _pick_from_item(item, "school", "name") or "院校待补充"
        major = _pick_from_item(item, "major") or "专业待补充"
        prob = _pick_from_item(item, "prob", "probability")
        prob_text = _format_probability(prob)
        rows.append(f"<li><strong>{escape(str(school))}</strong><span>{escape(str(major))}</span><em>{escape(prob_text)}</em></li>")
    if not rows:
        return ""
    return f"""
    <section class="panel">
      <h2>推荐院校 TOP3</h2>
      <ol class="list">{''.join(rows)}</ol>
    </section>
    """


def _render_volunteers(items: Any) -> str:
    rows = []
    for item in _take_dicts(items, limit=3):
        school = _pick_from_item(item, "school", "name") or "志愿待补充"
        majors = item.get("majors") if isinstance(item.get("majors"), list) else None
        if majors:
            detail = " / ".join(str(x) for x in majors[:3])
        else:
            detail = _pick_from_item(item, "major", "type") or ""
        rows.append(f"<li><strong>{escape(str(school))}</strong><span>{escape(str(detail))}</span></li>")
    if not rows:
        return ""
    return f"""
    <section class="panel">
      <h2>志愿预览</h2>
      <ul class="list volunteers">{''.join(rows)}</ul>
    </section>
    """


def _take_dicts(items: Any, *, limit: int) -> Iterable[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    out = []
    for item in items:
        if isinstance(item, dict):
            out.append(item)
        if len(out) >= limit:
            break
    return out


def _pick_from_item(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def _permission_hint(permission: str, policy: dict[str, Any]) -> str:
    labels = []
    if policy.get("can_comment"):
        labels.append("可评论")
    if policy.get("can_edit"):
        labels.append("可编辑")
    if not labels:
        labels.append("仅查看")
    return f"权限：{escape(permission)} · {' / '.join(labels)}"


def _metric_card(label: str, value: str) -> str:
    return f"""
    <article class="metric-card">
      <div class="metric-label">{escape(label)}</div>
      <div class="metric-value">{escape(value)}</div>
    </article>
    """


def _format_probability(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if num <= 1:
        num *= 100
    return f"录取概率 {num:.0f}%"


def _format_number(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def _page_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="format-detection" content="telephone=no,email=no,address=no" />
    <title>{escape(title)}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f5f7fb;
        --card: #ffffff;
        --text: #0f172a;
        --muted: #64748b;
        --line: #dbe4f0;
        --brand: #2563eb;
        --brand-soft: #eff6ff;
        --warn: #b45309;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif; }}
      .page {{ max-width: 760px; margin: 0 auto; padding: 16px; }}
      .hero, .panel, .metric-card {{ background: var(--card); border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 6px 24px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 22px 18px; margin-bottom: 14px; }}
      .hero.compact {{ text-align: center; padding: 28px 18px; }}
      .badge {{ display: inline-flex; align-items: center; padding: 6px 10px; border-radius: 999px; background: var(--brand-soft); color: var(--brand); font-size: 13px; font-weight: 600; margin-bottom: 10px; }}
      .badge-warn {{ background: #fff7ed; color: var(--warn); }}
      h1 {{ margin: 0 0 10px; font-size: 28px; line-height: 1.25; }}
      h2 {{ margin: 0 0 10px; font-size: 18px; }}
      .lead {{ margin: 0; color: var(--muted); font-size: 15px; line-height: 1.65; }}
      .meta, .subtle {{ color: var(--muted); font-size: 14px; line-height: 1.6; }}
      .hero-actions {{ margin-top: 14px; display: flex; gap: 10px; flex-wrap: wrap; }}
      .grid.metrics {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }}
      .metric-card {{ padding: 16px; }}
      .metric-label {{ font-size: 13px; color: var(--muted); margin-bottom: 8px; }}
      .metric-value {{ font-size: 24px; font-weight: 700; word-break: break-word; }}
      .panel {{ padding: 18px; margin-bottom: 14px; }}
      .panel.notice {{ border-style: dashed; background: #fcfcfd; }}
      .list {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }}
      .list li {{ display: grid; gap: 4px; padding: 12px; background: #f8fafc; border-radius: 14px; }}
      .list li strong {{ font-size: 15px; }}
      .list li span, .list li em {{ font-size: 14px; color: var(--muted); font-style: normal; }}
      .footer-panel code {{ white-space: pre-wrap; word-break: break-all; }}
      .password-form {{ margin-top: 18px; display: grid; gap: 10px; text-align: left; }}
      .password-form label {{ font-size: 14px; color: var(--muted); }}
      .password-form input {{ width: 100%; padding: 12px 14px; border: 1px solid var(--line); border-radius: 12px; font-size: 16px; }}
      button {{ border: 0; border-radius: 12px; padding: 12px 16px; background: var(--brand); color: #fff; font-size: 15px; font-weight: 600; }}
      button.ghost {{ background: #e2e8f0; color: var(--text); }}
      .error {{ color: #b91c1c; font-size: 14px; margin-top: 10px; }}
      @media (max-width: 640px) {{
        .page {{ padding: 12px; }}
        h1 {{ font-size: 24px; }}
        .grid.metrics {{ grid-template-columns: 1fr; }}
        .metric-value {{ font-size: 22px; }}
      }}
    </style>
  </head>
  <body>
    <main class="page">{body}</main>
  </body>
</html>
"""