import pytest
from app.security.audit import audit_logger

def test_audit_log_structure():
    entry = audit_logger.log_event(
        event_type="TOOL_EXECUTION_ATTEMPT",
        session_id="sess-100",
        user_id="doc-123",
        agent_id="agent-007",
        tool_name="get_patient_record",
        status="ALLOWED",
        details={"prompt_sanitized": True}
    )
    
    assert entry["event_type"] == "TOOL_EXECUTION_ATTEMPT"
    assert entry["session_id"] == "sess-100"
    assert entry["status"] == "ALLOWED"
    assert entry["details"]["prompt_sanitized"] is True
    assert "timestamp" in entry