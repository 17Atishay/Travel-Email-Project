"""
Enterprise audit logging and observability for Finance Collections AI.
"""

import os
import json
import logging
from datetime import datetime

def setup_logger():
    """Initializes and returns a standard Python logger."""
    logger = logging.getLogger("collections_agent")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def log_audit_event(
    invoice_id: str,
    client_name: str,
    stage: str,
    tone: str,
    risk_level: str,
    approval_status: str,
    reviewer_comment: str,
    send_status: str = "Dry Run - Simulated"
):
    """
    Logs structured audit data to logs/audit_log.json for compliance.
    """
    os.makedirs("logs", exist_ok=True)
    file_path = os.path.join("logs", "audit_log.json")
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "invoice_number": invoice_id,
        "client_name": client_name,
        "escalation_stage": stage,
        "tone_used": tone,
        "risk_level": risk_level,
        "approval_status": approval_status,
        "reviewer_comment": reviewer_comment,
        "send_status": send_status
    }
    
    audit_logs = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    audit_logs = json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            logging.getLogger("collections_agent").error(f"Error reading audit log: {e}")
            
    audit_logs.append(event)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(audit_logs, f, indent=4)
    except IOError as e:
        logging.getLogger("collections_agent").error(f"Error writing to audit log: {e}")
