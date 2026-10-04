import pytest
from app.security.capability import generate_capability_token
from app.tools.patient_records import get_patient_record

def test_get_patient_record_with_valid_token():
    token = generate_capability_token(
        user_id="doc-123",
        agent_id="agent-007",
        tool_name="get_patient_record",
        target_resource_id="PAT-9988"
    )
    
    result = get_patient_record(capability_token=token, patient_id="PAT-9988")
    
    assert result["patient_id"] == "PAT-9988"
    assert result["ssn"] == "***-**-****"
    assert result["dob"] == "****-**-**"

def test_get_patient_record_with_invalid_token():
    with pytest.raises(PermissionError, match="Invalid, expired, or tampered capability token"):
        get_patient_record(capability_token="invalid:token:format", patient_id="PAT-9988")