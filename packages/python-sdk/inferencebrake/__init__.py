"""
InferenceBrake - Loop detection for AI agents

Installation:
    pip install inferencebrake

With LangChain support:
    pip install inferencebrake[langchain]
"""

import inferencebrake_sdk

InferenceBrake = inferencebrake_sdk.InferenceBrake
CheckStatus = inferencebrake_sdk.CheckStatus

__version__ = "0.2.0"
__all__ = ["InferenceBrake", "CheckStatus"]

try:
    from .langchain import InferenceBrakeCallbackHandler, LoopDetectedError
    __all__.append("InferenceBrakeCallbackHandler")
    __all__.append("LoopDetectedError")
except ImportError:
    pass
