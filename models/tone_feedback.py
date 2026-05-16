"""
Tone feedback model — CRUD for the self-learning tone optimization system.
"""

from database.connection import execute_query
from utils.helpers import generate_id


def create_feedback(email_id: str, tone_used: str, client_response: str = "",
                    detected_outcome: str = "No Response", effectiveness_score: float = 0.5,
                    notes: str = "") -> str:
    """Record tone feedback after email interaction. Returns feedback_id."""
    feedback_id = generate_id("TFB")
    execute_query(
        """INSERT INTO tone_feedback (feedback_id, email_id, tone_used, client_response,
           detected_outcome, effectiveness_score, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (feedback_id, email_id, tone_used, client_response, detected_outcome,
         effectiveness_score, notes),
        fetch="none"
    )
    return feedback_id


def get_feedback_by_email(email_id: str) -> dict:
    """Get feedback for a specific email."""
    return execute_query(
        "SELECT * FROM tone_feedback WHERE email_id = ?", (email_id,), fetch="one"
    )


def get_tone_effectiveness(tone: str = None) -> list:
    """Get average effectiveness for each tone (or a specific tone)."""
    if tone:
        return execute_query(
            """SELECT tone_used, AVG(effectiveness_score) as avg_score,
                      COUNT(*) as sample_size
               FROM tone_feedback WHERE tone_used = ? GROUP BY tone_used""",
            (tone,)
        )
    return execute_query(
        """SELECT tone_used, AVG(effectiveness_score) as avg_score,
                  COUNT(*) as sample_size
           FROM tone_feedback GROUP BY tone_used ORDER BY avg_score DESC"""
    )


def get_client_tone_history(client_id: str) -> list:
    """Get tone effectiveness history for a client's emails."""
    return execute_query(
        """SELECT tf.*, el.client_id, el.tone, el.subject
           FROM tone_feedback tf
           JOIN email_logs el ON tf.email_id = el.email_id
           WHERE el.client_id = ?
           ORDER BY tf.created_at DESC""",
        (client_id,)
    )


def get_best_tone_for_client(client_id: str) -> str:
    """Determine the best-performing tone for a client based on historical data."""
    result = execute_query(
        """SELECT tf.tone_used, AVG(tf.effectiveness_score) as avg_score
           FROM tone_feedback tf
           JOIN email_logs el ON tf.email_id = el.email_id
           WHERE el.client_id = ?
           GROUP BY tf.tone_used
           HAVING COUNT(*) >= 1
           ORDER BY avg_score DESC
           LIMIT 1""",
        (client_id,), fetch="one"
    )
    return result["tone_used"] if result else None


def get_outcome_distribution() -> list:
    """Get distribution of outcomes across all tone feedback."""
    return execute_query(
        """SELECT detected_outcome, COUNT(*) as count
           FROM tone_feedback GROUP BY detected_outcome ORDER BY count DESC"""
    )
