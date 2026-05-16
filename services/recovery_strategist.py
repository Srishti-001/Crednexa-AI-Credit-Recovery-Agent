"""
recovery_strategist.py — backward-compatibility shim.
Proxies to services.strategy_engine.
"""

from services.strategy_engine import generate_recovery_strategy

__all__ = ["generate_recovery_strategy"]
