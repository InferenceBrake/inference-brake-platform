"""Decorators for wrapping raw agent completion and tool loops.

Use these with the raw OpenAI/Anthropic SDKs, or any custom loop that does not
use a supported framework callback.
"""

from __future__ import annotations

import functools
import inspect
import logging
import os
from typing import Any, Callable, Optional

from .client import (
    CheckStatus,
    InferenceBrake,
    LoopDetectedError,
)
from .policy import LoopPolicy

logger = logging.getLogger(__name__)


def loop_key(fn: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Mark a callable as a loop identity normalizer.

    Mirrors OpenRouter's per-tool ``loopKey``. The callable takes the raw action
    identity and returns a normalized, hashable identity so cosmetic differences
    do not look like progress. Return ``None`` to skip that action.
    """
    fn.__inferencebrake_loop_key__ = True  # type: ignore[attr-defined]
    return fn


def guard_agent_loop(
    api_key: Optional[str] = None,
    session_id: Optional[Any] = None,
    supabase_url: Optional[str] = None,
    timeout: int = 10,
    auto_stop: bool = True,
    fail_open: bool = True,
    extract: Optional[Callable[[Any], str]] = None,
    action: Optional[Callable[[Any], Optional[str]]] = None,
    loop_key: Optional[Callable[[str], Optional[str]]] = None,
    check_input: bool = False,
    on_loop: Optional[Callable[[CheckStatus], None]] = None,
    escalate: Optional[Callable[[CheckStatus, int], None]] = None,
    max_escalations: int = 2,
    model: Optional[Any] = None,
    prompt: Optional[Any] = None,
) -> Callable:
    """Wrap a function so every result is checked for a reasoning loop.

    The decorated function is typically one model completion or one agent step.
    Its return value (or ``extract(result)``) is the reasoning text sent to
    InferenceBrake. On detection the wrapper calls ``on_loop`` and, if
    ``auto_stop`` is set, raises :class:`LoopDetectedError`.

    Args:
        api_key: InferenceBrake key. Falls back to ``INFERENCEBRAKE_API_KEY``.
        session_id: Static string, or a callable ``(args, kwargs) -> str``.
        supabase_url: Override the API base URL (self-hosting).
        timeout: Request timeout in seconds.
        auto_stop: Raise ``LoopDetectedError`` on a detected loop (default True).
        fail_open: On network error or 5xx, let the agent continue (default True).
        extract: Pull reasoning text from the result. Defaults to
            ``choices[0].message.content`` then ``str(result)``.
        action: Pull a tool/action identity from the result for the action
            repetition detector.
        loop_key: Normalize the action identity. Return ``None`` to skip it.
        check_input: Also check the first positional arg / ``prompt`` kwarg.
        on_loop: Callback invoked with the ``CheckStatus`` on detection.
        escalate: Callback invoked with ``(status, attempt)`` when a loop is
            detected and the escalation budget is not exhausted. The wrapped
            call is allowed to continue so you can switch to a stronger model.
        max_escalations: Cap on ``escalate`` calls before stopping.
        model: Static model id, or a callable ``(result) -> str``, recorded for
            attribution.
        prompt: Static prompt/task label, or a callable ``(result) -> str``,
            recorded for attribution.
    """
    key = api_key or os.getenv("INFERENCEBRAKE_API_KEY")
    if not key:
        raise ValueError(
            "guard_agent_loop requires an api_key or the INFERENCEBRAKE_API_KEY env var"
        )

    def decorator(func: Callable) -> Callable:
        guard = InferenceBrake(
            api_key=key,
            supabase_url=supabase_url,
            timeout=timeout,
            auto_stop=False,  # the wrapper controls raising
            fail_open=fail_open,
        )
        policy = LoopPolicy(
            auto_stop=auto_stop,
            max_escalations=max_escalations,
            escalate=escalate,
            on_loop=on_loop,
        )

        def resolve_session(args: tuple, kwargs: dict) -> str:
            if callable(session_id):
                return str(session_id(*args, **kwargs))
            return session_id or f"{func.__module__}.{func.__name__}"

        def evaluate(
            text: Any,
            sid: str,
            raw_action: Optional[str],
            result: Any = None,
        ) -> Optional[CheckStatus]:
            if not text:
                return None

            identity = raw_action
            if identity is not None and loop_key is not None:
                try:
                    identity = loop_key(str(identity))
                except Exception as e:  # never let identity computation crash the run
                    logger.warning("loop_key failed (%s); falling back to raw action", e)

            model_value = model(result) if callable(model) else model
            prompt_value = prompt(result) if callable(prompt) else prompt

            status = guard.check(
                reasoning=str(text),
                session_id=sid,
                action=identity,
                model=model_value,
                prompt=prompt_value,
            )
            policy.handle(status)
            return status

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            sid = resolve_session(args, kwargs)
            if check_input:
                text = kwargs.get("prompt") or (args[0] if args else "")
                evaluate(text, sid, None)

            result = func(*args, **kwargs)

            text = extract(result) if extract else _default_extract(result)
            raw_action = action(result) if action else None
            evaluate(text, sid, raw_action, result)
            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            sid = resolve_session(args, kwargs)
            if check_input:
                text = kwargs.get("prompt") or (args[0] if args else "")
                evaluate(text, sid, None)

            result = await func(*args, **kwargs)

            text = extract(result) if extract else _default_extract(result)
            raw_action = action(result) if action else None
            evaluate(text, sid, raw_action, result)
            return result

        return async_wrapper if inspect.iscoroutinefunction(func) else wrapper

    return decorator


guard = guard_agent_loop


def _default_extract(result: Any) -> str:
    """Best-effort reasoning text from an OpenAI/Anthropic style response."""
    try:
        choice = result.choices[0]
        message = getattr(choice, "message", None)
        if message is not None:
            content = getattr(message, "content", None)
            if content is None and isinstance(message, dict):
                content = message.get("content")
            if content:
                return str(content)
        text = getattr(choice, "text", None)
        if text:
            return str(text)
    except (AttributeError, IndexError, TypeError):
        pass
    return str(result)