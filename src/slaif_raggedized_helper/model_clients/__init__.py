"""Small adapter-injectable model client protocols (no abstract framework)."""

from .base import EmbeddingClient, GeneratorClient, RerankerClient

__all__ = ["EmbeddingClient", "GeneratorClient", "RerankerClient"]
