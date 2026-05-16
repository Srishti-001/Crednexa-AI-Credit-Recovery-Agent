"""
Risk score model — CRUD operations for the risk_scores table.
"""

from database.connection import execute_query
from utils.helpers import generate_id
import json


def create_risk_score(client_id: str, risk_score: float, risk_category: str,
                      contributing_factors: dict = None, payment_reliability: float = 1.0,
                      avg_days_overdue: float = 0, total_overdue_count: int = 0) -> str:
    """Create a risk score entry. Returns score_id."""
    score_id = generate_id("RSK")
    factors_json = json.dumps(contributing_factors) if contributing_factors else "{}"
    execute_query(
        """INSERT INTO risk_scores (score_id, client_id, risk_score, risk_category,
           contributing_factors, payment_reliability, avg_days_overdue, total_overdue_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (score_id, client_id, risk_score, risk_category, factors_json,
         payment_reliability, avg_days_overdue, total_overdue_count),
        fetch="none"
    )
    return score_id


def get_latest_risk_score(client_id: str) -> dict:
    """Get the most recent risk score for a client."""
    result = execute_query(
        """SELECT * FROM risk_scores WHERE client_id = ?
           ORDER BY calculated_at DESC LIMIT 1""",
        (client_id,), fetch="one"
    )
    if result and result.get("contributing_factors"):
        try:
            result["contributing_factors"] = json.loads(result["contributing_factors"])
        except json.JSONDecodeError:
            result["contributing_factors"] = {}
    return result


def get_risk_history(client_id: str, limit: int = 10) -> list:
    """Get risk score history for a client."""
    return execute_query(
        "SELECT * FROM risk_scores WHERE client_id = ? ORDER BY calculated_at DESC LIMIT ?",
        (client_id, limit)
    )


def get_all_latest_risk_scores() -> list:
    """Get the latest risk score for each client."""
    return execute_query(
        """SELECT rs.*, c.company_name, c.contact_email, c.total_outstanding
           FROM risk_scores rs
           JOIN clients c ON rs.client_id = c.client_id
           WHERE rs.calculated_at = (
               SELECT MAX(rs2.calculated_at) FROM risk_scores rs2
               WHERE rs2.client_id = rs.client_id
           )
           ORDER BY rs.risk_score DESC"""
    )


def get_risk_distribution() -> list:
    """Get count of clients in each risk category."""
    return execute_query(
        """SELECT risk_category, COUNT(DISTINCT client_id) as count
           FROM risk_scores rs
           WHERE rs.calculated_at = (
               SELECT MAX(rs2.calculated_at) FROM risk_scores rs2
               WHERE rs2.client_id = rs.client_id
           )
           GROUP BY risk_category
           ORDER BY CASE risk_category
               WHEN 'Critical' THEN 1 WHEN 'High' THEN 2
               WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 END"""
    )
