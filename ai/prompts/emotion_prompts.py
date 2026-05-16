"""
Prompt templates for Client Emotion and Intent Detection.
"""


def get_emotion_prompt(
    client_response: str,
    company_name: str = "",
    conversation_history: str = "",
) -> str:
    """Generate prompt for emotion and intent detection from client response."""

    return f"""You are an expert in communication analysis and emotional intelligence.
Analyze the following client response and detect their emotional state and intent.

{f"CLIENT: {company_name}" if company_name else ""}

CLIENT RESPONSE:
\"\"\"{client_response}\"\"\"

{f"CONVERSATION HISTORY:{chr(10)}{conversation_history}" if conversation_history else ""}

ANALYSIS REQUIRED:
1. Primary Emotion: Detect the dominant emotion
2. Confidence Level: How confident are you in this assessment
3. Intent: What is the client trying to communicate
4. Recommended Approach: How should we respond

Respond with JSON:
{{
    "emotion": "Happy|Neutral|Frustrated|Angry|Desperate|Cooperative",
    "confidence": 0.0 to 1.0,
    "intent": "Brief description of client's intent",
    "reasoning": "Explanation of why you detected this emotion",
    "recommended_approach": "How to respond to this client",
    "urgency": "Low|Medium|High",
    "payment_likelihood": "Low|Medium|High"
}}"""


def get_batch_emotion_prompt(responses: list) -> str:
    """Generate prompt for analyzing multiple client responses."""
    formatted = "\n\n".join([
        f"Response {i+1} (Client: {r.get('company_name', 'Unknown')}):\n\"{r.get('text', '')}\""
        for i, r in enumerate(responses)
    ])

    return f"""Analyze the following client responses and detect emotions for each.

{formatted}

Respond with a JSON array of emotion analyses, one per response:
[
    {{
        "response_index": 1,
        "emotion": "...",
        "confidence": 0.0-1.0,
        "intent": "...",
        "payment_likelihood": "Low|Medium|High"
    }}
]"""
