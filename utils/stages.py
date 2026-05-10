"""
Logic for determining escalation stages based on invoice overdue days.
"""
from typing import Tuple

def calculate_escalation_stage(days_overdue: int) -> Tuple[str, str]:
    """
    Determines the collection stage and tone based on the number of days an invoice is overdue.
    
    Args:
        days_overdue (int): Number of days past the due date.
        
    Returns:
        Tuple[str, str]: The escalation stage and the recommended tone.
    """
    try:
        if days_overdue < 1:
            return "Current", "Friendly"
        elif 1 <= days_overdue <= 7:
            return "1st Follow-Up", "Warm & Friendly"
        elif 8 <= days_overdue <= 14:
            return "2nd Follow-Up", "Polite but Firm"
        elif 15 <= days_overdue <= 21:
            return "3rd Follow-Up", "Formal & Serious"
        elif 22 <= days_overdue <= 30:
            return "4th Follow-Up", "Stern & Urgent"
        else:
            return "Escalation Flag", "Flag for Legal"
    except Exception as e:
        return "Unknown", "Unknown"
