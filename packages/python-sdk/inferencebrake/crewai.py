"""
InferenceBrake CrewAI Callback

Detects reasoning loops in CrewAI agents.

Installation:
    pip install inferencebrake[crewai]

Usage:
    from inferencebrake import create_crewai_callback
    
    callback = create_crewai_callback(
        api_key="ib_xxx",
        supabase_url="https://xxx.supabase.co",
        on_loop_detected=lambda status: print(f"Loop detected: {status.message}")
    )
    
    # Add to your CrewAI agent
    agent.callbacks = [callback]
"""

import os
import logging
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass

import inferencebrake_sdk

logger = logging.getLogger(__name__)


@dataclass
class CrewAICallback:
    """Callback for CrewAI agents."""
    api_key: str
    supabase_url: str
    session_id: str
    threshold: float
    auto_stop: bool
    on_loop_detected: Optional[Callable] = None
    _client: Any = None
    
    def __post_init__(self):
        self._step_count = 0
    
    @property
    def client(self):
        if self._client is None:
            self._client = inferencebrake_sdk.InferenceBrake(
                api_key=self.api_key,
                supabase_url=self.supabase_url,
            )
        return self._client
    
    def on_agent_action(self, agent, action: str) -> None:
        """Called when agent takes an action."""
        self._step_count += 1
        
        if not self.client:
            return
        
        try:
            status = self.client.check(
                reasoning=action,
                session_id=self.session_id,
                threshold=self.threshold,
            )
            
            if status.should_stop:
                logger.warning(
                    f"InferenceBrake: Loop detected at step {self._step_count}"
                )
                
                if self.on_loop_detected:
                    self.on_loop_detected(status)
                
                if self.auto_stop:
                    raise LoopDetectedError(
                        f"Loop detected: {status.message}"
                    )
                    
        except Exception as e:
            logger.error(f"InferenceBrake check failed: {e}")
    
    def reset(self, new_session_id: Optional[str] = None) -> None:
        """Reset the session."""
        self._step_count = 0
        if new_session_id:
            self.session_id = new_session_id


class LoopDetectedError(Exception):
    """Raised when a reasoning loop is detected."""
    pass


def create_crewai_callback(
    api_key: str,
    supabase_url: str,
    session_id: Optional[str] = None,
    threshold: float = 0.85,
    auto_stop: bool = True,
    on_loop_detected: Optional[Callable] = None,
) -> CrewAICallback:
    """Create a CrewAI callback for loop detection."""
    return CrewAICallback(
        api_key=api_key,
        supabase_url=supabase_url,
        session_id=session_id or f"crewai-{os.urandom(8).hex()}",
        threshold=threshold,
        auto_stop=auto_stop,
        on_loop_detected=on_loop_detected,
    )
