#!/usr/bin/env python3
from __future__ import annotations

import http.client
import json
import pathlib
import urllib.parse
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
CROWD = ROOT / "data" / "crowd_db"
OUT = ROOT / "reports" / "score_range_fullchain_e2e_2026_06_26.json"
BASE_HOST = "127.0.0.1"
BASE_PORT = 19100
PUBLIC_SUPPORTED = {
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


def request(
    method: str,
    path: str,
    body: Any | None = None,
    headers: dict[str, str] | None = None,
):
    conn = http.client.HTTPConnection(BASE_HOST, BASE_PORT, timeout=20)
    h = {"Connection": "close"}
    if headers:
        h.update(headers)
    payload: bytes = b""
    if body is not None:
        if isinstance(body, bytes):
            payload = body
        elif isinstance(body, bytearray):
            payload = bytes(body)
        else:
            payload = json.dumps(body, ensure_ascii=False).encode()
            h.setdefault("Content-Type", "application/json")
    conn.request(method, path, body=payload, headers=h)
    resp = conn.getresponse()
    text = resp.read().decode("utf-8", "replace")
    resp_headers = {k.lower(): v for k, v in resp.getheaders()}
    status = resp.status
    conn.close()
    return status, resp_headers, text


def pick_samples(limit: int = 30):
    samples = []
    for path in sorted(CROWD.glob("*.json")):
        data = json.loads(path.read_text())
        province = data["province"]
        for idx, sr in enumerate(data.get("score_ranges", [])):
            lo, hi = sr["range"]
            mid = (lo + hi) // 2
            recs = sr.get("recommendations", [])
            top = recs[0] if recs else {}
            subj = top.get("subject_requirements") or {}
            preferred = str(subj.get("preferred_subject") or "").strip()
            reselect = [
                str(x).strip()
                for x in subj.get("reselect_subject") or []
                if str(x).strip()
            ]
            subjects = [x for x in [preferred, *reselect] if x]
            if not subjects:
                subjects = ["物理"]
            rank = max(1, 100000 - mid * 100)
            samples.append({
                "province": province,
                "range_index": idx,
                "range": [lo, hi],
                "score": mid,
                "rank": rank,
                "subjects": subjects[:3],
                "note": sr.get("note", ""),
                "major": str(top.get("major") or "先复核现有方案").strip(),
            })
    by_prov: dict[str, list[dict[str, Any]]] = {}
    for s in samples:
        by_prov.setdefault(s["province"], []).append(s)
    for arr in by_prov.values():
        arr.sort(key=lambda x: (x["range"][0], x["range"][1]))
    picked = []
    round_idx = 0
    for _ in range(100):
        progressed = False
        for province in sorted(by_prov):
            arr = by_prov[province]
            if round_idx < len(arr):
                picked.append(arr[round_idx])
                progressed = True
                if len(picked) >= limit:
                    return picked
        if not progressed:
            break
        round_idx += 1
    return picked[:limit]


def main() -> int:
    samples = pick_samples(30)
    results: list[dict[str, Any]] = []
    full_plan_ok = 0
    cwb_ok = 0
    for idx, s in enumerate(samples, 1):
        row: dict[str, Any] = {
            "sample_no": idx,
            **s,
            "eligible_for_public_order": s["province"] in PUBLIC_SUPPORTED,
        }
        # 1) review/start from landing params
        qs = urllib.parse.urlencode({
            "source": "home",
            "province": s["province"],
            "score": str(s["score"]),
            "goal": f"{s['province']} {s['note']} {s['major']} 复核",
            "consult": f"全链路样例 idx={idx}",
        })
        st, hd, body = request("GET", f"/review/start?{qs}")
        row["review_start_status"] = st
        # 真实契约：未登录访客看到的是「复核结果」页（含"你当前提交的信息"+"初步评估结果"+"下一步建议"）；
        # 已登录 token 访问才会进入"方案复核入口"。两种都算 review 主入口可达。
        row["review_start_ok"] = (
            st == 200
            and ("方案复核入口" in body or "复核结果" in body)
            and s["province"] in body
            and str(s["score"]) in body
        )

        if not row["eligible_for_public_order"]:
            row["status"] = "skipped_public_order_contract_boundary"
            results.append(row)
            continue

        # 2) public order
        order_payload = {
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": f"13899{idx:06d}",
            "candidate_name": f"全链路样例{idx}",
            "candidate_province": s["province"],
        }
        st, hd, body = request("POST", "/api/public/orders", order_payload)
        row["create_order_status"] = st
        if st != 201:
            row["status"] = "create_order_failed"
            row["create_order_body"] = body[:300]
            results.append(row)
            continue
        created = json.loads(body)
        row["order_id"] = created.get("order_id")
        row["checkout_url"] = created.get("checkout_url")
        row["portal_status_url"] = created.get("portal_status_url")

        # 3) pay mock complete
        payment_id = row["checkout_url"].split("/pay/mock/")[1].split("?")[0]
        st, hd, body = request("POST", f"/pay/mock/{payment_id}/complete")
        row["payment_complete_status"] = st
        row["payment_complete_location"] = hd.get("location")
        row["payment_complete_ok"] = st == 303 and bool(
            hd.get("location", "").endswith("/payment-success")
        )

        # 4) payment success page
        if hd.get("location"):
            st2, hd2, b2 = request("GET", hd["location"])
            row["payment_success_status"] = st2
            row["payment_success_ok"] = st2 == 200 and (
                "支付成功" in b2 or "订单进度总览" in b2 or "已支付" in b2
            )
        else:
            row["payment_success_status"] = None
            row["payment_success_ok"] = False

        # 5) portal info GET
        info_path = row["portal_status_url"].replace("/status", "/info")
        st, hd, body = request("GET", urllib.parse.urlparse(info_path).path)
        row["portal_info_get_status"] = st
        row["portal_info_get_ok"] = st == 200 and "考生资料填写" in body

        # 6) portal info POST/submit via真实 portal 入口
        token = row["portal_status_url"].split("/portal/")[1].split("/status")[0]
        info_payload = {
            "mode": "submit",
            "candidate_province": s["province"],
            "candidate_subjects": s["subjects"],
            "candidate_score": s["score"],
            "candidate_rank": s["rank"],
            "existing_plan_summary": f"已有一版方案，样例{idx}，先看有没有风险",
            "family_background": "家长希望先看梯度是否合理",
            "interest_assessment_type": "mbti",
            "interest_assessment_result": "INTJ",
            "interest_assessment_notes": "仅做辅助",
            "consent_version": "portal-v1",
            "consent_scope": "step1",
            "privacy_accepted": True,
            "service_terms_accepted": True,
            "guardian_confirmed": True,
        }
        st, hd, body = request("POST", f"/portal/{token}/info", info_payload)
        row["portal_info_submit_status"] = st
        row["portal_info_submit_ok"] = st in (200, 201)
        if st not in (200, 201):
            row["portal_info_submit_body"] = body[:300]

        # 7) status page
        st, hd, body = request(
            "GET", urllib.parse.urlparse(row["portal_status_url"]).path
        )
        row["portal_status_status"] = st
        row["portal_status_ok"] = st == 200 and "订单进度总览" in body

        # 8) review start with token
        st, hd, body = request(
            "GET", f"/review/start?source=status&token={urllib.parse.quote(token)}"
        )
        row["token_review_start_status"] = st
        row["token_review_start_ok"] = (
            st == 200
            and ("方案复核入口" in body or "复核结果" in body)
            and s["province"] in body
        )

        # 9a) full plan action
        form = urllib.parse.urlencode({"token": token, "action": "full_plan"})
        st, hd, body = request(
            "POST",
            "/review/action",
            form.encode(),
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        row["review_action_full_plan_status"] = st
        row["review_action_full_plan_location"] = hd.get("location")
        if hd.get("location"):
            st2, hd2, b2 = request("GET", hd["location"])
            row["full_plan_status"] = st2
            row["full_plan_ok"] = (
                st2 == 200 and "完整规划建议页" in b2 and "方案优先级" in b2
            )
        else:
            row["full_plan_status"] = None
            row["full_plan_ok"] = False
        if row["full_plan_ok"]:
            full_plan_ok += 1

        # 9b) cwb action
        form = urllib.parse.urlencode({"token": token, "action": "cwb"})
        st, hd, body = request(
            "POST",
            "/review/action",
            form.encode(),
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        row["review_action_cwb_status"] = st
        row["review_action_cwb_location"] = hd.get("location")
        if hd.get("location"):
            st2, hd2, b2 = request("GET", hd["location"])
            row["cwb_status"] = st2
            row["cwb_ok"] = (
                st2 == 200
                and "冲稳保建议页" in b2
                and "冲刺建议" in b2
                and "稳妥建议" in b2
                and "保底建议" in b2
            )
        else:
            row["cwb_status"] = None
            row["cwb_ok"] = False
        if row["cwb_ok"]:
            cwb_ok += 1

        row["status"] = (
            "ok"
            if all([
                row["review_start_ok"],
                row["payment_complete_ok"],
                row["payment_success_ok"],
                row["portal_info_get_ok"],
                row["portal_info_submit_ok"],
                row["portal_status_ok"],
                row["token_review_start_ok"],
                row["full_plan_ok"],
                row["cwb_ok"],
            ])
            else "failed"
        )
        results.append(row)

    eligible = [r for r in results if r["eligible_for_public_order"]]
    passed = [r for r in eligible if r["status"] == "ok"]
    failed = [r for r in eligible if r["status"] != "ok"]

    # P1-3 安全脱敏：在写入报告前，从每个 sample 移除含 portal token 的 URL 字段
    SENSITIVE_FIELDS = [
        "portal_status_url",
        "checkout_url",
        "payment_complete_location",
        "review_action_full_plan_location",
        "review_action_cwb_location",
    ]
    sanitized_results = []
    for r in results:
        sr = dict(r)
        for field in SENSITIVE_FIELDS:
            if field in sr:
                sr[field] = "<redacted>"
        sanitized_results.append(sr)
    sanitized_failed = []
    for r in failed:
        sr = dict(r)
        for field in SENSITIVE_FIELDS:
            if field in sr:
                sr[field] = "<redacted>"
        sanitized_failed.append(sr)

    summary = {
        "base_url": f"http://{BASE_HOST}:{BASE_PORT}",
        "sample_count_total": len(sanitized_results),
        "eligible_for_fullchain": len(eligible),
        "fullchain_pass": len(passed),
        "fullchain_fail": len(failed),
        "full_plan_pass": full_plan_ok,
        "cwb_pass": cwb_ok,
        "skipped_contract_boundary": [
            {
                "sample_no": r["sample_no"],
                "province": r["province"],
                "reason": r["status"],
            }
            for r in sanitized_results
            if not r["eligible_for_public_order"]
        ],
        "failed_samples": sanitized_failed,
        "samples": sanitized_results,
        "note": "完整链路定义：下单 -> 支付模拟 -> payment-success -> portal info -> portal status -> review/start -> review/action(full_plan/cwb) -> 页面回读。非 public supported province 不计入完整下单链路失败。portal token URL 已脱敏（P1-3）。",
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"wrote {OUT}")
    print(f"eligible_for_fullchain={len(eligible)}")
    print(f"fullchain_pass={len(passed)}/{len(eligible)}")
    print(f"full_plan_pass={full_plan_ok}/{len(eligible)}")
    print(f"cwb_pass={cwb_ok}/{len(eligible)}")
    print(
        "skipped_contract_boundary="
        f"{sum(1 for r in results if not r['eligible_for_public_order'])}"
    )
    if failed:
        print(json.dumps(failed[:2], ensure_ascii=False, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
