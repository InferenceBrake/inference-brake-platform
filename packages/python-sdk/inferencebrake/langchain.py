"""
InferenceBrake LangChain Callback Handler

Detects reasoning loops in LangChain agents using InferenceBrake API.

Installation:
    pip install inferencebrake[langchain]

Usage:
    from inferencebrake import InferenceBrakeCallbackHandler
    
    handler = InferenceBrakeCallbackHandler(
        api_key="ib_xxx",
        supabase_url="https://xxx.supabase.co"
    )
    
    agent = AgentExecutor(
        agent=agent,
        callbacks=[handler]
    )
"""

import os
import logging
from typing import Any, Dict, List, Optional, Callable

import inferencebrake_sdk

logger = logging.getLogger(__name__)


class InferenceBrakeCallbackHandler:
    """LangChain callback handler for loop detection.
    
    Note: Requires langchain-core to be installed.
    Run: pip install langchain-core
    """
    
    def __init__(
        self,
        api_key: str,
        supabase_url: str,
        session_id: Optional[str] = None,
        threshold: float = 0.85,
        auto_stop: bool = True,
        on_loop_detected: Optional[Callable] = None,
    ):
        """
        Initialize the InferenceBrake callback handler.
        
        Args:
            api_key: Your InferenceBrake API key
            supabase_url: Your Supabase project URL
            session_id: Optional session ID (defaults to auto-generated)
            threshold: Similarity threshold for loop detection (default: 0.85)
            auto_stop: Whether to raise exception on loop detected (default: True)
            on_loop_detected: Optional callback function when loop is detected
        """
        self.api_key = api_key
        self.supabase_url = supabase_url
        self.session_id = session_id or f"langchain-{os.urandom(8).hex()}"
        self.threshold = threshold
        self.auto_stop = auto_stop
        self.on_loop_detected = on_loop_detected
        
        self._client = None
        self._step_count = 0
        
        try:
            import langchain_core  # noqa: F401
        except ImportError:
            logger.warning("langchain-core not installed. Install with: pip install langchain-core")
    
    @property
    def client(self):
        """Lazy import and cache the InferenceBrake client."""
        if self._client is None:
            try:
                self._client = inferencebrake_sdk.InferenceBrake(
                    api_key=self.api_key,
                    supabase_url=self.supabase_url,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize InferenceBrake client: {e}")
                return None
        return self._client
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts generating."""
        pass
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when LLM generates a new token."""
        pass
    
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when LLM finishes generating."""
        pass
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM errors."""
        pass
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Called when chain starts."""
        pass
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when chain ends."""
        pass
    
    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when chain errors."""
        pass
    
    def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        """Called when agent takes an action."""
        self._step_count += 1
        
        if not self.client:
            return
        
        reasoning = str(action.log) if hasattr(action, 'log') else str(action)
        
        try:
            status = self.client.check(
                reasoning=reasoning,
                session_id=self.session_id,
                threshold=self.threshold,
            )
            
            if status.should_stop:
                logger.warning(
                    f"InferenceBrake: Loop detected at step {self._step_count}. "
                    f"Similarity: {status.similarity:.2%}, "
                    f"Detectors: {status.detectors}"
                )
                
                if self.on_loop_detected:
                    self.on_loop_detected(status)
                
                if self.auto_stop:
                    raise LoopDetectedError(
                        f"Loop detected: {status.message} "
                        f"(similarity: {status.similarity:.2%})"
                    )
                    
        except Exception as e:
            logger.error(f"InferenceBrake check failed: {e}")
    
    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        """Called when agent finishes."""
        pass
    
    def reset(self, new_session_id: Optional[str] = None) -> None:
        """Reset the session."""
        self._step_count = 0
        if new_session_id:
            self.session_id = new_session_id


class LoopDetectedError(Exception):
    """Raised when a reasoning loop is detected."""
    pass


def create_handler(
    api_key: str,
    supabase_url: str,
    session_id: Optional[str] = None,
    threshold: float = 0.85,
    auto_stop: bool = True,
) -> InferenceBrakeCallbackHandler:
    """Factory function to create an InferenceBrake callback handler."""
    return InferenceBrakeCallbackHandler(
        api_key=api_key,
        supabase_url=supabase_url,
        session_id=session_id,
        threshold=threshold,
        auto_stop=auto_stop,
    )
