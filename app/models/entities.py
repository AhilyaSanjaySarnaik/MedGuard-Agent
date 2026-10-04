from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class UserIdentity(BaseModel):
    user_id: str = Field(..., example="doc-123")
    role: str = Field(..., example="doctor")

class AgentIdentity(BaseModel):
    agent_id: str = Field(..., example="agent-007")
    role: str = Field(..., example="clinical_assistant")

class PatientContext(BaseModel):
    patient_id: str = Field(..., example="PAT-9988")
    assigned_doctor_id: str = Field(..., example="doc-123")

class ToolExecutionRequest(BaseModel):
    session_id: str = Field(default="default-session", example="sess-100")
    user: UserIdentity
    agent: AgentIdentity
    patient: PatientContext
    tool_name: str = Field(..., example="get_patient_record")
    prompt_input: str = Field(..., example="Fetch patient records for evaluation")
    estimated_tokens: int = Field(default=100, ge=1)
    arguments: Dict[str, Any] = Field(default_factory=dict)