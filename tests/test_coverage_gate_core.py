import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_CHECKER_PATH = (
    REPO_ROOT / "skills" / "gaokao-spec-checker" / "scripts" / "spec_checker_v2.py"
)
VISUAL_REPORT_PATH = (
    REPO_ROOT
    / "skills"
    / "gaokao-college-advisor"
    / "scripts"
    / "gaokao_visual_report.py"
)


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


spec_checker = _load_module("spec_checker_v2_coverage", SPEC_CHECKER_PATH)
visual_report = _load_module("gaokao_visual_report_coverage", VISUAL_REPORT_PATH)


GaokaoSpecCheckerV2 = spec_checker.GaokaoSpecCheckerV2


def test_detect_province_alias_branch():
    assert spec_checker.detect_province("湘考生，578分，志愿方案") == "湖南"


def test_report_unsupported_province_branch():
    checker = GaokaoSpecCheckerV2(province="火星")
    report = checker.auto_detect_and_check("火星考生志愿方案")
    assert "暂不支持 火星" in report


def test_checker_hits_core_warning_and_validation_branches():
    checker = GaokaoSpecCheckerV2(province="湖南")
    report = checker.auto_detect_and_check(
        "\n".join(
            [
                "湖南2026高考志愿填报方案",
                "本次共填报20个院校专业组志愿。",
                "每组最多6个专业。",
                "全部专业服从调剂。",
                "会计专业普遍要求物化生。",
                "88%录取概率。",
                "2026年位次预计5000名。",
                "请关注退档风险。",
            ]
        )
    )
    assert "调剂范围错误（湖南）" in report
    assert "主观概率估算" in report
    assert "2026年位次" in report
    assert "选科要求一刀切" in report


def test_checker_hits_professional_school_mode_error():
    checker = GaokaoSpecCheckerV2(province="浙江")
    report = checker.auto_detect_and_check(
        "\n".join(
            [
                "浙江省630分志愿方案",
                "本次共填报80个专业+学校志愿。",
                "每个志愿填1个专业。",
                "仍保留专业组概念，并支持组内调剂。",
                "风险提示：注意退档风险。",
            ]
        )
    )
    assert "模式错误（浙江）" in report


def test_checker_can_generate_clean_report():
    checker = GaokaoSpecCheckerV2(province="浙江")
    report = checker.auto_detect_and_check(
        "\n".join(
            [
                "浙江省630分志愿方案",
                "本次共填报80个专业+学校志愿。",
                "每个志愿填1个专业。",
                "无调剂。",
                "风险提示：注意退档与体检限制。",
            ]
        )
    )
    assert "方案基本合规" in report
    assert "问题总数：0 个" in report


def test_visual_report_usage_message(capsys, monkeypatch):
    monkeypatch.setattr(visual_report.sys, "argv", ["gaokao_visual_report.py"])
    with pytest.raises(SystemExit) as exc:
        visual_report.main()
    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "用法: python3 gaokao_visual_report.py <student_data.json>" in output
    assert "生成示例" in output


def test_visual_report_demo_mode(capsys, monkeypatch):
    monkeypatch.setattr(
        visual_report,
        "generate_visual_report",
        lambda student, volunteers, output_format="all": ["/tmp/demo.md"],
    )
    monkeypatch.setattr(
        visual_report.sys, "argv", ["gaokao_visual_report.py", "--demo"]
    )

    visual_report.main()

    output = capsys.readouterr().out
    assert "生成完成" in output
    assert "/tmp/demo.md" in output


def test_visual_report_json_input(tmp_path, capsys, monkeypatch):
    payload = {
        "student": {"name": "张三", "province": "浙江省", "score": 620},
        "volunteers": [{"school": "浙江大学", "major": "计算机类"}],
    }
    data_path = tmp_path / "student.json"
    data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    observed: dict[str, object] = {}

    def fake_generate(student, volunteers, output_format="all"):
        observed["student"] = student
        observed["volunteers"] = volunteers
        observed["output_format"] = output_format
        return ["/tmp/from-json.html"]

    monkeypatch.setattr(visual_report, "generate_visual_report", fake_generate)
    monkeypatch.setattr(
        visual_report.sys, "argv", ["gaokao_visual_report.py", str(data_path)]
    )

    visual_report.main()

    assert observed["student"] == payload["student"]
    assert observed["volunteers"] == payload["volunteers"]
    assert observed["output_format"] == "all"
    output = capsys.readouterr().out
    assert "/tmp/from-json.html" in output
