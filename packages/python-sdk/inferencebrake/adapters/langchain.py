"""LangChain callback handler for InferenceBrake loop detection.

Subclasses ``langchain_core.callbacks.BaseCallbackHandler`` when available and
hooks ``on_llm_start`` / ``on_llm_end``. If langchain-core is not installed the
module still imports, using a minimal stand-in base class, so the rest of the
SDK keeps working.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Optional

from ..client import CheckStatus, InferenceBrake, LoopDetectedError
from ..policy import LoopPolicy

logger = logging.getLogger(__name__)

try:  # pragma: no cover - depends on optional dependency
    from langchain_core.callbacks import BaseCallbackHandler

    HAS_LANGCHAIN = True
except ImportError:  # pragma: no cover
    HAS_LANGCHAIN = False

    class BaseCallbackHandler:  # type: ignore[no-redef]
        """Minimal stand-in so the handler is importable without langchain-core."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass


class InferenceBrakeCallbackHandler(BaseCallbackHandler):
    """Runs an InferenceBrake check after each LLM completion.

    Example:
        from inferencebrake import InferenceBrakeCallbackHandler

        handler = InferenceBrakeCallbackHandler(api_key="ib_...")
        agent = AgentExecutor(agent=agent, tools=tools, callbacks=[handler])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        supabase_url: Optional[str] = None,
        session_id: Optional[str] = None,
        threshold: Optional[float] = None,
        auto_stop: bool = True,
        fail_open: bool = True,
        action: Optional[Callable[[str], Optional[str]]] = None,
        loop_key: Optional[Callable[[str], Optional[str]]] = None,
        on_loop_detected: Optional[Callable[[CheckStatus], None]] = None,
        escalate: Optional[Callable[[CheckStatus, int], None]] = None,
        max_escalations: int = 2,
        model: Optional[str] = None,
    ) -> None:
        try:
            super().__init__()
        except TypeError:  # pragma: no cover - some base classes reject no-arg init
            pass

        self.api_key = api_key or os.getenv("INFERENCEBRAKE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "InferenceBrakeCallbackHandler requires an api_key or "
                "the INFERENCEBRAKE_API_KEY env var"
            )

        self._client = InferenceBrake(
            api_key=self.api_key,
            supabase_url=supabase_url,
            fail_open=fail_open,
        )
        self.session_id = session_id or f"langchain-{os.urandom(8).hex()}"
        self.threshold = threshold
        self.auto_stop = auto_stop
        self.action = action
        self.loop_key = loop_key
        self.on_loop_detected = on_loop_detected
        self.model = model
        self._policy = LoopPolicy(
            auto_stop=auto_stop,
            max_escalations=max_escalations,
            escalate=escalate,
            on_loop=on_loop_detected,
        )
        self.step_count = 0
        self.last_status: Optional[CheckStatus] = None

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """Called when the LLM starts. Reserved for input-side checks."""
        return None

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when the LLM finishes. Checks the completion for a loop."""
        text = _extract_text(response)
        if not text:
            return

        self.step_count += 1

        identity = self.action(text) if callable(self.action) else None
        if identity is not None and self.loop_key is not None:
            try:
                identity = self.loop_key(str(identity))
            except Exception as e:
                logger.warning("loop_key failed (%s); falling back to raw action", e)

        status = self._client.check(
            reasoning=text,
            session_id=self.session_id,
            threshold=self.threshold,
            action=identity,
            model=self.model,
        )
        self.last_status = status

        if status.should_stop:
            logger.warning(
                "InferenceBrake: loop detected at step %s (confidence %.2f, detectors: %s)",
                self.step_count,
                status.confidence,
                status.detector_triggered or "none",
            )
            self._policy.handle(status)

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        return None

    def reset(self, new_session_id: Optional[str] = None) -> None:
        """Start a new logical session."""
        self.step_count = 0
        self.last_status = None
        self._policy.reset()
        if new_session_id:
            self.session_id = new_session_id


def _extract_text(response: Any) -> Optional[str]:
    """Pull generated text out of a LangChain LLMResult."""
    try:
        generation = response.generations[0][0]
    except (AttributeError, IndexError, TypeError):
        return None

    text = getattr(generation, "text", None)
    if text:
        return str(text)

    message = getattr(generation, "message", None)
    if message is not None:
        content = getattr(message, "content", None)
        if content:
            return str(content)
    return None