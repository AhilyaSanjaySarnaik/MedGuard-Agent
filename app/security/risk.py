import time
from typing import Dict
from pydantic import BaseModel

class SessionRiskProfile(BaseModel):
    max_token_budget: int = 5000
    consumed_tokens: int = 0
    max_tool_calls: int = 10
    tool_call_count: int = 0
    last_call_timestamp: float = 0.0
    min_call_interval_seconds: float = 0.5  # Prevents rapid automated tool looping

class RiskManager:
    def __init__(self):
        # In-memory store for session profiles; use Redis for production scale
        self._sessions: Dict[str, SessionRiskProfile] = {}

    def get_or_create_session(self, session_id: str) -> SessionRiskProfile:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionRiskProfile()
        return self._sessions[session_id]

    def evaluate_and_record_usage(
        self, session_id: str, estimated_tokens: int
    ) -> tuple[bool, str]:
        profile = self.get_or_create_session(session_id)
        now = time.time()

        # 1. Rate check: Prevent high-velocity automated loops
        if profile.last_call_timestamp > 0:
            elapsed = now - profile.last_call_timestamp
            # Enforces that sub-millisecond duplicate ticks (elapsed == 0.0) are blocked safely
            if 0.0 <= elapsed < profile.min_call_interval_seconds:
                return False, "Rate Limit Exceeded: Velocity anomaly detected (suspected automated loop)."

        # 2. Call count check: Prevent runaway tool execution
        if profile.tool_call_count >= profile.max_tool_calls:
            return False, f"Execution Limit Exceeded: Session reached maximum tool calls ({profile.max_tool_calls})."

        # 3. Token budget check: Prevent exhaustion/cost inflation
        if profile.consumed_tokens + estimated_tokens > profile.max_token_budget:
            return False, f"Token Budget Exceeded: Remaining budget is {profile.max_token_budget - profile.consumed_tokens} tokens."

        # Update profile if all checks pass
        profile.consumed_tokens += estimated_tokens
        profile.tool_call_count += 1
        profile.last_call_timestamp = now

        return True, "ALLOWED"

# Global singleton instance for the gateway
risk_manager = RiskManager()
