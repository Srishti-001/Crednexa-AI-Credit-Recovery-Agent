"""
emotion_detector.py — backward-compatibility shim.
Proxies to services.sentiment_analysis.
"""

from services.sentiment_analysis import analyse_sentiment as detect_emotion

__all__ = ["detect_emotion"]
