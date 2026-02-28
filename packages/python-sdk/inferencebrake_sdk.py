"""
InferenceBrake Python SDK
Semantic loop detection for AI agents using Supabase free embeddings

Installation:
    pip install inferencebrake

Usage:
    from inferencebrake import InferenceBrake
    
    guard = InferenceBrake(api_key="ib_your_key")
    status = guard.check("reasoning text", session_id="agent-1")
"""

import requests
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import os


@dataclass
class CheckStatus:
    """Response from InferenceBrake API"""
    action: str  # "KILL" or "PROCEED"
    loop_detected: bool
    similarity: float
    status: str  # "safe", "warning", or "danger"
    message: str
    confidence: float = 0.0
    action_repeat_count: int = 0
    ngram_overlap: float = 0.0
    detectors: dict = None
    
    def __post_init__(self):
        if self.detectors is None:
            self.detectors = {}
    
    def __repr__(self):
        return f"CheckStatus(action={self.action}, similarity={self.similarity:.2f})"
    
    @property
    def should_stop(self) -> bool:
        """Convenience method to check if agent should stop"""
        return self.action == "KILL"
    
    @property
    def estimated_savings(self) -> float:
        """Placeholder for cost saved calculation (not validated)"""
        return 0.0


class InferenceBrakeError(Exception):
    """Base exception for InferenceBrake SDK"""
    pass


class RateLimitError(InferenceBrakeError):
    """Raised when rate limit is exceeded"""
    pass


class AuthenticationError(InferenceBrakeError):
    """Raised when API key is invalid"""
    pass


class InferenceBrake:
    """
    InferenceBrake client for detecting semantic loops in AI agent reasoning.
    
    Uses Supabase's free gte-small embedding model (384 dimensions) for
    zero-cost loop detection.
    
    Example:
        >>> from inferencebrake import InferenceBrake
        >>> 
        >>> guard = InferenceBrake(api_key="ib_your_key")
        >>> 
        >>> for step in agent.run():
        ...     status = guard.check(
        ...         reasoning=step.reasoning,
        ...         session_id="agent-session-123"
        ...     )
        ...     
        ...     if status.should_stop:
        ...         print(f"Loop detected! Similarity: {status.similarity}")
        ...         break
    """
    
    def __init__(
        self,
        api_key: str,
        supabase_url: Optional[str] = None,
        timeout: int = 10,
        auto_stop: bool = False
    ):
        """
        Initialize InferenceBrake client.
        
        Args:
            api_key: Your InferenceBrake API key (get one at inferencebrake.dev)
            supabase_url: Your Supabase project URL (if self-hosting)
            timeout: Request timeout in seconds (default: 10)
            auto_stop: If True, raise exception when loop is detected
        """
        self.api_key = api_key
        
        # Allow custom Supabase URL or use environment variable
        self.supabase_url = supabase_url or os.getenv('INFERENCEBRake_URL')
        
        if not self.supabase_url:
            raise InferenceBrakeError(
                "Supabase URL required. Either pass supabase_url parameter "
                "or set INFERENCEBRake_URL environment variable"
            )
        
        # Construct edge function URL
        self.base_url = f"{self.supabase_url}/functions/v1"
        self.timeout = timeout
        self.auto_stop = auto_stop
        
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def check(
        self,
        reasoning: str,
        session_id: str,
        threshold: Optional[float] = None
    ) -> CheckStatus:
        """
        Check if the current reasoning step indicates a loop.
        
        Args:
            reasoning: The agent's current reasoning/thought process
            session_id: Unique identifier for this agent session
            threshold: Custom similarity threshold (default: 0.85)
        
        Returns:
            CheckStatus object with detection results
        
        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            InferenceBrakeError: For other API errors
        """
        url = f"{self.base_url}/check"
        
        payload = {
            "reasoning": reasoning,
            "session_id": session_id
        }
        
        if threshold is not None:
            payload["threshold"] = threshold
        
        try:
            response = self._session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            
            if response.status_code == 429:
                raise RateLimitError(
                    "Rate limit exceeded. Upgrade your plan at inferencebrake.dev/pricing"
                )
            
            if response.status_code != 200:
                error_msg = response.json().get('error', 'Unknown error')
                raise InferenceBrakeError(f"API error: {response.status_code} - {error_msg}")
            
            data = response.json()
            status = CheckStatus(
                action=data["action"],
                loop_detected=data["loop_detected"],
                similarity=data["similarity"],
                status=data["status"],
                message=data["message"],
                confidence=data.get("confidence", 0.0),
                action_repeat_count=data.get("action_repeat_count", 0),
                ngram_overlap=data.get("ngram_overlap", 0.0),
                detectors=data.get("detectors", {})
            )
            
            if self.auto_stop and status.should_stop:
                raise InferenceBrakeError(
                    f"Loop detected: {status.message} "
                    f"(similarity: {status.similarity:.2f})"
                )
            
            return status
            
        except requests.exceptions.Timeout:
            raise InferenceBrakeError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise InferenceBrakeError(f"Request failed: {str(e)}")
    
    def check_batch(
        self,
        reasoning_list: List[str],
        session_id: str
    ) -> List[CheckStatus]:
        """
        Check multiple reasoning steps in batch.
        
        Args:
            reasoning_list: List of reasoning texts
            session_id: Session identifier
        
        Returns:
            List of CheckStatus objects
        """
        results = []
        for reasoning in reasoning_list:
            status = self.check(reasoning, session_id)
            results.append(status)
            
            # Stop batch if loop detected
            if status.should_stop:
                break
        
        return results
    
    def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get reasoning history for a session.
        
        Args:
            session_id: Session identifier
            limit: Max number of steps to return
        
        Returns:
            List of reasoning steps with metadata
        """
        # Note: This would require additional endpoint in Supabase Edge Function
        url = f"{self.base_url}/session/{session_id}"
        
        try:
            response = self._session.get(
                url,
                params={"limit": limit},
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            
            if response.status_code != 200:
                raise InferenceBrakeError(f"API error: {response.status_code}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise InferenceBrakeError(f"Request failed: {str(e)}")
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self._session.close()


# ============================================
# DECORATORS FOR EASY INTEGRATION
# ============================================

def inferencebrake_monitor(
    api_key: str,
    supabase_url: str,
    session_id: Optional[str] = None
):
    """
    Decorator to automatically monitor agent functions for loops.
    
    Example:
        >>> @inferencebrake_monitor(
        ...     api_key="ib_your_key",
        ...     supabase_url="https://xxx.supabase.co"
        ... )
        ... def agent_step(reasoning: str):
        ...     # Your agent logic here
        ...     return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract reasoning from args/kwargs
            reasoning = kwargs.get('reasoning') or (args[0] if args else "")
            
            # Generate session_id if not provided
            sid = session_id or f"auto-{int(time.time())}"
            
            # Check for loop
            guard = InferenceBrake(api_key=api_key, supabase_url=supabase_url)
            status = guard.check(reasoning=str(reasoning), session_id=sid)
            
            if status.should_stop:
                print(f"Warning: {status.message}")
                return None
            
            # Continue with function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================
# LANGCHAIN INTEGRATION
# ============================================

class InferenceBrakeCallback:
    """
    LangChain callback handler for InferenceBrake.
    
    Example:
        >>> from langchain.callbacks import CallbackManager
        >>> from inferencebrake import InferenceBrakeCallback
        >>> 
        >>> callback = InferenceBrakeCallback(
        ...     api_key="ib_your_key",
        ...     supabase_url="https://xxx.supabase.co"
        ... )
        >>> manager = CallbackManager([callback])
        >>> 
        >>> agent = initialize_agent(tools, llm, callbacks=manager)
    """
    
    def __init__(
        self,
        api_key: str,
        supabase_url: str,
        session_id: Optional[str] = None
    ):
        self.guard = InferenceBrake(api_key=api_key, supabase_url=supabase_url)
        self.session_id = session_id or f"langchain-{int(time.time())}"
        self.step_count = 0
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Called when LLM starts"""
        pass
    
    def on_llm_end(self, response, **kwargs):
        """Called when LLM completes"""
        self.step_count += 1
        
        # Extract reasoning from response
        if hasattr(response, 'generations'):
            text = response.generations[0][0].text
        else:
            text = str(response)
        
        # Check for loop
        status = self.guard.check(
            reasoning=text,
            session_id=self.session_id
        )
        
        if status.should_stop:
            raise InferenceBrakeError(
                f"Loop detected at step {self.step_count}: {status.message}"
            )
    
    def on_chain_error(self, error, **kwargs):
        """Called when chain errors"""
        pass


# ============================================
# CLI TOOL
# ============================================

def cli():
    """Command-line interface for InferenceBrake"""
    import argparse
    
    parser = argparse.ArgumentParser(description="InferenceBrake CLI")
    parser.add_argument('--api-key', required=True, help='Your API key')
    parser.add_argument('--url', required=True, help='Supabase URL')
    parser.add_argument('--session', required=True, help='Session ID')
    parser.add_argument('--reasoning', required=True, help='Reasoning text to check')
    parser.add_argument('--threshold', type=float, help='Custom threshold')
    
    args = parser.parse_args()
    
    guard = InferenceBrake(api_key=args.api_key, supabase_url=args.url)
    status = guard.check(
        reasoning=args.reasoning,
        session_id=args.session,
        threshold=args.threshold
    )
    
    print(f"Action: {status.action}")
    print(f"Loop Detected: {status.loop_detected}")
    print(f"Similarity: {status.similarity:.2%}")
    print(f"Status: {status.status}")
    print(f"Message: {status.message}")
    
    if status.should_stop:
        exit(1)
    
    exit(0)


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    # Example usage
    SUPABASE_URL = "https://yourproject.supabase.co"
    API_KEY = "ib_your_api_key_here"
    
    guard = InferenceBrake(api_key=API_KEY, supabase_url=SUPABASE_URL)
    
    # Simulate agent loop
    session_id = "example-session"
    
    reasoning_steps = [
        "I need to search for weather in NYC",
        "Let me call the weather API for NYC",
        "I should check the weather in New York City",  # Similar!
        "I need to get weather data for NYC",  # Loop will be detected!
    ]
    
    for i, reasoning in enumerate(reasoning_steps, 1):
        print(f"\n{'='*60}")
        print(f"Step {i}: {reasoning}")
        print('='*60)
        
        status = guard.check(
            reasoning=reasoning,
            session_id=session_id
        )
        
        print(f"Action: {status.action}")
        print(f"Similarity: {status.similarity:.2%}")
        print(f"Status: {status.status}")
        
        if status.should_stop:
            print(f"\nLOOP DETECTED!")
            print(f"Message: {status.message}")
            break
        else:
            print("Safe to continue")
