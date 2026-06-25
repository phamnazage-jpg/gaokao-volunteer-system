# Full Upgrade Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the remaining P1/P2 user-facing upgrade work so the audit-first web flow has first-class 冲稳保 / 报告资产化 / 政策与同分段辅助 / 轻量版本管理.

**Architecture:** Reuse the existing `admin/routes/web_public.py` flow rather than introducing new subsystems. Persist new version/history metadata in `order_intakes.payload_json` beside the existing `review_results` map, keep `orders` as the current-live snapshot + artifact pointers, and upgrade existing user pages/routes in place.

**Tech Stack:** FastAPI route functions, inline HTML renderers in `admin/routes/web_public.py`, `data/orders/intake_store.py`, Pydantic `IntakePayload`, pytest route tests.

---

### Task 1: Lock failing regression tests for remaining P1/P2 gaps

**Files:**
- Modify: `admin/tests/test_web_public_review_flow.py`
- Modify: `admin/tests/test_web_public_content_pages.py`
- Modify: `admin/tests/test_web_public_portal_info.py`
- Modify: `data/orders/tests/test_schema.py`

**Step 1: Write failing tests**
- Report page should show whether current report is based on latest profile version.
- CWB/report pages should expose policy center / same-score helper entry points.
- Portal info page should render/save `target_cities` and any new version anchor output.
- Schema tests should lock new lightweight profile/report version metadata helpers or payload contracts.

**Step 2: Run the narrow test subset to confirm red**
Run:
`./.venv/bin/python -m pytest -q admin/tests/test_web_public_review_flow.py admin/tests/test_web_public_content_pages.py admin/tests/test_web_public_portal_info.py data/orders/tests/test_schema.py -k 'version or policy or score or target_cities or assessment or cwb'`

**Step 3: Implement only enough to make these pass**

**Step 4: Re-run the same subset**

---

### Task 2: Add lightweight profile/report version metadata without schema churn

**Files:**
- Modify: `admin/routes/web_public.py`
- Possibly modify: `data/orders/intake_schema.py`
- Test: `admin/tests/test_web_public_review_flow.py`
- Test: `admin/tests/test_web_public_portal_info.py`
- Test: `data/orders/tests/test_schema.py`

**Step 1: Add helper functions in `web_public.py`**
- Normalize profile snapshots from intake payload.
- Append profile version only when a saved snapshot meaningfully changes.
- Keep `latest_profile_version_id` and `profile_versions[]` in `order_intakes.payload_json`.
- Add idempotent report metadata sync for existing generated report artifacts: `latest_report_version_id` + `report_versions[]`.

**Step 2: Wire profile snapshot save into `submit_order_info`**
- After `IntakeStore.save`, update the saved payload with profile version metadata.
- Do not create a new version for identical snapshots.

**Step 3: Wire report metadata sync into report rendering**
- Reuse current derived `report_version` label as the metadata id.
- Reference latest profile version + latest review result id when available.
- Never create duplicate report versions on repeated page opens.

**Step 4: Surface latest-vs-history semantics in report page**
- Explicitly show whether the current report is based on latest profile.
- Show historical/stale warning when latest profile has moved on.

---

### Task 3: Finish P1 page upgrades in existing routes

**Files:**
- Modify: `admin/routes/web_public.py`
- Test: `admin/tests/test_web_public_review_flow.py`
- Test: `admin/tests/test_web_public_content_pages.py`
- Test: `admin/tests/test_order_status_page.py`

**Step 1: Upgrade CWB page in place**
- Keep `/portal/{token}/cwb`.
- Replace placeholder tone with first-class workspace sections: summary, 3-column C/W/B board, next actions, policy/same-score helper links.

**Step 2: Upgrade report shell in place**
- Keep `_render_report_shell` as the only outer shell.
- Add sections for version header, conclusion summary, risk summary, CWB action zone, policy/same-score helper links, next actions.
- Preserve original report body as a raw section instead of dropping it.

**Step 3: Add helper navigation to policy and same-score pages**
- Ensure entry can be discovered from report/CWB/status/home where required.
- Keep trust-boundary copy explicit.

**Step 4: Extract or centralize trust banner rendering**
- Source, update time, scope, confidence, and non-high-confidence constraints should come from one helper, reused by policy/same-score pages.

---

### Task 4: Close Step 2-4 / P2 UI and auxiliary factors

**Files:**
- Modify: `admin/routes/web_public.py`
- Test: `admin/tests/test_web_public_portal_info.py`
- Test: `admin/tests/test_web_public_review_flow.py`

**Step 1: Add missing Step 2 UI field**
- Render `target_cities` in the portal info page so current schema/persistence and UI are aligned.

**Step 2: Surface deep preference / assessment data as auxiliary context**
- In CWB/report/full-plan views, show optional “辅助判断因子” block when interest-assessment or deep preference data exists.
- Keep wording explicit: auxiliary only, not sole basis.

**Step 3: Keep all Step 2-4 and P2 fields optional**
- No change may make them gating for audit entry.

---

### Task 5: Update docs and execution truth sources

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `docs/UPGRADE_EXECUTION_BOARD_2026-06-22.md`
- Modify: `docs/PAGE_REDESIGN_CHECKLIST_2026-06-21.md`
- Modify: `docs/REPORT_PROFILE_VERSION_RELATION_2026-06-22.md`
- Modify: `product/PRD_UPGRADE_2026-06-21.md`
- Conditional: `docs/FIELD_MAPPING_AUDIT_FIRST_PROFILE_2026-06-21.md`

**Step 1: Update completion status for truly completed P1/P2 items**
- Only mark complete if code + tests now prove it.

**Step 2: Sync page acceptance language**
- Report latest-profile rule, policy/same-score trust boundary, target_cities UI, and version metadata location.

**Step 3: Record the chosen low-churn version storage design**
- `order_intakes.payload_json` as the history home; `orders` as current-live artifact mirror.

---

### Task 6: Run focused regression and final board verification

**Files:**
- Test only

**Step 1: Run directly affected suite**
`./.venv/bin/python -m pytest -q admin/tests/test_web_public_review_flow.py admin/tests/test_web_public_content_pages.py admin/tests/test_web_public_portal_info.py admin/tests/test_order_status_page.py data/orders/tests/test_schema.py`

**Step 2: Expand one ring if green**
`./.venv/bin/python -m pytest -q admin/tests/test_web_public.py admin/tests/test_web_public_review_flow.py admin/tests/test_web_public_content_pages.py admin/tests/test_web_public_portal_info.py admin/tests/test_order_status_page.py data/orders/tests/test_schema.py`

**Step 3: Verify docs/board status**
- Re-read `docs/UPGRADE_EXECUTION_BOARD_2026-06-22.md` and confirm P1/P2 items no longer pending if implemented.
