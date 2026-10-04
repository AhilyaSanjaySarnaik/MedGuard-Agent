from typing import Dict, Any
from app.security.capability import verify_capability_token
from app.security.sanitization import redact_phi_output

# Mock in-memory patient database
MOCK_PATIENT_DB = {
    "PAT-9988": {
        "patient_id": "PAT-9988",
        "name": "Jane Doe",
        "ssn": "000-12-3456",
        "dob": "1985-04-12",
        "diagnosis": "Type 2 Diabetes",
        "assigned_doctor_id": "doc-123"
    }
}

def get_patient_record(capability_token: str, patient_id: str) -> Dict[str, Any]:
    """
    Executes patient record retrieval only if a valid, unexpired capability token is provided.
    """
    # 1. Verify token binding for this tool and resource
    is_valid = verify_capability_token(
        token=capability_token,
        expected_tool="get_patient_record",
        expected_resource=patient_id
    )
    
    if not is_valid:
        raise PermissionError("Invalid, expired, or tampered capability token.")

    # 2. Fetch record
    record = MOCK_PATIENT_DB.get(patient_id)
    if not record:
        return {"error": f"Patient ID {patient_id} not found."}

    # 3. Scrub sensitive fields before returning to agent
    return redact_phi_output(record)