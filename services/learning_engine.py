"""
Learning Engine — Self-learning tone optimisation.
──────────────────────────────────────────────────────────────
Tracks which tone (Friendly / Professional / Firm / Urgent / Legal)
produces the best client response for each client, and uses that
history to override the default rules-based escalation.

Core loop:
  1. Email is sent with a tone  →  stored in email_logs
  2. Client responds             →  sentiment analysed
  3. Outcome recorded            →  tone_feedback row created
  4. Next email for same client  →  engine picks the historically
                                     best-performing tone for them
"""

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

import config
from database.connection import init_db
from models.tone_feedback import (
    create_feedback,
    get_tone_effectiveness,
    get_client_tone_history,
    get_best_tone_for_client,
    get_outcome_distribution,
)
from models.email_log import get_email_log
from services.sentiment_analysis import analyse_sentiment
from utils.helpers import get_tone_for_days


# ════════════════════════════════════════════════════════════════════════
# 1.  DETERMINE OPTIMAL TONE — the main entry-point used by email_gen
# ════════════════════════════════════════════════════════════════════════

def determine_optimal_tone(client_id: str, overdue_days: int) -> dict:
    """
    Pick the best tone for a follow-up email.

    Priority:
      1. If we have ≥ 2 feedback records for this client → use the
         historically best-performing tone (self-learning override).
      2. Otherwise → fall back to the rules-based escalation.

    Returns
    -------
    {
      "tone":   str,      e.g. "Firm"
      "level":  int,      1-5
      "source": str       "Self-Learning" | "Rules Engine"
    }
    """
    init_db()

    # ── check client history ──
    history = get_client_tone_history(client_id)
    if len(history) >= 2:
        best_tone = get_best_tone_for_client(client_id)
        if best_tone:
            level = _tone_name_to_level(best_tone)
            return {
                "tone": best_tone,
                "level": level,
                "source": "Self-Learning",
            }

    # ── rules-based fallback ──
    level, tone_name = get_tone_for_days(overdue_days)
    return {
        "tone": tone_name,
        "level": level,
        "source": "Rules Engine",
    }


# ════════════════════════════════════════════════════════════════════════
# 2.  RECORD FEEDBACK — called after a client responds to an email
# ════════════════════════════════════════════════════════════════════════

def record_tone_outcome(
    email_id: str,
    client_response: str = "",
    manual_outcome: str | None = None,
    manual_score: float | None = None,
) -> dict:
    """
    Record how effective a sent email's tone was.

    If *client_response* is provided, sentiment is auto-detected.
    If *manual_outcome* / *manual_score* are given they take priority.

    Outcome categories: Positive | Neutral | Negative | No Response

    Returns the feedback record dict.
    """
    init_db()
    email = get_email_log(email_id)
    if not email:
        return {"success": False, "error": "Email not found"}

    tone_used = email.get("tone", "Professional")

    # ── detect outcome ──
    if manual_outcome:
        outcome = manual_outcome
        score   = manual_score if manual_score is not None else _outcome_to_score(manual_outcome)
    elif client_response:
        sentiment = analyse_sentiment(client_response)
        outcome   = _emotion_to_outcome(sentiment["emotion"])
        score     = _outcome_to_score(outcome)
    else:
        outcome = "No Response"
        score   = 0.3  # low but non-zero

    feedback_id = create_feedback(
        email_id=email_id,
        tone_used=tone_used,
        client_response=client_response,
        detected_outcome=outcome,
        effectiveness_score=score,
    )

    return {
        "success": True,
        "feedback_id": feedback_id,
        "tone_used": tone_used,
        "outcome": outcome,
        "score": score,
    }


# ════════════════════════════════════════════════════════════════════════
# 3.  ANALYTICS — aggregate tone effectiveness
# ════════════════════════════════════════════════════════════════════════

def get_tone_performance_report() -> dict:
    """
    Return { tones: [{tone, avg_score, sample_size}], outcomes: [...] }
    """
    init_db()
    tones    = get_tone_effectiveness()
    outcomes = get_outcome_distribution()
    return {"tones": tones, "outcomes": outcomes}


def get_client_learning_data(client_id: str) -> dict:
    """
    Return tone history and current recommendation for one client.
    """
    init_db()
    history   = get_client_tone_history(client_id)
    best_tone = get_best_tone_for_client(client_id)
    return {
        "history": history,
        "recommended_tone": best_tone,
        "data_points": len(history),
    }


# ════════════════════════════════════════════════════════════════════════
# 4.  HELPERS
# ════════════════════════════════════════════════════════════════════════

_TONE_LEVEL_MAP = {
    "Friendly": 1, "Professional": 2, "Firm": 3,
    "Urgent": 4, "Legal": 5,
}

_LEVEL_TONE_MAP = {v: k for k, v in _TONE_LEVEL_MAP.items()}


def _tone_name_to_level(name: str) -> int:
    return _TONE_LEVEL_MAP.get(name, 2)


def _outcome_to_score(outcome: str) -> float:
    """Map qualitative outcome to a 0-1 effectiveness score."""
    return {
        "Positive":    0.9,
        "Neutral":     0.5,
        "Negative":    0.2,
        "No Response": 0.3,
    }.get(outcome, 0.5)


def _emotion_to_outcome(emotion: str) -> str:
    """Map sentiment emotion to an outcome label."""
    return {
        "Happy":       "Positive",
        "Cooperative":  "Positive",
        "Neutral":      "Neutral",
        "Frustrated":   "Negative",
        "Angry":        "Negative",
        "Desperate":    "Neutral",
    }.get(emotion, "Neutral")


def get_all_tones() -> list[dict]:
    """Return the available tones for the UI dropdowns."""
    return [
        {"tone": name, "level": level, "emoji": _emoji(name)}
        for name, level in _TONE_LEVEL_MAP.items()
    ]


def _emoji(tone: str) -> str:
    return {
        "Friendly": "😊", "Professional": "💼", "Firm": "✊",
        "Urgent": "🚨", "Legal": "⚖️",
    }.get(tone, "📧")
