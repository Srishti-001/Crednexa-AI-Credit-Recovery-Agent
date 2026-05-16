"""
AI response parser — extract and validate structured data from AI responses.
"""

import json
import re
from loguru import logger


def parse_json_response(response: str) -> dict:
    """
    Parse a JSON response from AI, handling common formatting issues.
    Returns parsed dict, or empty dict on failure.
    """
    if not response:
        return {}

    # Try direct JSON parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from code blocks
    patterns = [
        r'```json\s*\n?(.*?)\n?\s*```',
        r'```\s*\n?(.*?)\n?\s*```',
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
    ]

    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if '```' in pattern else match.group(0))
            except (json.JSONDecodeError, IndexError):
                continue

    logger.warning(f"Failed to parse JSON from AI response: {response[:200]}...")
    return {}


def extract_email_content(response: str) -> dict:
    """
    Extract email subject and body from AI response.
    Returns {'subject': str, 'body': str}.
    """
    # Try JSON first
    parsed = parse_json_response(response)
    if parsed and "subject" in parsed and "body" in parsed:
        return parsed

    # Try pattern matching
    subject = ""
    body = response

    # Look for Subject: line
    subject_match = re.search(r'(?:Subject|SUBJECT):\s*(.+?)(?:\n|$)', response)
    if subject_match:
        subject = subject_match.group(1).strip()
        # Body is everything after the subject line
        body_start = subject_match.end()
        body = response[body_start:].strip()

        # Remove "Body:" prefix if present
        body = re.sub(r'^(?:Body|BODY|Content|MESSAGE):\s*', '', body, flags=re.IGNORECASE).strip()

    return {"subject": subject, "body": body}


def extract_emotion_data(response: str) -> dict:
    """
    Extract emotion analysis from AI response.
    Returns {'emotion': str, 'confidence': float, 'intent': str, 'reasoning': str}.
    """
    parsed = parse_json_response(response)
    return {
        "emotion": parsed.get("emotion", "Neutral"),
        "confidence": float(parsed.get("confidence", 0.5)),
        "intent": parsed.get("intent", "Unknown"),
        "reasoning": parsed.get("reasoning", ""),
    }


def extract_strategy_data(response: str) -> dict:
    """
    Extract recovery strategy from AI response.
    Returns {'strategy_type': str, 'description': str, 'actions': list, 'priority': str, 'reasoning': str}.
    """
    parsed = parse_json_response(response)
    return {
        "strategy_type": parsed.get("strategy_type", "Negotiation"),
        "description": parsed.get("description", ""),
        "actions": parsed.get("recommended_actions", parsed.get("actions", [])),
        "priority": parsed.get("priority", "Medium"),
        "reasoning": parsed.get("reasoning", ""),
    }


def extract_tone_recommendation(response: str) -> dict:
    """
    Extract AI tone recommendation.
    Returns {'recommended_tone': str, 'reasoning': str, 'confidence': float}.
    """
    parsed = parse_json_response(response)
    return {
        "recommended_tone": parsed.get("recommended_tone", "Professional"),
        "reasoning": parsed.get("reasoning", ""),
        "confidence": float(parsed.get("confidence", 0.5)),
    }
