import pytest
from app.agent.agent import MedGuardAgent
from app.security.capability import generate_capability_token

def test_agent_execution_with_token():
    agent = MedGuardAgent()
    token = generate_capability_token(
        user_id="doc-123",
        agent_id="agent-007",
        tool_name="get_patient_record",
        target_resource_id="PAT-9988"
    )

    response = agent.execute_plan(
        session_id="sess-555",
        user_id="doc-123",
        user_role="doctor",
        patient_id="PAT-9988",
        assigned_doctor_id="doc-123",
        tool_name="get_patient_record",
        user_prompt="Get patient details",
        capability_token=token
    )

    assert response["status"] == "SUCCESS"
    assert response["data"]["patient_id"] == "PAT-9988"
    assert response["data"]["ssn"] == "***-**-****"

def test_agent_execution_without_token_fails():
    agent = MedGuardAgent()
    response = agent.execute_plan(
        session_id="sess-555",
        user_id="doc-123",
        user_role="doctor",
        patient_id="PAT-9988",
        assigned_doctor_id="doc-123",
        tool_name="get_patient_record",
        user_prompt="Get patient details",
        capability_token=None
    )

    assert response["status"] == "DENIED"
    assert "Missing mandatory capability token" in response["error"]