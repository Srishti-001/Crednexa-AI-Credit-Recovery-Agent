"""
tone_engine.py — backward-compatibility shim.
Proxies to services.learning_engine (the new self-learning implementation).
"""

from services.learning_engine import (
    determine_optimal_tone as determine_tone,
    get_all_tones,
)

__all__ = ["determine_tone", "get_all_tones"]
