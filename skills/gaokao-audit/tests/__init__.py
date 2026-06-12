"""Tests for the gaokao-audit skill.

This package is intentionally lightweight at the T1.2 milestone: only the
HTML template validation test lives here. The substantive parser test
suite (`test_plan_parser.py`) is added in T1.3 when `plan_parser.py` is
implemented.

Why a separate `test_validate_template.py`:
- Catches Jinja2 template regressions (e.g. missing closing `{% endif %}`)
  before T1.3 lands
- Provides a smoke test that runs in <1s with zero external deps
  beyond `jinja2` (which is already a project dev-dep)
"""
