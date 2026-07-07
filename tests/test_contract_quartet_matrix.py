from pathlib import Path


def test_contract_quartet_matrix_covers_required_contracts() -> None:
    text = Path("docs/CONTRACT_QUARTET_MATRIX_2026-07-07.md").read_text(encoding="utf-8")
    required = [
        "POST /api/auth/login",
        "GET /api/admin/stats/dashboard",
        "POST /api/public/orders",
        "POST /api/public/payments/alipay/notify",
        "GET /portal/{token}/cwb",
        "GET /portal/{token}/full-plan",
        "GET /api/llm/config",
        "POST /api/llm/{provider}/enhance",
    ]
    for contract in required:
        assert contract in text
