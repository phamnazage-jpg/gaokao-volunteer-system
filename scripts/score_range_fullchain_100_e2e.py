#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import http.client
import json
import os
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "reports" / "score_range_fullchain_100_cases_2026_06_25.json"
# P1-7 修复：默认回归产物写入 /tmp（gitignored），不覆写受版本控制的 reports/
OUT = Path("/tmp/score_range_fullchain_100_e2e.json")
BATCH_JSON = Path("/tmp/score_range_fullchain_100_batches.json")
BATCH_CSV = Path("/tmp/score_range_fullchain_100_batches.csv")
LOG = Path("/tmp/score-range-fullchain-100-e2e.log")
BASE_HOST = "127.0.0.1"
BASE_PORT = 19110
SMOKE_CASE_IDS = {2, 7, 12, 14, 20, 29, 31, 37, 44, 54, 83, 98}


def load_manifest(path: Path = MANIFEST) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_batch_plan(cases: list[dict[str, Any]]) -> dict[str, Any]:
    planned: list[dict[str, Any]] = []
    for case in cases:
        row = dict(case)
        batches: list[str] = []
        if row["id"] in SMOKE_CASE_IDS:
            batches.append("smoke")
        if row["expected_path"] == "fullchain":
            batches.append("fullchain")
        else:
            batches.append("boundary")
        row["batches"] = batches
        planned.append(row)
    return {
        "summary": {
            "case_count": len(planned),
            "smoke_case_count": sum(1 for row in planned if "smoke" in row["batches"]),
            "fullchain_case_count": sum(
                1 for row in planned if row["expected_path"] == "fullchain"
            ),
            "boundary_case_count": sum(
                1 for row in planned if row["expected_path"] == "contract_boundary"
            ),
        },
        "cases": planned,
    }


def write_batch_plan(plan: dict[str, Any], *, json_path: Path, csv_path: Path) -> None:
    json_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "id",
                "province",
                "score",
                "score_band_low",
                "score_band_high",
                "subjects",
                "anchor_major",
                "public_supported",
                "expected_path",
                "batches",
            ],
        )
        writer.writeheader()
        for row in plan["cases"]:
            writer.writerow({
                "id": row["id"],
                "province": row["province"],
                "score": row["score"],
                "score_band_low": row["score_band_low"],
                "score_band_high": row["score_band_high"],
                "subjects": "/".join(row.get("subjects") or []),
                "anchor_major": row["anchor_major"],
                "public_supported": "yes" if row["public_supported"] else "no",
                "expected_path": row["expected_path"],
                "batches": "/".join(row["batches"]),
            })


def select_cases(cases: list[dict[str, Any]], batch: str) -> list[dict[str, Any]]:
    if batch == "all":
        return list(cases)
    return [row for row in cases if batch in row.get("batches", [])]


def default_output_path(batch: str) -> Path:
    if batch == "all":
        return OUT
    return Path(f"/tmp/score_range_fullchain_100_e2e_{batch}.json")


def request(
    method: str,
    path: str,
    body: bytes | dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    *,
    port: int,
) -> tuple[int, dict[str, str], str]:
    conn = http.client.HTTPConnection(BASE_HOST, port, timeout=20)
    outgoing_headers = {"Connection": "close"}
    if headers:
        outgoing_headers.update(headers)
    payload: bytes | None
    if isinstance(body, dict):
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        outgoing_headers.setdefault("Content-Type", "application/json")
    else:
        payload = body
    conn.request(method, path, body=payload, headers=outgoing_headers)
    resp = conn.getresponse()
    raw_headers = {k.lower(): v for k, v in resp.getheaders()}
    text = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, raw_headers, text


def _start_admin(port: int) -> subprocess.Popen[str]:
    # P1-8 修复：启动前检测端口是否已被占用
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((BASE_HOST, port))
        sock.close()
    except OSError:
        raise RuntimeError(
            f"端口 {port} 已被占用，可能存在旧进程。"
            f"请先 kill 占用进程或更换端口再运行。"
        )

    env = os.environ.copy()
    env.update({
        "GAOKAO_ENV": "dev",
        "GAOKAO_DB_PATH": str(ROOT / f"data/orders/fullchain-admin-{port}.db"),
        "GAOKAO_ORDERS_DB_PATH": str(ROOT / f"data/orders-fullchain-{port}.db"),
        "GAOKAO_SHARE_DB_PATH": str(ROOT / f"data/share-fullchain-{port}.db"),
        "GAOKAO_SHARE_REPORT_DIR": str(ROOT / f"data/share-reports-fullchain-{port}"),
        "GAOKAO_OPS_ALERT_LOG": str(ROOT / f"data/alerts/fullchain-ops-{port}.jsonl"),
        "GAOKAO_RETENTION_DAYS": "180",
        "GAOKAO_JWT_SECRET": "x" * 32,
        "GAOKAO_PORTAL_TOKEN_SECRET": "y" * 32,
        "GAOKAO_ADMIN_USER": "admin",
        "GAOKAO_ADMIN_PASS": "FullchainTest1!",
        "GAOKAO_PAYMENT_WEBHOOK_SECRET": "P" + "r" * 31 + "!",
        "GAOKAO_PAYMENT_PROVIDER": "mock",
        "GAOKAO_ORDERS_FERNET_KEY": "F" * 44,
        "GAOKAO_ADMIN_BIND": f"127.0.0.1:{port}",
    })
    for directory in [
        ROOT / "data/orders",
        ROOT / "data",
        ROOT / f"data/share-reports-fullchain-{port}",
        ROOT / "data/alerts",
    ]:
        directory.mkdir(parents=True, exist_ok=True)
    log = open(LOG, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "admin.app:create_app",
            "--factory",
            "--host",
            BASE_HOST,
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # P1-8 修复：双条件探针（进程存活 + health 200）
    for _ in range(60):
        if proc.poll() is not None:
            proc.terminate()
            raise RuntimeError(f"admin 进程意外退出 (exit code={proc.returncode})")
        try:
            status, _, body = request("GET", "/health", port=port)
            if status == 200 and body.strip().startswith("{"):
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("admin failed to start")


def _stop_admin(proc: subprocess.Popen[str] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def execute_case(case: dict[str, Any], *, port: int) -> dict[str, Any]:
    idx = case["id"]
    row: dict[str, Any] = dict(case)
    row["sample_no"] = idx
    qs = urllib.parse.urlencode({
        "source": "home",
        "province": case["province"],
        "score": str(case["score"]),
        "goal": f"{case['province']} {case['score_band_note']} {case['anchor_major']} 复核",
        "consult": f"100样例全链路 idx={idx}",
    })
    st, hd, body = request("GET", f"/review/start?{qs}", port=port)
    row["review_start_status"] = st
    row["review_start_ok"] = (
        st == 200
        and ("方案复核入口" in body or "复核结果" in body)
        and case["province"] in body
    )

    if case["expected_path"] == "contract_boundary":
        # P1-2 修复：真正 POST /api/public/orders 验证是否被契约阻断
        order_payload = {
            "service_version": "standard",
            "amount_cents": 9900,
            "customer_phone": f"13888{idx:06d}",
            "candidate_name": f"边界验证{idx}",
            "candidate_province": case["province"],
        }
        st2, hd2, body2 = request(
            "POST", "/api/public/orders", order_payload, port=port
        )
        row["boundary_create_order_status"] = st2
        row["boundary_create_order_rejected"] = st2 in (400, 422)
        row["boundary_create_order_body"] = body2[:200]
        row["status"] = "skipped_public_order_contract_boundary"
        row["contract_boundary_ok"] = (
            row["review_start_ok"] and row["boundary_create_order_rejected"]
        )
        return row

    order_payload = {
        "service_version": "standard",
        "amount_cents": 9900,
        "customer_phone": f"13888{idx:06d}",
        "candidate_name": f"全链路100样例{idx}",
        "candidate_province": case["province"],
    }
    st, hd, body = request("POST", "/api/public/orders", order_payload, port=port)
    row["create_order_status"] = st
    if st != 201:
        row["status"] = "create_order_failed"
        row["create_order_body"] = body[:300]
        return row
    created = json.loads(body)
    row["order_id"] = created.get("order_id")
    row["checkout_url"] = created.get("checkout_url")
    row["portal_status_url"] = created.get("portal_status_url")

    payment_id = row["checkout_url"].split("/pay/mock/")[1].split("?")[0]
    st, hd, body = request("POST", f"/pay/mock/{payment_id}/complete", port=port)
    row["payment_complete_status"] = st
    row["payment_complete_location"] = hd.get("location")
    row["payment_complete_ok"] = st == 303 and bool(
        hd.get("location", "").endswith("/payment-success")
    )

    if hd.get("location"):
        st2, _, b2 = request("GET", hd["location"], port=port)
        row["payment_success_status"] = st2
        row["payment_success_ok"] = st2 == 200 and (
            "支付成功" in b2 or "订单进度总览" in b2 or "已支付" in b2
        )
    else:
        row["payment_success_status"] = None
        row["payment_success_ok"] = False

    info_path = row["portal_status_url"].replace("/status", "/info")
    st, _, body = request("GET", urllib.parse.urlparse(info_path).path, port=port)
    row["portal_info_get_status"] = st
    row["portal_info_get_ok"] = st == 200 and "考生资料填写" in body

    token = row["portal_status_url"].split("/portal/")[1].split("/status")[0]
    info_payload = {
        "mode": "submit",
        "candidate_province": case["province"],
        "candidate_subjects": case["subjects"],
        "candidate_score": case["score"],
        "candidate_rank": case["estimated_rank"],
        "existing_plan_summary": f"已有一版方案，100样例{idx}，先看风险",
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
    st, _, body = request("POST", f"/portal/{token}/info", info_payload, port=port)
    row["portal_info_submit_status"] = st
    row["portal_info_submit_ok"] = st in (200, 201)
    if st not in (200, 201):
        row["portal_info_submit_body"] = body[:300]

    st, _, body = request(
        "GET", urllib.parse.urlparse(row["portal_status_url"]).path, port=port
    )
    row["portal_status_status"] = st
    row["portal_status_ok"] = st == 200 and "订单进度总览" in body

    st, _, body = request(
        "GET",
        f"/review/start?source=status&token={urllib.parse.quote(token)}",
        port=port,
    )
    row["token_review_start_status"] = st
    row["token_review_start_ok"] = (
        st == 200
        and ("方案复核入口" in body or "复核结果" in body)
        and case["province"] in body
    )

    form = urllib.parse.urlencode({"token": token, "action": "full_plan"})
    st, hd, body = request(
        "POST",
        "/review/action",
        form.encode(),
        {"Content-Type": "application/x-www-form-urlencoded"},
        port=port,
    )
    row["review_action_full_plan_status"] = st
    row["review_action_full_plan_location"] = hd.get("location")
    if hd.get("location"):
        st2, _, b2 = request("GET", hd["location"], port=port)
        row["full_plan_status"] = st2
        row["full_plan_ok"] = (
            st2 == 200 and "完整规划建议页" in b2 and "方案优先级" in b2
        )
    else:
        row["full_plan_status"] = None
        row["full_plan_ok"] = False

    form = urllib.parse.urlencode({"token": token, "action": "cwb"})
    st, hd, body = request(
        "POST",
        "/review/action",
        form.encode(),
        {"Content-Type": "application/x-www-form-urlencoded"},
        port=port,
    )
    row["review_action_cwb_status"] = st
    row["review_action_cwb_location"] = hd.get("location")
    if hd.get("location"):
        st2, _, b2 = request("GET", hd["location"], port=port)
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
    return row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="100 个高考分数真实全链路验证")
    parser.add_argument(
        "--batch", choices=["all", "smoke", "fullchain", "boundary"], default="all"
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--batch-json", type=Path, default=BATCH_JSON)
    parser.add_argument("--batch-csv", type=Path, default=BATCH_CSV)
    parser.add_argument("--port", type=int, default=BASE_PORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = args.output or default_output_path(args.batch)
    manifest = load_manifest(args.manifest)
    plan = build_batch_plan(manifest["cases"])
    write_batch_plan(plan, json_path=args.batch_json, csv_path=args.batch_csv)
    selected = select_cases(plan["cases"], args.batch)

    print(
        f"[fullchain100] batch={args.batch} selected={len(selected)} port={args.port}"
    )
    proc = _start_admin(args.port)
    try:
        results = []
        for case in selected:
            row = execute_case(case, port=args.port)
            results.append(row)
            print(
                f"  [{'OK' if row['status'] in ('ok', 'skipped_public_order_contract_boundary') else 'FAIL'}] "
                f"#{row['id']:03d} {row['province']} {row['score']} -> {row['status']}"
            )
    finally:
        _stop_admin(proc)

    review_start_pass = sum(1 for row in results if row.get("review_start_ok"))
    eligible = [row for row in results if row["expected_path"] == "fullchain"]
    passed = [row for row in eligible if row.get("status") == "ok"]
    failed = [
        row
        for row in results
        if row.get("status") not in ("ok", "skipped_public_order_contract_boundary")
    ]
    boundary = [row for row in results if row["expected_path"] == "contract_boundary"]
    boundary_pass = [
        row
        for row in boundary
        if row.get("status") == "skipped_public_order_contract_boundary"
        and row.get("contract_boundary_ok")
    ]
    full_plan_pass = sum(1 for row in eligible if row.get("full_plan_ok"))
    cwb_pass = sum(1 for row in eligible if row.get("cwb_ok"))

    summary = {
        "base_url": f"http://{BASE_HOST}:{args.port}",
        "selected_batch": args.batch,
        "selected_case_count": len(results),
        "review_start_pass": review_start_pass,
        "review_start_fail": len(results) - review_start_pass,
        "eligible_for_fullchain": len(eligible),
        "fullchain_pass": len(passed),
        "fullchain_fail": len(eligible) - len(passed),
        "contract_boundary_expected": len(boundary),
        "contract_boundary_pass": len(boundary_pass),
        "contract_boundary_fail": len(boundary) - len(boundary_pass),
        "full_plan_pass": full_plan_pass,
        "cwb_pass": cwb_pass,
        "failed_samples": failed,
        "samples": results,
        "batch_plan_json": str(args.batch_json.relative_to(ROOT)),
        "batch_plan_csv": str(args.batch_csv.relative_to(ROOT)),
        "note": "fullchain=公开支持省份完整下单链路；contract_boundary=非公开支持省份仅验证复核入口与合同边界。",
    }
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {output_path}")
    print(f"review_start_pass={review_start_pass}/{len(results)}")
    print(f"eligible_for_fullchain={len(eligible)}")
    print(f"fullchain_pass={len(passed)}/{len(eligible)}")
    print(f"contract_boundary_pass={len(boundary_pass)}/{len(boundary)}")
    print(f"full_plan_pass={full_plan_pass}/{len(eligible)}")
    print(f"cwb_pass={cwb_pass}/{len(eligible)}")
    return 0 if not failed and len(boundary_pass) == len(boundary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
