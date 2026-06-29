"""轻量管理后台页面路由。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional, cast

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, HTMLResponse

from admin.auth import require_role
from admin.db import AdminUser
from admin.config import Settings, get_settings_dep
from admin.share_page import (
    load_report_from_directory,
    render_share_page,
    status_code_for_result,
)
from data.share.short_link import route_short_link_with_report


router = APIRouter(tags=["ui"])

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_DASHBOARD_HTML = _STATIC_DIR / "dashboard.html"


@router.get("/admin/login", include_in_schema=False)
def admin_login_page() -> HTMLResponse:
    """管理后台 Web 登录页。"""
    html = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>管理后台登录</title>
<link rel="stylesheet" href="/static/portal-ui.css" />
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0e1a2b;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.login-card{background:#fff;border-radius:24px;box-shadow:0 24px 52px rgba(20,34,53,.16);padding:40px;max-width:400px;width:100%}
.login-card h1{font-size:24px;color:#142235;margin-bottom:8px}
.login-card .sub{color:#5b6b88;font-size:14px;margin-bottom:28px}
.field{margin-bottom:16px}
.field label{display:block;font-size:13px;font-weight:600;color:#334155;margin-bottom:6px}
.field input{width:100%;padding:12px 14px;border-radius:12px;border:1px solid #d7e3f1;font-size:14px;background:#f8fbff;transition:border-color .18s}
.field input:focus{outline:none;border-color:#1f6feb;box-shadow:0 0 0 4px rgba(31,111,235,.12)}
.btn-login{width:100%;min-height:48px;border-radius:14px;border:none;background:linear-gradient(135deg,#2d7cff,#0f4fd6);color:#fff;font-size:16px;font-weight:700;cursor:pointer;transition:.18s;margin-top:8px}
.btn-login:hover{transform:translateY(-1px);box-shadow:0 12px 28px rgba(31,111,235,.32)}
.btn-login:disabled{opacity:.6;cursor:not-allowed;transform:none}
.error-msg{margin-top:16px;padding:12px 14px;border-radius:12px;background:#fef2f2;border:1px solid #fecaca;color:#b42318;font-size:13px;display:none}
.error-msg.show{display:block}
.back-home{display:block;margin-top:20px;text-align:center;color:#5b6b88;font-size:13px;text-decoration:none}
.back-home:hover{color:#1f6feb}
</style>
</head>
<body>
<div class="login-card">
<h1>管理后台</h1>
<p class="sub">请输入管理员账号密码登录</p>
<form id="login-form">
<div class="field">
<label>用户名</label>
<input type="text" id="username" name="username" placeholder="admin" required autocomplete="username" />
</div>
<div class="field">
<label>密码</label>
<input type="password" id="password" name="password" placeholder="请输入密码" required autocomplete="current-password" />
</div>
<div id="error-msg" class="error-msg"></div>
<button type="submit" class="btn-login" id="login-btn">登录</button>
</form>
<a class="back-home" href="/">← 返回首页</a>
</div>
<script>
(function(){
var form=document.getElementById('login-form');
var errEl=document.getElementById('error-msg');
var btn=document.getElementById('login-btn');
form.addEventListener('submit',function(e){
e.preventDefault();
var u=document.getElementById('username').value.trim();
var p=document.getElementById('password').value;
if(!u||!p){showError('请输入用户名和密码');return;}
btn.disabled=true;
btn.textContent='登录中...';
errEl.classList.remove('show');
fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})})
.then(function(resp){return resp.json().then(function(d){return{ok:resp.ok,data:d};});})
.then(function(r){
if(r.ok&&r.data.access_token){
var token=r.data.access_token;
var expires=Date.now()+(r.data.expires_in||3600)*1000;
try{
localStorage.setItem('admin_token',token);
localStorage.setItem('admin_token_expires',String(expires));
sessionStorage.setItem('admin_token',token);
}catch(e){}
window.location.href='/admin/dashboard?t='+encodeURIComponent(token);
}else{
var msg=(r.data&&r.data.message)||'登录失败，请检查用户名和密码';
showError(msg);
btn.disabled=false;
btn.textContent='登录';
}
})
.catch(function(){
showError('网络异常，请稍后重试');
btn.disabled=false;
btn.textContent='登录';
});
});
function showError(msg){
errEl.textContent=msg;
errEl.classList.add('show');
}
})();
</script>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/dashboard", include_in_schema=False)
@router.get("/admin/dashboard", include_in_schema=False)
def dashboard_page(_: AdminUser = Depends(require_role("admin"))) -> FileResponse:
    """返回最小仪表盘页面壳。"""
    return FileResponse(_DASHBOARD_HTML)


@router.get("/admin/orders/new", include_in_schema=False)
def admin_new_order_page(_: AdminUser = Depends(require_role("admin"))) -> HTMLResponse:
    return HTMLResponse(_render_admin_new_order_page())



@router.get("/s/{code}", include_in_schema=False)
def share_page(
    code: str,
    request: Request,
    pwd: Optional[str] = Query(default=None),
) -> HTMLResponse:
    """公开分享页（T7.5）。"""
    settings = get_settings_dep(request)
    report_loader = _resolve_report_loader(request, settings)
    result = route_short_link_with_report(
        code,
        password=pwd,
        base_url=str(request.base_url).rstrip("/"),
        db_path=Path(settings.share_db_path),
        report_loader=report_loader,
    )
    html = render_share_page(result, password=pwd)
    return HTMLResponse(html, status_code=status_code_for_result(result))


def _resolve_report_loader(
    request: Request, settings: Settings
) -> Optional[Callable[[str], Optional[dict[str, Any]]]]:
    custom_loader = getattr(request.app.state, "share_report_loader", None)
    if callable(custom_loader):
        return cast(Callable[[str], Optional[dict[str, Any]]], custom_loader)

    report_dir = settings.share_report_dir
    if not report_dir:
        return None

    def _loader(report_id: str) -> Optional[dict]:
        return load_report_from_directory(report_id, report_dir)

    return _loader


def _render_admin_new_order_page() -> str:
    province_options = [
        "北京",
        "上海",
        "天津",
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
        "广西",
        "海南",
        "四川",
        "贵州",
        "云南",
        "甘肃",
        "青海",
        "宁夏",
        "新疆",
        "内蒙古",
        "西藏",
    ]
    province_html = "".join(
        f'<option value="{p}">{p}</option>' for p in province_options
    )
    return f"""<!doctype html>
<html lang='zh-CN'><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' /><title>后台手动添加订单</title>
<link rel='stylesheet' href='/static/portal-ui.css' />
<style>
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f7fb;color:#172033;margin:0; }}
.wrap {{ max-width:960px; margin:0 auto; padding:32px 20px; display:grid; gap:16px; }}
.panel {{ background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px; box-shadow:0 18px 42px rgba(20,34,53,.08); }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
.field {{ display:flex; flex-direction:column; gap:6px; margin-bottom:14px; }}
input, select, textarea {{ width:100%; padding:12px; border-radius:12px; border:1px solid #cfd7e6; }}
textarea {{ min-height:110px; resize:vertical; }}
button {{ border:none;border-radius:14px;background:#1f6feb;color:#fff;font-weight:700;padding:13px 18px;cursor:pointer; }}
.helper {{ color:#5b6b88; line-height:1.7; }}
.proof {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:16px 0 20px; }}
.proof-item {{ padding:14px 16px; border-radius:16px; background:linear-gradient(180deg,#f8fbff,#eef5ff); border:1px solid #d7e3f1; }}
.proof-item strong {{ display:block; margin-bottom:4px; }}
#result {{ margin-top:14px; min-height:24px; color:#5b6b88; white-space:pre-wrap; }}
@media (max-width: 900px) {{ .grid, .proof {{ grid-template-columns:1fr; }} }}
</style>
</head><body><main class='wrap'>
<section class='panel'><span class='portal-eyebrow'>后台录单</span><h1>后台手动添加订单</h1><p class='helper'>用于人工服务场景下的补录、客服录单或线下沟通后的订单补建。页面会读取当前登录态调用 <code>/api/orders</code>。</p></section>
<section class='panel'>
<div class='proof'>
  <article class='proof-item'><strong>人工补录更直接</strong><span>适合客服、学校渠道或线下沟通后补建订单。</span></article>
  <article class='proof-item'><strong>与后台订单主链一致</strong><span>录入后仍会进入统一订单、通知与交付链路。</span></article>
  <article class='proof-item'><strong>字段尽量按业务语义展示</strong><span>避免让后台录单页继续像内部测试表单。</span></article>
</div>
<form id='order-form'>
<div class='grid'>
<div class='field'><label>来源</label><select name='source'><option value='wechat'>wechat</option><option value='xianyu'>xianyu</option><option value='web'>web</option><option value='school'>school</option></select></div>
<div class='field'><label>服务版本</label><select name='service_version'><option value='audit'>audit</option><option value='basic'>basic</option><option value='standard' selected>standard</option><option value='premium'>premium</option></select></div>
<div class='field'><label>金额（分）</label><input name='amount_cents' value='9900' /></div>
<div class='field'><label>称呼</label><input name='customer_name' placeholder='可选，例如：张同学 / 张家长' /></div>
<div class='field'><label>手机号</label><input name='customer_phone' /></div>
<div class='field'><label>微信</label><input name='customer_wechat' /></div>
<div class='field'><label>考生姓名</label><input name='candidate_name' /></div>
<div class='field'><label>考试省份</label><select name='candidate_province'>{province_html}</select></div>
<div class='grid'>
<div class='field'><label>同意方式</label><select name='consent_method'><option value='verbal_chat' selected>verbal_chat</option><option value='phone_recording'>phone_recording</option><option value='screenshot'>screenshot</option><option value='written_form'>written_form</option><option value='self_declared'>self_declared</option></select></div>
<div class='field'><label>同意备注</label><input name='consent_note' placeholder='例如：微信沟通后家长口头同意' /></div>
</div>
<div class='field'><label>备注</label><textarea name='notes'></textarea></div>
<button type='submit'>创建订单</button>
</form>
<div id='result'></div>
</section></main>
<script>
const TOKEN_KEY = 'gaokao_admin_dashboard_token';
document.getElementById('order-form').addEventListener('submit', async function(event) {{
  event.preventDefault();
  const token = window.sessionStorage.getItem(TOKEN_KEY) || '';
  const form = new FormData(event.target);
  const payload = {{
    source: form.get('source'),
    service_version: form.get('service_version'),
    amount_cents: Number(form.get('amount_cents') || 0),
    customer_name: form.get('customer_name') || null,
    customer_phone: form.get('customer_phone') || null,
    customer_wechat: form.get('customer_wechat') || null,
    candidate_name: form.get('candidate_name') || null,
    candidate_province: form.get('candidate_province') || null,
    notes: form.get('notes') || null,
    consent: {{
      consent_method: form.get('consent_method') || 'verbal_chat',
      consent_note: form.get('consent_note') || null,
    }},
  }};
  const resultNode = document.getElementById('result');
  resultNode.textContent = '正在创建订单…';
  const resp = await fetch('/api/orders', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json', 'Authorization': `Bearer ${{token}}` }},
    body: JSON.stringify(payload),
  }});
  const body = await resp.json();
  resultNode.textContent = JSON.stringify(body, null, 2);
}});
</script>
<!-- 合规 footer: 与 portal 前台 _render_footer_links() 同口径 -->
<footer style="margin-top:32px;padding:16px;border-top:1px solid #d8e0ee;color:#5b6b88;font-size:13px;text-align:center;background:#f4f6fb;">
  <a href="/privacy" style="color:#2f55a4;text-decoration:none;margin:0 8px;">隐私政策</a> ·
  <a href="/deletion-policy" style="color:#2f55a4;text-decoration:none;margin:0 8px;">数据删除说明</a> ·
  <a href="/service-terms" style="color:#2f55a4;text-decoration:none;margin:0 8px;">服务说明</a>
  <div style="margin-top:4px;color:#7c8aa8;">© 2026 高考志愿填报智能系统 · 内部操作员亦需遵守隐私与数据合规</div>
</footer>
</body></html>"""
