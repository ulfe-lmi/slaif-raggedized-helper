"""Adapter-injectable client protocols (deliberately small; no framework).

These are structural :class:`typing.Protocol` contracts so concrete adapters
(gateway HTTP, later direct offline, or fakes in tests) can be injected without
inheritance. Importing this module loads no heavy ML stack and performs no I/O.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from ..schema import (
    EmbeddingDefinition,
    GeneratorRequest,
    GeneratorResult,
    ModelIdentity,
    RerankRequest,
    RerankResult,
)


@runtime_checkable
class GeneratorClient(Protocol):
    """One semantic generator for annotation/visual/answer purposes."""

    identity: ModelIdentity

    def generate(self, request: GeneratorRequest) -> GeneratorResult:
        """Produce one bounded semantic result for ``request``.

        Must not raise for an expected terminal/refusal/failure; unexpected
        errors are the adapter's responsibility to map to a safe result or
        propagate as an explicit failure.
        """
        ...


@runtime_checkable
class EmbeddingClient(Protocol):
    """Embedding encoder bound to one definition and execution shape."""

    definition: EmbeddingDefinition

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one finite normalized vector per input, in order."""
        ...


@runtime_checkable
class RerankerClient(Protocol):
    """Cross-encoder reranker returning finite scores bound to pair IDs."""

    def rerank(self, request: RerankRequest) -> RerankResult:
        """Return exactly one finite score for each submitted pair ID."""
        ...
