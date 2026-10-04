import hmac
import hashlib
import time
import json
from typing import Optional
from pydantic import BaseModel

# Secret key used for signing capability tokens
CAPABILITY_SECRET_KEY = b"medguard-production-capability-secret-key-32bytes"

class CapabilityTokenData(BaseModel):
    user_id: str
    agent_id: str
    tool_name: str
    target_resource_id: str
    expires_at: int
    signature: str

def generate_capability_token(
    user_id: str,
    agent_id: str,
    tool_name: str,
    target_resource_id: str,
    ttl_seconds: int = 30
) -> str:
    """Generates a secure, tamper-proof capability token."""
    expires_at = int(time.time()) + ttl_seconds
    
    # Pack the operational data layout into a deterministic JSON string structure
    payload_dict = {
        "user_id": user_id,
        "agent_id": agent_id,
        "tool_name": tool_name,
        "target_resource_id": target_resource_id,
        "expires_at": expires_at
    }
    payload_json = json.dumps(payload_dict, sort_keys=True)
    
    # Generate cryptographic signature
    signature = hmac.new(
        CAPABILITY_SECRET_KEY,
        payload_json.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    # Combine the data package and cryptographic seal with a safe double-pipe delimiter
    return f"{payload_json}||{signature}"

def verify_capability_token(
    token: str,
    expected_tool: str,
    expected_resource: str
) -> bool:
    """Verifies a capability token signature, structure, and expiration."""
    try:
        # Split payload json text from signature
        if "||" not in token:
            return False
            
        payload_json, signature = token.split("||", 1)
        
        # Load and parse back token layout data
        data = json.loads(payload_json)
        expires_at = int(data["expires_at"])
        
        # 1. Check expiration window
        if time.time() > expires_at:
            return False
            
        # 2. Check access scope restrictions
        if data["tool_name"] != expected_tool or data["target_resource_id"] != expected_resource:
            return False
            
        # 3. Validate signature structure to catch tampering attempts
        recomputed_payload = json.dumps(data, sort_keys=True)
        expected_signature = hmac.new(
            CAPABILITY_SECRET_KEY,
            recomputed_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception:
        # Gracefully handle corrupted strings, missing json properties, or bad types
        return False
