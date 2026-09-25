"""
Unit tests for AntiEcho core orchestrator and clean() function.
"""

import antiecho


def test_clean_end_to_end():
    messages = [
        {"role": "system", "content": "You are a coding assistant."},
        {"role": "user", "content": "We are using Python 3.12 and FastAPI. Write an endpoint."},
        {
            "role": "assistant",
            "content": (
                "Certainly! As you mentioned, we are using Python 3.12 and FastAPI. "
                "Here is the code:\n\n"
                "```python\n"
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "# line 1\n# line 2\n# line 3\n# line 4\n# line 5\n# line 6\n# line 7\n"
                "```\n\n"
                "Let me know if you would like me to modify anything else!"
            )
        },
        {
            "role": "user",
            "content": (
                "It failed with this error:\n"
                "Traceback (most recent call last):\n"
                "  File \"main.py\", line 1\n"
                "ModuleNotFoundError: No module named 'fastapi'"
            )
        },
        {"role": "assistant", "content": "You need to run: pip install fastapi"},
        {"role": "user", "content": "Awesome, that worked! Now add a route."},
        {
            "role": "assistant",
            "content": (
                "Certainly! As you mentioned, we are using Python 3.12 and FastAPI. "
                "Here is the updated code:\n\n"
                "```python\n"
                "@app.get('/health')\n"
                "def health():\n"
                "    return {'status': 'ok'}\n"
                "```\n\n"
                "Feel free to ask if you need anything else!"
            )
        }
    ]

    cleaned = antiecho.clean(messages)
    stats = antiecho.get_last_stats()

    assert stats is not None
    assert stats.tokens_saved > 0
    assert stats.reduction_percent > 0
    assert stats.echoes_pruned >= 1
    assert stats.resolved_errors_collapsed >= 1
    assert len(cleaned) == len(messages)  # Pinned context injected into system message

    # Verify system message has pinned active memory
    assert "[Active Context & Pinned Directives]" in cleaned[0]["content"]


def test_empty_messages():
    cleaned = antiecho.clean([])
    assert cleaned == []
    stats = antiecho.get_last_stats()
    assert stats is not None
    assert stats.tokens_saved == 0
