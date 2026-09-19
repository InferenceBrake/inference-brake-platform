"""
InferenceBrake - Loop detection for AI agents

Installation:
    pip install inferencebrake

With LangChain support:
    pip install inferencebrake[langchain]
"""

from .client import (
    InferenceBrake,
    CheckStatus,
    InferenceBrakeError,
    AuthenticationError,
    RateLimitError,
    inferencebrake_monitor,
    InferenceBrakeCallback,
)

__version__ = "0.3.0"
__all__ = [
    "InferenceBrake",
    "CheckStatus",
    "InferenceBrakeError",
    "AuthenticationError",
    "RateLimitError",
    "inferencebrake_monitor",
    "InferenceBrakeCallback",
]

try:
    from .langchain import InferenceBrakeCallbackHandler, LoopDetectedError
    __all__.extend(["InferenceBrakeCallbackHandler", "LoopDetectedError"])
except ImportError:
    pass

try:
    from .crewai import CrewAICallback, create_crewai_callback
    __all__.extend(["CrewAICallback", "create_crewai_callback"])
except ImportError:
    pass
