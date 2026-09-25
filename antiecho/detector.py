"""
AntiEcho Loop & Echo Detector.
Detects cross-turn conversational echoes, assistant boilerplate, and repetitive loops.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple, Set


# Common assistant echoing prefixes and conversational filler patterns
BOILERPLATE_PATTERNS = [
    # Reference echoes
    r"^(?:Certainly|Sure|Of course|Great|Understood|Alright|Got it)[!,.]?\s+(?:as\s+(?:you\s+)?(?:mentioned|stated|noted|specified|requested|discussed|pointed out)(?:\s+(?:earlier|before|previously|above))?)[^.,\n]*[.,!:]\s*",
    r"^(?:As\s+(?:you\s+)?(?:mentioned|stated|noted|specified|requested|discussed|pointed out)(?:\s+(?:earlier|before|previously|above))?)[^.,\n]*[.,!:]\s*",
    r"^(?:Based\s+on\s+(?:our\s+)?(?:previous\s+)?(?:conversation|discussion|context)[^.,\n]*[.,!:]\s*)",
    r"^(?:Since\s+we\s+are\s+using\s+[^.,\n]+(?:as\s+you\s+mentioned)?)[.,!:]\s*",
    r"^(?:Keeping\s+in\s+mind\s+that\s+[^.,\n]+)[.,!:]\s*",
    
    # Generic conversational filler openings
    r"^(?:Certainly|Sure|Of course|Absolutely|Definitely)[!.,]?\s+(?:I\'d\s+be\s+happy\s+to\s+help\s+(?:you\s+)?(?:with\s+that)?)[!.,:]\s*",
    r"^(?:I\s+understand\s+(?:your\s+request|that\s+you\s+want\s+to|what\s+you\s+are\s+asking))[!.,:]\s*",
    r"^(?:Here\s+(?:is|are)\s+(?:the\s+)?(?:updated\s+)?(?:solution|code|response|implementation)[!.,:]\s*)",
    
    # Repetitive sign-offs / closings
    r"\n*(?:Let\s+me\s+know\s+if\s+you\s+(?:have\s+any\s+(?:other\s+)?questions|need\s+(?:any\s+)?(?:further\s+)?assistance|would\s+like\s+me\s+to\s+(?:change|modify)\s+anything(?:\s+else)?))[.!]*\s*$",
    r"\n*(?:Feel\s+free\s+to\s+ask\s+if\s+you\s+need\s+anything\s+else)[.!]*\s*$",
    r"\n*(?:I\s+hope\s+this\s+helps[!.]*)\s*$",
]

COMPILED_BOILERPLATE = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in BOILERPLATE_PATTERNS]


class EchoDetector:
    """
    Analyzes message history to detect:
    1. Cross-turn phrase echoing (e.g. repeated justifications or mantras).
    2. Conversational assistant boilerplate.
    3. Structural duplication.
    """

    def __init__(self, min_phrase_words: int = 5, echo_threshold: int = 2):
        self.min_phrase_words = min_phrase_words
        self.echo_threshold = echo_threshold

    def strip_boilerplate(self, content: str) -> Tuple[str, int]:
        """
        Strips common conversational echoing boilerplate from a single message content.
        Returns (cleaned_content, num_matches_removed).
        """
        cleaned = content
        matches_count = 0

        for pattern in COMPILED_BOILERPLATE:
            new_cleaned, count = pattern.subn("", cleaned)
            if count > 0:
                matches_count += count
                cleaned = new_cleaned.strip()

        return cleaned, matches_count

    def find_repeated_phrases(self, assistant_messages: List[str]) -> Set[str]:
        """
        Identifies multi-word phrases that the assistant is obsessively repeating
        across multiple turns (echo loops).
        """
        if len(assistant_messages) < 2:
            return set()

        phrase_counts: Dict[str, int] = {}

        for msg in assistant_messages:
            # Normalize and extract candidate sentences or clauses
            sentences = re.split(r'[.\n;!?]', msg)
            seen_in_msg: Set[str] = set()

            for s in sentences:
                s_clean = " ".join(s.strip().lower().split())
                words = s_clean.split()
                if len(words) >= self.min_phrase_words:
                    if s_clean not in seen_in_msg:
                        seen_in_msg.add(s_clean)
                        phrase_counts[s_clean] = phrase_counts.get(s_clean, 0) + 1

        # Keep phrases that appear in at least `echo_threshold` different assistant messages
        echoes = {phrase for phrase, count in phrase_counts.items() if count >= self.echo_threshold}
        return echoes

    def sanitize_turn(self, content: str, known_echoes: Set[str]) -> Tuple[str, int]:
        """
        Cleans a message content by stripping boilerplate and suppressing known echoes.
        """
        cleaned, boilerplate_removed = self.strip_boilerplate(content)
        echoes_removed = 0

        for echo in known_echoes:
            # Case-insensitive replacement of repeated sentence
            pattern = re.compile(re.escape(echo), re.IGNORECASE)
            new_cleaned, count = pattern.subn("", cleaned)
            if count > 0:
                echoes_removed += count
                cleaned = new_cleaned

        # Clean up double newlines and spaces
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
        return cleaned, boilerplate_removed + echoes_removed
