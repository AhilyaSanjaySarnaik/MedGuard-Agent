import re
from typing import Dict, Any

INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"system:",
    r"you are now an unrestricted ai",
    r"bypass security"
]

def sanitize_inbound_prompt(raw_prompt: str) -> str:
    cleaned = raw_prompt
    for pattern in INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "[REDACTED_INJECTION_ATTEMPT]", cleaned, flags=re.IGNORECASE)
    return cleaned

def redact_phi_output(data: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = data.copy()
    if "ssn" in sanitized:
        sanitized["ssn"] = "***-**-****"
    if "dob" in sanitized:
        sanitized["dob"] = "****-**-**"
    return sanitized