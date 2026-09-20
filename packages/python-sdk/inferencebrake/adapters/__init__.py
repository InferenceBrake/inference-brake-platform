"""Framework adapters for InferenceBrake.

Each adapter is optional: importing this package does not require the framework
to be installed. Install extras as needed, e.g. ``pip install inferencebrake[langchain]``.
"""

from .langchain import InferenceBrakeCallbackHandler
from .crewai import CrewAICallback, create_crewai_callback

__all__ = [
    "InferenceBrakeCallbackHandler",
    "CrewAICallback",
    "create_crewai_callback",
]