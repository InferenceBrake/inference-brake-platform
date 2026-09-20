"""
InferenceBrake - Loop detection for AI agents

Installation:
    pip install inferencebrake

With LangChain support:
    pip install inferencebrake[langchain]
"""

from .client import (
    AuthenticationError,
    CheckStatus,
    DoomLoopException,
    InferenceBrake,
    InferenceBrakeCallback,
    InferenceBrakeError,
    LoopDetectedError,
    RateLimitError,
    inferencebrake_monitor,
)
from .decorators import guard, guard_agent_loop, loop_key
from .policy import STEERING_MESSAGE, LoopPolicy, steering_message
from .adapters import (
    CrewAICallback,
    InferenceBrakeCallbackHandler,
    create_crewai_callback,
)

# CheckStatus is the typed response returned by every check. Status is an alias.
Status = CheckStatus

__version__ = "0.6.0"
__all__ = [
    "InferenceBrake",
    "CheckStatus",
    "Status",
    "InferenceBrakeError",
    "AuthenticationError",
    "RateLimitError",
    "LoopDetectedError",
    "DoomLoopException",
    "LoopPolicy",
    "STEERING_MESSAGE",
    "steering_message",
    "inferencebrake_monitor",
    "InferenceBrakeCallback",
    "guard_agent_loop",
    "guard",
    "loop_key",
    "InferenceBrakeCallbackHandler",
    "CrewAICallback",
    "create_crewai_callback",
]