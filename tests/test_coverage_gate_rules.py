from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_SCRIPT = REPO_ROOT / "scripts" / "check_coverage_gate.py"


def _load_gate_module():
    spec = importlib.util.spec_from_file_location("coverage_gate_rules", GATE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_coverage_gate_ignores_test_files_in_ratio(tmp_path):
    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text(
        """<?xml version=\"1.0\" ?>
<coverage line-rate=\"0.95\">
  <packages>
    <package name=\"pkg\">
      <classes>
        <class name=\"AdminRoutes\" filename=\"admin/routes/orders.py\" line-rate=\"0.70\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
            <line number=\"2\" hits=\"1\"/>
            <line number=\"3\" hits=\"1\"/>
            <line number=\"4\" hits=\"1\"/>
            <line number=\"5\" hits=\"1\"/>
            <line number=\"6\" hits=\"1\"/>
            <line number=\"7\" hits=\"1\"/>
            <line number=\"8\" hits=\"0\"/>
            <line number=\"9\" hits=\"0\"/>
            <line number=\"10\" hits=\"0\"/>
          </lines>
        </class>
        <class name=\"SpecChecker\" filename=\"gaokao-spec-checker/scripts/spec_checker_v2.py\" line-rate=\"1.0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
          </lines>
        </class>
        <class name=\"VisualReport\" filename=\"gaokao-college-advisor/scripts/gaokao_visual_report.py\" line-rate=\"1.0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
          </lines>
        </class>
        <class name=\"AppTests\" filename=\"tests/test_orders.py\" line-rate=\"1.0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
            <line number=\"2\" hits=\"1\"/>
            <line number=\"3\" hits=\"1\"/>
            <line number=\"4\" hits=\"1\"/>
            <line number=\"5\" hits=\"1\"/>
            <line number=\"6\" hits=\"1\"/>
            <line number=\"7\" hits=\"1\"/>
            <line number=\"8\" hits=\"1\"/>
            <line number=\"9\" hits=\"1\"/>
            <line number=\"10\" hits=\"1\"/>
            <line number=\"11\" hits=\"1\"/>
            <line number=\"12\" hits=\"1\"/>
            <line number=\"13\" hits=\"1\"/>
            <line number=\"14\" hits=\"1\"/>
            <line number=\"15\" hits=\"1\"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )

    gate = _load_gate_module()

    assert gate.main([str(GATE_SCRIPT), str(coverage_xml)]) == 1


def test_coverage_gate_ignores_docs_and_admin_tests_in_ratio(tmp_path):
    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text(
        """<?xml version=\"1.0\" ?>
<coverage line-rate=\"1.00\">
  <packages>
    <package name=\"pkg\">
      <classes>
        <class name=\"AdminStats\" filename=\"admin/stats.py\" line-rate=\"0.60\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
            <line number=\"2\" hits=\"1\"/>
            <line number=\"3\" hits=\"1\"/>
            <line number=\"4\" hits=\"1\"/>
            <line number=\"5\" hits=\"1\"/>
            <line number=\"6\" hits=\"1\"/>
            <line number=\"7\" hits=\"0\"/>
            <line number=\"8\" hits=\"0\"/>
            <line number=\"9\" hits=\"0\"/>
            <line number=\"10\" hits=\"0\"/>
          </lines>
        </class>
        <class name=\"SpecChecker\" filename=\"gaokao-spec-checker/scripts/spec_checker_v2.py\" line-rate=\"1.0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
          </lines>
        </class>
        <class name=\"VisualReport\" filename=\"gaokao-college-advisor/scripts/gaokao_visual_report.py\" line-rate=\"1.0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
          </lines>
        </class>
        <class name=\"AdminTests\" filename=\"admin/tests/test_dashboard.py\" line-rate=\"1.0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
            <line number=\"2\" hits=\"1\"/>
            <line number=\"3\" hits=\"1\"/>
            <line number=\"4\" hits=\"1\"/>
            <line number=\"5\" hits=\"1\"/>
            <line number=\"6\" hits=\"1\"/>
            <line number=\"7\" hits=\"1\"/>
            <line number=\"8\" hits=\"1\"/>
          </lines>
        </class>
        <class name=\"PlanDoc\" filename=\"docs/plans/sample_fixture.py\" line-rate=\"1.0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
            <line number=\"2\" hits=\"1\"/>
            <line number=\"3\" hits=\"1\"/>
            <line number=\"4\" hits=\"1\"/>
            <line number=\"5\" hits=\"1\"/>
            <line number=\"6\" hits=\"1\"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )

    gate = _load_gate_module()

    assert gate.main([str(GATE_SCRIPT), str(coverage_xml)]) == 1


def test_coverage_gate_accepts_core_entries_without_workspace_prefix(tmp_path):
    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text(
        """<?xml version=\"1.0\" ?>
<coverage line-rate=\"1.00\">
  <packages>
    <package name=\"pkg\">
      <classes>
        <class name=\"AdminRoutes\" filename=\"admin/routes/orders.py\" line-rate=\"1.0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
          </lines>
        </class>
        <class name=\"SpecChecker\" filename=\"gaokao-spec-checker/scripts/spec_checker_v2.py\" line-rate=\"1.0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
          </lines>
        </class>
        <class name=\"VisualReport\" filename=\"gaokao-college-advisor/scripts/gaokao_visual_report.py\" line-rate=\"1.0\">
          <lines>
            <line number=\"1\" hits=\"1\"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )

    gate = _load_gate_module()

    assert gate.main([str(GATE_SCRIPT), str(coverage_xml)]) == 0
