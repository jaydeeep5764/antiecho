"""
AntiEcho Core Orchestrator.
Coordinates echo detection, context pruning, active memory distillation,
and token savings measurement.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import copy

from antiecho.detector import EchoDetector
from antiecho.pruner import ContextPruner
from antiecho.memory import ActiveMemory


@dataclass
class CleaningStats:
    """Detailed metrics on context sanitization and savings."""
    original_messages: int = 0
    cleaned_messages: int = 0
    original_chars: int = 0
    cleaned_chars: int = 0
    original_tokens: int = 0
    cleaned_tokens: int = 0
    tokens_saved: int = 0
    reduction_percent: float = 0.0
    echoes_pruned: int = 0
    resolved_errors_collapsed: int = 0
    code_blocks_superseded: int = 0
    active_facts_pinned: int = 0

    def summary(self) -> str:
        """Returns a human-readable one-line summary of savings."""
        return (
            f"AntiEcho: Saved {self.tokens_saved:,} tokens (-{self.reduction_percent:.1f}%) | "
            f"Pruned {self.echoes_pruned} echoes, {self.resolved_errors_collapsed} resolved errors, "
            f"{self.code_blocks_superseded} superseded code blocks | "
            f"Pinned {self.active_facts_pinned} active facts"
        )


class AntiEcho:
    """
    Main AntiEcho engine for context sanitization and memory preservation.
    """

    def __init__(
        self,
        strip_boilerplate: bool = True,
        detect_repeated_phrases: bool = True,
        collapse_resolved_errors: bool = True,
        prune_superseded_code: bool = True,
        pin_active_memory: bool = True,
        max_recent_turns_raw: int = 6,
        chars_per_token: float = 4.0,
    ):
        self.strip_boilerplate = strip_boilerplate
        self.detect_repeated_phrases = detect_repeated_phrases
        self.collapse_resolved_errors = collapse_resolved_errors
        self.prune_superseded_code = prune_superseded_code
        self.pin_active_memory = pin_active_memory
        self.max_recent_turns_raw = max_recent_turns_raw
        self.chars_per_token = chars_per_token

        self.detector = EchoDetector()
        self.pruner = ContextPruner(keep_code_in_recent_turns=max(2, max_recent_turns_raw // 2))
        self.memory = ActiveMemory()
        self.last_stats: Optional[CleaningStats] = None

    def _estimate_tokens(self, text: str) -> int:
        return max(1, int(len(text) / self.chars_per_token))

    def _calculate_total_chars(self, messages: List[Dict[str, Any]]) -> int:
        return sum(len(str(m.get("content", ""))) for m in messages)

    def clean(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sanitizes and de-echoes a conversation history.
        Works directly with standard OpenAI/Anthropic format:
        [{"role": "user"|"assistant"|"system", "content": "..."}]
        """
        if not messages:
            self.last_stats = CleaningStats()
            return []

        orig_chars = self._calculate_total_chars(messages)
        orig_tokens = self._estimate_tokens(" ".join(str(m.get("content", "")) for m in messages))

        # Deep copy to prevent modifying user input in place
        working_messages = copy.deepcopy(messages)

        # 1. Distill Active Memory & Facts
        facts_pinned = 0
        if self.pin_active_memory:
            self.memory.extract_from_messages(working_messages)
            working_messages = self.memory.inject_memory_header(working_messages)
            facts_pinned = len(self.memory.facts) + len(self.memory.constraints)

        # 2. Collapse Resolved Errors
        errors_collapsed = 0
        if self.collapse_resolved_errors:
            working_messages, errors_collapsed = self.pruner.collapse_resolved_tracebacks(working_messages)

        # 3. Prune Superseded Code Blocks
        code_superseded = 0
        if self.prune_superseded_code:
            working_messages, code_superseded = self.pruner.prune_superseded_code_blocks(working_messages)

        # 4. Detect and Eliminate Repetitive Assistant Phrases
        echoes_pruned = 0
        assistant_contents = [
            str(m.get("content", "")) for m in working_messages if m.get("role") == "assistant"
        ]
        
        known_echoes: Set[str] = set()
        if self.detect_repeated_phrases:
            known_echoes = self.detector.find_repeated_phrases(assistant_contents)

        for i, msg in enumerate(working_messages):
            if msg.get("role") == "assistant":
                content = str(msg.get("content", ""))
                cleaned_content, count = self.detector.sanitize_turn(content, known_echoes)
                if count > 0:
                    echoes_pruned += count
                    working_messages[i]["content"] = cleaned_content

        # Calculate final metrics
        cleaned_chars = self._calculate_total_chars(working_messages)
        cleaned_tokens = self._estimate_tokens(" ".join(str(m.get("content", "")) for m in working_messages))
        tokens_saved = max(0, orig_tokens - cleaned_tokens)
        reduction_pct = (tokens_saved / orig_tokens * 100.0) if orig_tokens > 0 else 0.0

        self.last_stats = CleaningStats(
            original_messages=len(messages),
            cleaned_messages=len(working_messages),
            original_chars=orig_chars,
            cleaned_chars=cleaned_chars,
            original_tokens=orig_tokens,
            cleaned_tokens=cleaned_tokens,
            tokens_saved=tokens_saved,
            reduction_percent=reduction_pct,
            echoes_pruned=echoes_pruned,
            resolved_errors_collapsed=errors_collapsed,
            code_blocks_superseded=code_superseded,
            active_facts_pinned=facts_pinned,
        )

        return working_messages

    @property
    def stats(self) -> Optional[CleaningStats]:
        """Returns the stats from the most recent clean() call."""
        return self.last_stats


# Default global instance for 1-line usage
_default_engine = AntiEcho()


def clean(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function: Cleans and de-echoes message history in 1 line.
    
    Example:
        import antiecho
        clean_messages = antiecho.clean(messages)
    """
    return _default_engine.clean(messages)


def get_last_stats() -> Optional[CleaningStats]:
    """Returns the stats from the last clean() execution."""
    return _default_engine.stats
