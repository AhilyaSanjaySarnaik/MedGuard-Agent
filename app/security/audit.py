import logging
import json
import time
from typing import Dict, Any, Optional

# Configure structured JSON logger
logger = logging.getLogger("medguard.audit")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class AuditLogger:
    @staticmethod
    def log_event(
        event_type: str,
        session_id: str,
        user_id: str,
        agent_id: str,
        tool_name: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Emits a structured JSON audit log entry for security and compliance tracking.
        """
        audit_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "session_id": session_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "status": status,
            "details": details or {}
        }
        
        logger.info(json.dumps(audit_entry))
        return audit_entry

audit_logger = AuditLogger()