"""
risk_scorer.py — backward-compatibility shim.
Proxies all calls to services.risk_engine (the new implementation).
"""

from services.risk_engine import (
    calculate_client_risk,
    recalculate_all_risks,
    get_priority_queue,
    get_risk_overview,
)

__all__ = [
    "calculate_client_risk",
    "recalculate_all_risks",
    "get_priority_queue",
    "get_risk_overview",
]
