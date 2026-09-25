"""
AntiEcho: Stop LLM context echoing, repetition spirals, and memory poisoning.
"""

from antiecho.core import AntiEcho, clean, get_last_stats, CleaningStats
from antiecho.detector import EchoDetector
from antiecho.pruner import ContextPruner
from antiecho.memory import ActiveMemory
from antiecho.wrapper import wrap

__version__ = "0.1.0"

__all__ = [
    "AntiEcho",
    "clean",
    "wrap",
    "get_last_stats",
    "CleaningStats",
    "EchoDetector",
    "ContextPruner",
    "ActiveMemory",
]
