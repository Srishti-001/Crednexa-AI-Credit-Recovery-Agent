"""
Google Gemini API wrapper for AI-powered features.
"""

import google.generativeai as genai
from loguru import logger
import config


def _get_model():
    """Initialize and return the Gemini model."""
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env file")
    genai.configure(api_key=config.GEMINI_API_KEY)
    return genai.GenerativeModel(config.GEMINI_MODEL)


def generate_text(prompt: str, temperature: float = None, max_tokens: int = None) -> str:
    """
    Generate text using Gemini API.
    Returns the generated text string.
    """
    try:
        model = _get_model()
        generation_config = genai.types.GenerationConfig(
            temperature=temperature or config.AI_TEMPERATURE,
            max_output_tokens=max_tokens or config.AI_MAX_TOKENS,
        )
        response = model.generate_content(prompt, generation_config=generation_config)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise


def generate_json(prompt: str, temperature: float = None) -> str:
    """
    Generate JSON output using Gemini.
    Adds explicit JSON instruction to the prompt.
    """
    json_prompt = f"""{prompt}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no code blocks, no explanations.
Just the raw JSON object."""
    return generate_text(json_prompt, temperature=temperature or 0.3)


def generate_email(prompt: str) -> str:
    """Generate email content with slightly creative temperature."""
    return generate_text(prompt, temperature=0.7)


def analyze_emotion(prompt: str) -> str:
    """Analyze emotion with low temperature for consistency."""
    return generate_json(prompt, temperature=0.2)


def generate_strategy(prompt: str) -> str:
    """Generate recovery strategy."""
    return generate_json(prompt, temperature=0.5)


def generate_summary(prompt: str) -> str:
    """Generate financial summary."""
    return generate_text(prompt, temperature=0.4)


def is_configured() -> bool:
    """Check if Gemini API is configured."""
    return bool(config.GEMINI_API_KEY and config.GEMINI_API_KEY != "your_gemini_api_key_here")
