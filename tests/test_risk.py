import time
import pytest
from app.security.risk import RiskManager

def test_token_budget_limit():
    rm = RiskManager()
    session_id = "sess-001"

    # Consumes 4000 tokens out of 5000
    allowed, msg = rm.evaluate_and_record_usage(session_id, 4000)
    assert allowed is True

    # Sleep 0.6 seconds to satisfy the min_call_interval_seconds threshold
    time.sleep(0.6)

    # Exceeds budget (4000 + 1500 > 5000)
    allowed, msg = rm.evaluate_and_record_usage(session_id, 1500)
    assert allowed is False
    assert "Token Budget Exceeded" in msg

def test_tool_call_limit():
    rm = RiskManager()
    session_id = "sess-002"

    for _ in range(10):
        time.sleep(0.6)  # Avoid velocity limit
        allowed, _ = rm.evaluate_and_record_usage(session_id, 100)
        assert allowed is True

    # 11th call should fail
    time.sleep(0.6)
    allowed, msg = rm.evaluate_and_record_usage(session_id, 100)
    assert allowed is False
    assert "Execution Limit Exceeded" in msg
