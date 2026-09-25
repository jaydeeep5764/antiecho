"""
Unit tests for EchoDetector.
"""

from antiecho.detector import EchoDetector


def test_strip_boilerplate_opening():
    detector = EchoDetector()
    text = "Certainly! As you mentioned earlier, we will use Python 3.12. Here is the code."
    cleaned, count = detector.strip_boilerplate(text)
    assert count >= 1
    assert "Certainly! As you mentioned earlier," not in cleaned
    assert "we will use Python 3.12" in cleaned


def test_strip_boilerplate_closing():
    detector = EchoDetector()
    text = "Here is the code snippet.\n\nLet me know if you would like me to modify anything else!"
    cleaned, count = detector.strip_boilerplate(text)
    assert count >= 1
    assert "Let me know if you would like me to modify" not in cleaned
    assert "Here is the code snippet." in cleaned


def test_find_repeated_phrases():
    detector = EchoDetector(min_phrase_words=4, echo_threshold=2)
    messages = [
        "First turn. Remember that we are targeting Windows 11 only. Here is part 1.",
        "Second turn. Remember that we are targeting Windows 11 only. Here is part 2.",
        "Third turn. Something completely different without that phrase.",
    ]
    echoes = detector.find_repeated_phrases(messages)
    assert len(echoes) >= 1
    assert any("remember that we are targeting windows 11 only" in e for e in echoes)


def test_sanitize_turn_removes_known_echoes():
    detector = EchoDetector()
    known = {"remember that we are targeting windows 11 only"}
    text = "Certainly! Remember that we are targeting Windows 11 only. Let's write the code."
    cleaned, count = detector.sanitize_turn(text, known)
    assert "Remember that we are targeting Windows 11 only" not in cleaned
    assert count >= 1
