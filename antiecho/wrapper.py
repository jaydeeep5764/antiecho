"""
AntiEcho SDK Client Wrapper.
Provides transparent, 1-line interception for OpenAI and OpenAI-compatible clients.
"""

from __future__ import annotations
from typing import Any, Callable, Optional, Dict
import functools

from antiecho.core import AntiEcho, CleaningStats


class CompletionsWrapper:
    """Wraps client.chat.completions to sanitize messages before execution."""

    def __init__(self, target_completions: Any, engine: AntiEcho):
        self._target = target_completions
        self._engine = engine

    def create(self, *args: Any, **kwargs: Any) -> Any:
        """Intercepts chat.completions.create and cleans messages."""
        if "messages" in kwargs and isinstance(kwargs["messages"], list):
            kwargs["messages"] = self._engine.clean(kwargs["messages"])
        return self._target.create(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


class ChatWrapper:
    """Wraps client.chat to intercept completions."""

    def __init__(self, target_chat: Any, engine: AntiEcho):
        self._target = target_chat
        self._engine = engine
        self.completions = CompletionsWrapper(target_chat.completions, engine)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


class ClientWrapper:
    """
    Transparent wrapper around an OpenAI (or compatible) client instance.
    """

    def __init__(self, client: Any, engine: Optional[AntiEcho] = None):
        self._client = client
        self._engine = engine or AntiEcho()
        if hasattr(client, "chat"):
            self.chat = ChatWrapper(client.chat, self._engine)

    @property
    def last_stats(self) -> Optional[CleaningStats]:
        """Access stats from the most recent sanitized call."""
        return self._engine.stats

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


def wrap(client: Any, engine: Optional[AntiEcho] = None) -> Any:
    """
    Wraps an OpenAI or OpenAI-compatible client instance in 1 line.
    
    Example:
        from openai import OpenAI
        from antiecho import wrap

        client = wrap(OpenAI())
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
    """
    return ClientWrapper(client, engine)
