"""
Recovery strategy model — CRUD operations for the recovery_strategies table.
"""

from database.connection import execute_query
from utils.helpers import generate_id
from datetime import datetime
import json


def create_strategy(client_id: str, strategy_type: str, description: str,
                    recommended_actions: list = None, priority: str = "Medium",
                    ai_reasoning: str = "") -> str:
    """Create a new recovery strategy. Returns strategy_id."""
    strategy_id = generate_id("STR")
    actions_json = json.dumps(recommended_actions) if recommended_actions else "[]"
    execute_query(
        """INSERT INTO recovery_strategies (strategy_id, client_id, strategy_type,
           description, recommended_actions, priority, ai_reasoning)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (strategy_id, client_id, strategy_type, description, actions_json, priority, ai_reasoning),
        fetch="none"
    )
    return strategy_id


def get_strategy(strategy_id: str) -> dict:
    """Get a single strategy by ID."""
    result = execute_query(
        "SELECT * FROM recovery_strategies WHERE strategy_id = ?",
        (strategy_id,), fetch="one"
    )
    if result and result.get("recommended_actions"):
        try:
            result["recommended_actions"] = json.loads(result["recommended_actions"])
        except json.JSONDecodeError:
            result["recommended_actions"] = []
    return result


def get_strategies_by_client(client_id: str) -> list:
    """Get all strategies for a client."""
    results = execute_query(
        "SELECT * FROM recovery_strategies WHERE client_id = ? ORDER BY created_at DESC",
        (client_id,)
    )
    for r in results:
        if r.get("recommended_actions"):
            try:
                r["recommended_actions"] = json.loads(r["recommended_actions"])
            except json.JSONDecodeError:
                r["recommended_actions"] = []
    return results


def get_active_strategies() -> list:
    """Get all active strategies with client info."""
    return execute_query(
        """SELECT rs.*, c.company_name, c.contact_email
           FROM recovery_strategies rs JOIN clients c ON rs.client_id = c.client_id
           WHERE rs.status IN ('Proposed', 'Active')
           ORDER BY CASE rs.priority
               WHEN 'Critical' THEN 1
               WHEN 'High' THEN 2
               WHEN 'Medium' THEN 3
               WHEN 'Low' THEN 4
           END"""
    )


def update_strategy_status(strategy_id: str, status: str) -> None:
    """Update strategy status."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query(
        "UPDATE recovery_strategies SET status = ?, updated_at = ? WHERE strategy_id = ?",
        (status, now, strategy_id), fetch="none"
    )
