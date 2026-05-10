"""
Logic for AI-inspired payment risk scoring.
"""
from typing import Tuple

def calculate_risk_score(days_overdue: int, amount_due: float, follow_up_count: int) -> Tuple[str, str]:
    """
    Calculates the payment risk score and generates a reasoning statement based on multiple factors.
    
    Args:
        days_overdue (int): Number of days the invoice is overdue.
        amount_due (float): Total amount due for the invoice.
        follow_up_count (int): Number of follow-ups previously sent.
        
    Returns:
        Tuple[str, str]: Risk level (Low Risk, Medium Risk, High Risk) and the reasoning statement.
    """
    try:
        # Simple risk heuristic
        if days_overdue >= 30 or (days_overdue >= 15 and amount_due > 10000):
            risk_level = "High Risk"
        elif days_overdue >= 15 or (days_overdue >= 8 and amount_due > 5000) or follow_up_count >= 2:
            risk_level = "Medium Risk"
        else:
            risk_level = "Low Risk"
            
        # Reasoning Generation
        reasons = []
        if risk_level == "High Risk":
            reasons.append(f"invoice is overdue for {days_overdue} days")
            if amount_due > 10000:
                reasons.append(f"amount due (${amount_due:,.2f}) is exceptionally high")
            if follow_up_count >= 3:
                reasons.append("multiple reminders have already been sent")
        elif risk_level == "Medium Risk":
            reasons.append(f"invoice is overdue for {days_overdue} days")
            if amount_due > 5000:
                reasons.append(f"amount due (${amount_due:,.2f}) is substantial")
            if follow_up_count >= 2:
                reasons.append("several reminders have been sent")
        else:
            reasons.append(f"invoice is only {days_overdue} days overdue")
            reasons.append("amount and history do not indicate significant risk")
            
        reasoning = f"{risk_level} because " + " and ".join(reasons) + "."
        return risk_level, reasoning
        
    except Exception as e:
        return "Unknown", f"Error calculating risk: {str(e)}"
