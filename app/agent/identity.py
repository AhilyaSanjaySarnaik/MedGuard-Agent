from typing import Optional
from app.entities import UserIdentity, AgentIdentity, PatientContext

class IdentityValidator:
    @staticmethod
    def is_doctor_assigned_to_patient(user: UserIdentity, patient: PatientContext) -> bool:
        """
        Validates if the requesting doctor matches the assigned physician on the patient record.
        """
        if user.role == "doctor" and user.user_id == patient.assigned_doctor_id:
            return True
        return False

    @staticmethod
    def validate_agent_role(agent: AgentIdentity) -> bool:
        """
        Verifies that the agent has a recognized system role.
        """
        allowed_roles = {"clinical_assistant", "triage_bot", "admin_agent"}
        return agent.role in allowed_roles

identity_validator = IdentityValidator()