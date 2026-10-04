import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
import app.main as main_module  # Import the module to patch the global risk_manager reference

client = TestClient(app)

def test_execute_tool_success_with_opa_bypass():
    """Verifies that a valid payload succeeds when OPA falls back or passes."""
    payload = {
        "session_id": "session-success-test",  # Unique session avoids 429
        "user": {"user_id": "doc-123", "role": "doctor"},
        "agent": {"agent_id": "agent-007", "role": "clinical_assistant"},
        "patient": {"patient_id": "PAT-9988", "assigned_doctor_id": "doc-123"},
        "tool_name": "get_patient_record",
        "prompt_input": "Retrieve records for PAT-9988",
        "estimated_tokens": 100,
        "arguments": {"patient_id": "PAT-9988"}
    }
    
    response = client.post("/api/v1/gateway/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ALLOWED"
    assert "capability_token" in data
    assert data["result"]["ssn"] == "***-**-****"  # Verifies content is safely masked

def test_execute_tool_forbidden_when_opa_fails(monkeypatch):
    """Verifies that an explicit False response from OPA blocks execution with a 403."""
    import httpx

    class MockResponse:
        status_code = 200
        def json(self):
            return {"result": False}

    async def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    payload = {
        "session_id": "session-opa-block-test",  # Different session isolation
        "user": {"user_id": "unauthorized-user", "role": "guest"},
        "agent": {"agent_id": "agent-007", "role": "clinical_assistant"},
        "patient": {"patient_id": "PAT-9988", "assigned_doctor_id": "doc-123"},
        "tool_name": "get_patient_record",
        "prompt_input": "Get patient details",
        "estimated_tokens": 100,
        "arguments": {"patient_id": "PAT-9988"}
    }

    response = client.post("/api/v1/gateway/execute", json=payload)
    assert response.status_code == 403
    assert "Access Denied" in response.json()["detail"]

def test_gateway_rate_limiting_enforcement(monkeypatch):
    """Verifies that making immediate back-to-back calls triggers a 429 payload drop."""
    session_id = "session-rate-limit-test"
    payload = {
        "session_id": session_id,
        "user": {"user_id": "doc-123", "role": "doctor"},
        "agent": {"agent_id": "agent-007", "role": "clinical_assistant"},
        "patient": {"patient_id": "PAT-9988", "assigned_doctor_id": "doc-123"},
        "tool_name": "get_patient_record",
        "prompt_input": "First fast call",
        "estimated_tokens": 100,
        "arguments": {"patient_id": "PAT-9988"}
    }

    # First call sets the baseline timestamp profile and succeeds
    response1 = client.post("/api/v1/gateway/execute", json=payload)
    assert response1.status_code == 200

    # Mock the global risk_manager object inside app.main to return a False violation match
    class MockRiskManager:
        def evaluate_and_record_usage(self, session_id, estimated_tokens):
            return False, "Rate Limit Exceeded: Velocity anomaly detected (suspected automated loop)."

    monkeypatch.setattr(main_module, "risk_manager", MockRiskManager())

    # Second instant call triggers the velocity violation anomaly drop deterministically
    response2 = client.post("/api/v1/gateway/execute", json=payload)
    assert response2.status_code == 429
    assert "Risk Policy Violation" in response2.json()["detail"]
