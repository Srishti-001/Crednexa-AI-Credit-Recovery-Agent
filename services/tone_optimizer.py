"""
tone_optimizer.py — backward-compatibility shim.
Proxies to services.learning_engine.
"""

from services.learning_engine import (
    record_tone_outcome as record_feedback,
    get_tone_performance_report as get_optimized_tone,
    get_client_learning_data,
)

__all__ = ["record_feedback", "get_optimized_tone", "get_client_learning_data"]
