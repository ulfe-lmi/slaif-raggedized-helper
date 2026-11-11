"""Private publication and fresh semantic verification of native bundles."""

import time

from . import derived_store, ingestion_bundle
from .source_admission import OriginalStore


class IngestionStoreError(ValueError):
    """Input-free refusal of publication or load."""


def _check(end):
    if time.monotonic() >= end:
        raise ValueError


def _stores(originals, derived):
    if type(originals) is not OriginalStore or type(derived) is not derived_store.Store:
        raise ValueError


def publish(originals, derived, metadata, members):
    """Validate against the original, then publish canonical bytes."""
    end = time.monotonic() + 60
    try:
        _stores(originals, derived)
        _check(end)
        value = ingestion_bundle.validate(originals, metadata, members)
        _check(end)
        fixed = tuple(derived_store.Member(name, data) for name, data in value.members)
        ident = derived.publish(value.metadata_json, fixed)
        _check(end)
        return ident
    except Exception:
        raise IngestionStoreError('ingestion store refused') from None


def load(originals, derived, container_id):
    """Verify container integrity and revalidate against the current original."""
    end = time.monotonic() + 60
    try:
        _stores(originals, derived)
        if type(container_id) is not str or not derived_store.HEX.fullmatch(container_id):
            raise ValueError
        _check(end)
        snapshot = derived.load(container_id)
        _check(end)
        manifest = derived_store._parse(snapshot.manifest)
        metadata = derived_store._encode(manifest['metadata'])
        members = tuple((member.name, member.data) for member in snapshot.members)
        _check(end)
        value = ingestion_bundle.validate(originals, metadata, members)
        _check(end)
        return value
    except Exception:
        raise IngestionStoreError('ingestion store refused') from None
