"""
Unit tests for ActiveMemory.
"""

from antiecho.memory import ActiveMemory


def test_extract_facts_and_constraints():
    memory = ActiveMemory()
    messages = [
        {"role": "user", "content": "We are using Python 3.12 and SQLite."},
        {"role": "user", "content": "- Must avoid external dependencies\n- Always return valid JSON"}
    ]

    memory.extract_from_messages(messages)
    rendered = memory.render_pinned_context()

    assert "[Active Context & Pinned Directives]" in rendered
    assert "Constraint: Must avoid external dependencies" in rendered or "Constraint: Always return valid JSON" in rendered
    assert any("using Python" in f or "Python" in f for f in memory.facts)


def test_inject_memory_header_to_existing_system():
    memory = ActiveMemory()
    memory.facts.add("language is Rust")
    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    updated = memory.inject_memory_header(messages)
    assert len(updated) == 1
    assert "You are a helpful assistant." in updated[0]["content"]
    assert "[Active Context & Pinned Directives]" in updated[0]["content"]
    assert "language is Rust" in updated[0]["content"]
