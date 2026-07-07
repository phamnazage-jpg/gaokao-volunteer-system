from scripts.check_llm_domain_data_coverage import main


def test_llm_domain_data_coverage_gate_passes() -> None:
    assert main() == 0
