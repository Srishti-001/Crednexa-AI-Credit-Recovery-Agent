"""
Sentiment Analysis — Client emotion and intent detection.
──────────────────────────────────────────────────────────────
Uses Gemini / OpenAI to detect the emotion and intent behind
a client's email or message.  Falls back to keyword heuristics
if no AI key is configured.

Output format:
  { emotion, confidence, intent, reasoning }
"""

import re

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

import config
from ai import gemini_client, openai_client
from ai.response_parser import extract_emotion_data


# ════════════════════════════════════════════════════════════════════════
# PROMPT
# ════════════════════════════════════════════════════════════════════════

_EMOTION_PROMPT = """You are a world-class sentiment analysis model specialised
in business-to-business credit recovery communications.

Analyse the following CLIENT RESPONSE and determine:
1. **emotion** — one of: Happy, Cooperative, Neutral, Frustrated, Angry, Desperate
2. **confidence** — 0.0 to 1.0
3. **intent** — one of: Will Pay, Negotiating, Stalling, Disputing, Ignoring, Refusing
4. **reasoning** — one sentence explaining your classification

CLIENT RESPONSE:
\"\"\"
{text}
\"\"\"

Respond ONLY with valid JSON:
{{
  "emotion": "...",
  "confidence": 0.0,
  "intent": "...",
  "reasoning": "..."
}}"""


# ════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ════════════════════════════════════════════════════════════════════════

def analyse_sentiment(text: str) -> dict:
    """
    Analyse a piece of client text (email reply, SMS, note).

    Returns
    -------
    {
      "emotion":    str,
      "confidence": float 0-1,
      "intent":     str,
      "reasoning":  str,
      "model":      str       ← which provider was used
    }
    """
    if not text or not text.strip():
        return {
            "emotion": "Neutral", "confidence": 0.0,
            "intent": "Unknown", "reasoning": "No text provided.",
            "model": "N/A",
        }

    prompt = _EMOTION_PROMPT.format(text=text.strip())

    # ── try AI providers ──
    try:
        if config.AI_PROVIDER == "gemini" and gemini_client.is_configured():
            raw = gemini_client.analyze_emotion(prompt)
            data = extract_emotion_data(raw)
            data["model"] = f"Gemini ({config.GEMINI_MODEL})"
            return data

        elif openai_client.is_configured():
            raw = openai_client.analyze_emotion(prompt)
            data = extract_emotion_data(raw)
            data["model"] = f"OpenAI ({config.OPENAI_MODEL})"
            return data

    except Exception as exc:
        logger.warning(f"AI sentiment analysis failed, using keyword fallback: {exc}")

    # ── keyword fallback ──
    result = _keyword_analysis(text)
    result["model"] = "Keyword Heuristics"
    return result


# ════════════════════════════════════════════════════════════════════════
# KEYWORD FALLBACK
# ════════════════════════════════════════════════════════════════════════

# compiled once at import time
_PATTERNS: dict[str, list[re.Pattern]] = {
    "Angry": [
        re.compile(r, re.I)
        for r in [
            r"\b(unacceptable|outrageous|furious|disgusted|fed up|worst|terrible)\b",
            r"\b(legal action|lawyer|court|sue|complain)\b",
            r"\b(never again|done with|fraud|cheat|scam)\b",
        ]
    ],
    "Frustrated": [
        re.compile(r, re.I)
        for r in [
            r"\b(frustrated|annoyed|disappointed|irritated|upset|tired of)\b",
            r"\b(why|how many times|again|still waiting|not resolved)\b",
            r"\b(bad experience|poor service|delays|no response)\b",
        ]
    ],
    "Desperate": [
        re.compile(r, re.I)
        for r in [
            r"\b(please help|urgent|desperate|struggling|can't afford)\b",
            r"\b(last chance|no money|financial difficulty|hardship)\b",
            r"\b(beg|mercy|somehow|extension|survive)\b",
        ]
    ],
    "Cooperative": [
        re.compile(r, re.I)
        for r in [
            r"\b(will pay|arrange payment|working on it|transfer soon)\b",
            r"\b(agree|accept|understand|committed|plan to)\b",
            r"\b(installment|partial payment|schedule|sort this out)\b",
        ]
    ],
    "Happy": [
        re.compile(r, re.I)
        for r in [
            r"\b(thank you|thanks|great|excellent|satisfied|happy)\b",
            r"\b(paid|cleared|settled|resolved|appreciate)\b",
        ]
    ],
}

_INTENT_MAP: dict[str, str] = {
    "Happy":        "Will Pay",
    "Cooperative":  "Negotiating",
    "Neutral":      "Stalling",
    "Frustrated":   "Disputing",
    "Angry":        "Refusing",
    "Desperate":    "Negotiating",
}


def _keyword_analysis(text: str) -> dict:
    """Score text against keyword patterns and pick the best match."""
    scores: dict[str, int] = {}
    for emotion, patterns in _PATTERNS.items():
        total = sum(len(p.findall(text)) for p in patterns)
        if total:
            scores[emotion] = total

    if not scores:
        return {
            "emotion": "Neutral",
            "confidence": 0.4,
            "intent": "Stalling",
            "reasoning": "No strong emotion keywords detected — defaulting to Neutral.",
        }

    best_emotion = max(scores, key=scores.get)           # type: ignore[arg-type]
    total_hits   = sum(scores.values())
    confidence   = min(scores[best_emotion] / max(total_hits, 1), 1.0)

    return {
        "emotion": best_emotion,
        "confidence": round(confidence, 2),
        "intent": _INTENT_MAP.get(best_emotion, "Unknown"),
        "reasoning": (f"Keyword analysis found {scores[best_emotion]} "
                      f"{best_emotion}-related terms."),
    }


# ════════════════════════════════════════════════════════════════════════
# BATCH — analyse recent unanalysed emails
# ════════════════════════════════════════════════════════════════════════

def batch_analyse_responses(responses: list[dict]) -> list[dict]:
    """
    Analyse a list of { "text": str, "email_id": str } dicts.
    Returns list with added sentiment keys.
    """
    results = []
    for item in responses:
        sentiment = analyse_sentiment(item.get("text", ""))
        sentiment["email_id"] = item.get("email_id", "")
        results.append(sentiment)
    return results
