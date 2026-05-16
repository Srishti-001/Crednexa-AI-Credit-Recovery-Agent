"""
OpenAI API wrapper — fallback AI provider.
"""

from openai import OpenAI
from loguru import logger
import config


def _get_client():
    """Initialize and return the OpenAI client."""
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in .env file")
    return OpenAI(api_key=config.OPENAI_API_KEY)


def generate_text(prompt: str, temperature: float = None, max_tokens: int = None) -> str:
    """Generate text using OpenAI API."""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional finance and credit recovery assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature or config.AI_TEMPERATURE,
            max_tokens=max_tokens or config.AI_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise


def generate_json(prompt: str, temperature: float = None) -> str:
    """Generate JSON output using OpenAI."""
    json_prompt = f"""{prompt}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no code blocks, no explanations."""
    return generate_text(json_prompt, temperature=temperature or 0.3)


def generate_email(prompt: str) -> str:
    return generate_text(prompt, temperature=0.7)


def analyze_emotion(prompt: str) -> str:
    return generate_json(prompt, temperature=0.2)


def generate_strategy(prompt: str) -> str:
    return generate_json(prompt, temperature=0.5)


def generate_summary(prompt: str) -> str:
    return generate_text(prompt, temperature=0.4)


def is_configured() -> bool:
    """Check if OpenAI API is configured."""
    return bool(config.OPENAI_API_KEY and config.OPENAI_API_KEY != "your_openai_api_key_here")
