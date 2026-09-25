"""
AntiEcho Pruner.
Prunes dead weight, collapsed resolved error tracebacks, and superseded code blocks.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple


# Regex patterns to detect stack traces and compiler errors
TRACEBACK_PATTERNS = [
    # Python traceback
    r"Traceback\s+\(most\s+recent\s+call\s+last\):[\s\S]+?(?:\w+Error|\w+Exception):\s+[^\n]+",
    # Node/JS stack trace
    r"(?:Error|TypeError|ReferenceError|SyntaxError):\s+[^\n]+(?:\n\s+at\s+[^\n]+)+",
    # Rust / Go / C++ compiler error blocks
    r"(?:error\[E\d+\]|fatal\s+error):[\s\S]+?(?:\n\n|\Z)",
]

COMPILED_TRACEBACKS = [re.compile(p) for p in TRACEBACK_PATTERNS]

# Indications that a previous problem was resolved
RESOLUTION_INDICATORS = [
    r"\b(?:worked|fixed|solved|resolved|it works|that worked|now it works|passed|builds now|working now)\b",
    r"\b(?:thanks|thank you|perfect|great job|awesome)\b",
    r"\b(?:next\s+step|moving\s+on|now\s+let\'s|next\s+issue)\b"
]
COMPILED_RESOLUTIONS = [re.compile(p, re.IGNORECASE) for p in RESOLUTION_INDICATORS]


class ContextPruner:
    """
    Identifies and compresses context that is no longer needed:
    - Resolved error traces
    - Superseded code blocks in earlier turns
    """

    def __init__(self, keep_code_in_recent_turns: int = 2):
        self.keep_code_in_recent_turns = keep_code_in_recent_turns

    def is_error_resolved_in_chat(self, error_turn_index: int, messages: List[Dict[str, Any]]) -> bool:
        """
        Checks if subsequent user messages indicate that the error mentioned at error_turn_index
        was successfully resolved.
        """
        # Look at user messages after error_turn_index
        for idx in range(error_turn_index + 1, len(messages)):
            msg = messages[idx]
            if msg.get("role") == "user":
                content = str(msg.get("content", ""))
                for pattern in COMPILED_RESOLUTIONS:
                    if pattern.search(content):
                        return True
        return False

    def collapse_resolved_tracebacks(self, messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Collapses verbose multi-line tracebacks in earlier turns if they were resolved.
        """
        pruned_messages = []
        collapsed_count = 0

        for i, msg in enumerate(messages):
            content = str(msg.get("content", ""))
            role = msg.get("role", "")

            # If it's a past turn (not the latest message) and appears resolved
            if i < len(messages) - 1 and self.is_error_resolved_in_chat(i, messages):
                new_content = content
                for pattern in COMPILED_TRACEBACKS:
                    matches = list(pattern.finditer(new_content))
                    for m in matches:
                        raw_trace = m.group(0)
                        # Extract error type and message for the summary line
                        first_line = raw_trace.strip().split("\n")[0]
                        last_line = raw_trace.strip().split("\n")[-1]
                        summary = f"[Resolved Error Traceback: {last_line or first_line}]"
                        new_content = new_content.replace(raw_trace, summary)
                        collapsed_count += 1
                
                pruned_messages.append({**msg, "content": new_content})
            else:
                pruned_messages.append(msg)

        return pruned_messages, collapsed_count

    def prune_superseded_code_blocks(self, messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Compresses large code blocks in older assistant turns if newer assistant turns
        provide revised implementations.
        """
        # Collect assistant turn indices
        assistant_indices = [i for i, m in enumerate(messages) if m.get("role") == "assistant"]
        if len(assistant_indices) <= self.keep_code_in_recent_turns:
            return messages, 0

        # Indices eligible for superseded code pruning
        eligible_indices = set(assistant_indices[:-self.keep_code_in_recent_turns])
        pruned_messages = []
        pruned_blocks_count = 0

        code_block_pattern = re.compile(r"```([a-zA-Z0-9_\-\+]*)\n([\s\S]+?)```")

        for i, msg in enumerate(messages):
            if i in eligible_indices:
                content = str(msg.get("content", ""))
                
                def replace_old_code(match):
                    nonlocal pruned_blocks_count
                    lang = match.group(1) or "code"
                    code = match.group(2)
                    lines = code.strip().split("\n")
                    # Only collapse non-trivial code blocks (> 6 lines)
                    if len(lines) > 6:
                        pruned_blocks_count += 1
                        first_line = lines[0].strip()[:40]
                        return f"```{lang}\n# [Prior implementation of {first_line}... superseded in later turns]\n```"
                    return match.group(0)

                new_content = code_block_pattern.sub(replace_old_code, content)
                pruned_messages.append({**msg, "content": new_content})
            else:
                pruned_messages.append(msg)

        return pruned_messages, pruned_blocks_count
