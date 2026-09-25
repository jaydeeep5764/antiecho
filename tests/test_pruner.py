"""
Unit tests for ContextPruner.
"""

from antiecho.pruner import ContextPruner


def test_collapse_resolved_tracebacks():
    pruner = ContextPruner()
    messages = [
        {"role": "user", "content": "Hello, write code."},
        {
            "role": "user",
            "content": (
                "I got an error:\n"
                "Traceback (most recent call last):\n"
                "  File \"test.py\", line 10, in <module>\n"
                "    val = obj.foo()\n"
                "AttributeError: 'NoneType' object has no attribute 'foo'"
            )
        },
        {"role": "assistant", "content": "Here is the fix: check if obj is not None."},
        {"role": "user", "content": "Awesome, that worked! Now let's do part 2."}
    ]

    pruned, count = pruner.collapse_resolved_tracebacks(messages)
    assert count == 1
    assert "Resolved Error Traceback" in pruned[1]["content"]
    assert "AttributeError: 'NoneType' object has no attribute 'foo'" in pruned[1]["content"]
    assert "File \"test.py\", line 10" not in pruned[1]["content"]


def test_prune_superseded_code_blocks():
    pruner = ContextPruner(keep_code_in_recent_turns=1)
    large_code_1 = "```python\n" + "\n".join([f"line_{i} = {i}" for i in range(10)]) + "\n```"
    large_code_2 = "```python\n" + "\n".join([f"updated_line_{i} = {i}" for i in range(10)]) + "\n```"

    messages = [
        {"role": "user", "content": "Step 1"},
        {"role": "assistant", "content": f"Here is draft 1:\n{large_code_1}"},
        {"role": "user", "content": "Step 2 update it"},
        {"role": "assistant", "content": f"Here is draft 2:\n{large_code_2}"}
    ]

    pruned, count = pruner.prune_superseded_code_blocks(messages)
    assert count == 1
    # First assistant message code should be superseded
    assert "superseded in later turns" in pruned[1]["content"]
    # Latest assistant message code should still be intact
    assert "updated_line_9 = 9" in pruned[3]["content"]
