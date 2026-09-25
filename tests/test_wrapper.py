"""
Unit tests for the client wrapper.
"""

from antiecho import wrap


class MockCompletions:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return {"choices": [{"message": {"role": "assistant", "content": "mocked response"}}]}


class MockChat:
    def __init__(self):
        self.completions = MockCompletions()


class MockOpenAIClient:
    def __init__(self):
        self.chat = MockChat()


def test_wrapper_intercepts_messages():
    mock_client = MockOpenAIClient()
    wrapped = wrap(mock_client)

    raw_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "We are using Python 3.12."},
        {"role": "assistant", "content": "Certainly! As you mentioned, we are using Python 3.12."},
    ]

    response = wrapped.chat.completions.create(
        model="gpt-4o",
        messages=raw_messages
    )

    assert response["choices"][0]["message"]["content"] == "mocked response"
    intercepted_messages = mock_client.chat.completions.last_kwargs["messages"]

    # Verify that the intercepted messages were processed (e.g. pinned memory injected or cleaned)
    assert "[Active Context & Pinned Directives]" in intercepted_messages[0]["content"]
    assert wrapped.last_stats is not None
