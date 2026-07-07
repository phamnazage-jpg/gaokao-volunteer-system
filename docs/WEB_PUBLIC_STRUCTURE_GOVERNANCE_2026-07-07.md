# WEB_PUBLIC_STRUCTURE_GOVERNANCE_2026-07-07

## Context

`admin/routes/web_public.py` was flagged in `reports/REVIEW_REPORT_2026-07-07_SYSTEMIC_REVIEW.md` as a 300KB mixed public-route module.

## First cut performed

- Extracted public content/data helper functions into `admin/routes/public_content_helpers.py`.
- Kept runtime routes and URL behavior unchanged.
- This is intentionally a low-risk first cut before moving full route handlers.

## Next structural cuts

1. Move legal/content page renderers (`privacy`, `service-terms`, `deletion-policy`) into a dedicated module with router include.
2. Move data-query content pages (`policy-center`, `same-score-reference`, score/rank/majors/schools query pages) into a separate router module.
3. Keep public payment and portal routes separate from static content routes.

## Acceptance

- Existing public content tests pass.
- `admin/routes/web_public.py` size decreases from the 2026-07-07 review baseline.
