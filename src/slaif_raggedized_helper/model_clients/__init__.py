"""Adapter-injectable model client protocols and concrete adapters.

The protocols are deliberately small (no framework); the concrete adapters
(gateway ``/v1/responses``, private offline native ``/completion``) are
exported for direct injection. Importing this module loads no heavy ML
stack and performs no I/O.
"""

from .base import EmbeddingClient, GeneratorClient, RerankerClient
from .direct import DirectNativeGenerator
from .gateway import GatewayGenerator

__all__ = [
    "DirectNativeGenerator",
    "EmbeddingClient",
    "GeneratorClient",
    "GatewayGenerator",
    "RerankerClient",
]
