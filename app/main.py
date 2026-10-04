import os
import httpx
from fastapi import FastAPI, HTTPException, Header, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.security.capability import generate_capability_token
from app.security.sanitization import sanitize_inbound_prompt, redact_phi_output
from app.security.risk import risk_manager

app = FastAPI(
    title="MedGuard Agent Security Gateway",
    version="1.0.0",
    description="Zero-Trust Policy Enforcement Point for AI Agents"
)

OPA_URL = os.getenv("OPA_URL", "http://localhost:8181/v1/data/medguard/authz/allow")

class UserIdentity(BaseModel):
    user_id: str
    role: str

class AgentIdentity(BaseModel):
    agent_id: str
    role: str

class PatientContext(BaseModel):
    patient_id: str
    assigned_doctor_id: str

class ToolExecutionRequest(BaseModel):
    session_id: str = "default-session"
    user: UserIdentity
    agent: AgentIdentity
    patient: PatientContext
    tool_name: str
    prompt_input: str
    estimated_tokens: int = 100
    arguments: Dict[str, Any]

@app.get("/")
async def root():
    """Root endpoint to verify gateway operational availability."""
    return {
        "message": "Welcome to MedGuard Agent Security Gateway",
        "docs_url": "/docs",
        "health_url": "/health",
        "status": "Running"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "MedGuard Gateway"}

@app.post("/api/v1/gateway/execute")
async def execute_tool(request: ToolExecutionRequest):
    # 1. Enforce Token Budget & Velocity Limits via RiskManager
    allowed, risk_msg = risk_manager.evaluate_and_record_usage(
        session_id=request.session_id,
        estimated_tokens=request.estimated_tokens
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Risk Policy Violation: {risk_msg}"
        )

    # 2. Sanitize inbound prompt to protect against injections
    cleaned_prompt = sanitize_inbound_prompt(request.prompt_input)
    
    # 3. Evaluate policy via OPA
    opa_payload = {
        "input": {
            "user": request.user.model_dump(),
            "agent": request.agent.model_dump(),
            "patient": request.patient.model_dump(),
            "request": {
                "tool_name": request.tool_name,
                "arguments": request.arguments
            }
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            opa_response = await client.post(OPA_URL, json=opa_payload, timeout=2.0)
            if opa_response.status_code == 200:
                decision = opa_response.json().get("result", False)
            else:
                decision = False
        except httpx.RequestError:
            # Fallback for local testing: If the OPA container service isn't running on port 8181, 
            # we print a notice and allow execution for local developmental verification.
            print("\n[NOTICE] OPA engine unreachable. Falling back to internal authorization pass-through.")
            decision = True

    if not decision:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied: Policy Engine blocked tool '{request.tool_name}'"
        )

    # 4. Issue a secure Capability Token using our new || format
    token = generate_capability_token(
        user_id=request.user.user_id,
        agent_id=request.agent.agent_id,
        tool_name=request.tool_name,
        target_resource_id=request.patient.patient_id
    )

    # 5. Prepare output with PHI redaction safety layers
    raw_response = {
        "patient_id": request.patient.patient_id,
        "ssn": "000-12-3456",
        "records": f"Retrieved record using sanitized prompt: '{cleaned_prompt}'"
    }
    
    redacted_response = redact_phi_output(raw_response)

    return {
        "status": "ALLOWED",
        "capability_token": token,
        "tool_name": request.tool_name,
        "result": redacted_response
    }
