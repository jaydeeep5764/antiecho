"""
AntiEcho Active Memory & Fact Distiller.
Maintains persistent facts, user constraints, and project specifications
so that old conversational turns can be pruned without losing critical context.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any, Set, Tuple


FACT_PATTERNS = [
    # Explicit user requirements & constraints
    r"(?:we\s+are\s+using|I\s+am\s+using|use|project\s+uses)\s+([A-Za-z0-9_\-\.\+]+(?:\s+[A-Za-z0-9_\-\.\+]+){0,4})",
    r"(?:don\'t\s+use|do\s+not\s+use|avoid|never\s+use)\s+([A-Za-z0-9_\-\.\+]+(?:\s+[A-Za-z0-9_\-\.\+]+){0,4})",
    r"(?:operating\s+system|OS\s+is|running\s+on)\s+([A-Za-z0-9_\-]+)",
    r"(?:language\s+is|written\s+in)\s+([A-Za-z0-9_\-]+)",
    r"(?:database\s+is|DB\s+is)\s+([A-Za-z0-9_\-]+)",
    r"(?:target\s+framework|framework\s+is)\s+([A-Za-z0-9_\-]+)",
]


class ActiveMemory:
    """
    Distills and pins critical conversation constraints, specifications, and facts.
    """

    def __init__(self):
        self.facts: Set[str] = set()
        self.constraints: Set[str] = set()

    def extract_from_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Extracts key architectural, language, and project facts from user instructions.
        """
        for msg in messages:
            if msg.get("role") == "user":
                content = str(msg.get("content", ""))
                
                # Check for explicit directives
                for line in content.split("\n"):
                    line_clean = line.strip().lstrip("-*• ")
                    
                    # Catch bullet points or short lines that state preferences/constraints
                    if re.match(r"^(?:must|always|never|do not|don't|prefer|only use)\b", line_clean, re.I):
                        if 10 <= len(line_clean) <= 120:
                            self.constraints.add(line_clean)

                    # Extract language, tools, database specs
                    for pat in FACT_PATTERNS:
                        match = re.search(pat, line_clean, re.I)
                        if match:
                            fact_candidate = match.group(0).strip()
                            if len(fact_candidate) > 4:
                                self.facts.add(fact_candidate)

    def render_pinned_context(self) -> str:
        """
        Renders the active memory block into a clean, compact system injection.
        """
        if not self.facts and not self.constraints:
            return ""

        lines = ["[Active Context & Pinned Directives]"]
        for c in sorted(self.constraints):
            lines.append(f"• Constraint: {c}")
        for f in sorted(self.facts):
            lines.append(f"• Fact: {f}")

        return "\n".join(lines)

    def inject_memory_header(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensures the active memory block is cleanly pinned to the system prompt
        or the beginning of the context.
        """
        memory_str = self.render_pinned_context()
        if not memory_str:
            return messages

        updated = list(messages)
        if updated and updated[0].get("role") == "system":
            sys_content = updated[0].get("content", "")
            if "[Active Context & Pinned Directives]" not in sys_content:
                updated[0] = {
                    **updated[0],
                    "content": f"{sys_content}\n\n{memory_str}".strip()
                }
        else:
            updated.insert(0, {
                "role": "system",
                "content": memory_str
            })

        return updated
