import pytest
import time
import json
from app.security.capability import generate_capability_token, verify_capability_token

def test_valid_capability_token():
    """Verifies that a well-formed token validates successfully."""
    token = generate_capability_token(
        user_id="doc-123",
        agent_id="agent-007",
        tool_name="get_patient_record",
        target_resource_id="PAT-9988",
        ttl_seconds=30
    )
    assert verify_capability_token(token, "get_patient_record", "PAT-9988") is True

def test_tampered_resource_fails():
    """Verifies that scoping requests for different resource targets are rejected."""
    token = generate_capability_token(
        user_id="doc-123",
        agent_id="agent-007",
        tool_name="get_patient_record",
        target_resource_id="PAT-9988"
    )
    assert verify_capability_token(token, "get_patient_record", "PAT-1111") is False

def test_expired_token_fails():
    """Verifies that tokens beyond their TTL boundary are cleanly rejected."""
    # Generate a token that expired 5 seconds ago
    token = generate_capability_token(
        user_id="doc-123",
        agent_id="agent-007",
        tool_name="get_patient_record",
        target_resource_id="PAT-9988",
        ttl_seconds=-5
    )
    assert verify_capability_token(token, "get_patient_record", "PAT-9988") is False

def test_tampered_signature_fails():
    """Verifies that altering the data payload breaks validation."""
    token = generate_capability_token(
        user_id="doc-123",
        agent_id="agent-007",
        tool_name="get_patient_record",
        target_resource_id="PAT-9988"
    )
    
    # Split the token and alter the payload data structure directly
    payload_json, signature = token.split("||", 1)
    data = json.loads(payload_json)
    data["user_id"] = "attacker-666"  # Tamper with the user ID identity
    
    tampered_token = f"{json.dumps(data)}||{signature}"
    assert verify_capability_token(tampered_token, "get_patient_record", "PAT-9988") is False

def test_malformed_token_formats():
    """Verifies that arbitrary or corrupted token structural payloads fail safely."""
    assert verify_capability_token("invalid-token-string", "get_patient_record", "PAT-9988") is False
    assert verify_capability_token("bad_json||fake_signature", "get_patient_record", "PAT-9988") is False
