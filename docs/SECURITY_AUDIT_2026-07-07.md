# SECURITY_AUDIT_2026-07-07

## Scope

Follow-up for `reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md` M7.

## Findings and actions

| Surface | Classification | Action |
|---|---|---|
| `admin/routes/web_public.py` loading helper `innerHTML` | user-visible DOM write | Replaced with `replaceChildren()` + `textContent` when present. |
| `admin/routes/web_public.py` global hint `innerHTML` | error text rendering | Replaced with `textContent` when present. |
| `data/payments/dao.py` PRAGMA / ALTER TABLE f-strings | controlled table/DDL identifiers | Allowed; identifiers are internal constants, not user input. |
| test subprocess calls | test harness only | Allowed; no `shell=True` and no user-controlled shell string observed in reviewed hits. |
| vendored ECharts fallback | vendored/minified with escaping helper | Recorded as vendored boundary; do not edit manually. |

## Verification

- `grep` should not find `globalHint.innerHTML` in `admin/routes/web_public.py`.
- Web public route tests should pass.
