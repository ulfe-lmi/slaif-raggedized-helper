"""slaif-raggedized-helper — local contextual retrieval foundation (OAP 002-a).

Strict configuration, typed generator/embedding/reranker contracts, model
lock/qualification schemas and the offline ``raggedized doctor`` command.

Importing this package performs no network I/O, loads no models and imports no
heavy ML stack (Torch/Transformers/SentenceTransformers are not dependencies
of this slice; they belong to later explicit optional groups).
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
