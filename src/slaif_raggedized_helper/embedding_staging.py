"""Private, temporary staging of an admitted embedding inventory."""

import hashlib
import math
import os
import shutil
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path

from . import embedding_artifacts as artifacts, embedding_space


@dataclass(frozen=True)
class Staged:
    path: Path
    manifest_bytes: bytes
    space: embedding_space.AdmittedSpace


@contextmanager
def stage(manifest_bytes, artifact_root, definition, tokenizer_definition,
          expected_inventory_id, *, parent=None, timeout=120):
    """Yield a verified private copy for the lifetime of this context."""
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 120:
        raise ValueError("staging refused")
    deadline = time.monotonic() + timeout

    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise ValueError("staging refused")
        return min(value, 30)

    stage_path = None
    root = None
    try:
        space = embedding_space.admit(manifest_bytes, artifact_root, definition,
                                      tokenizer_definition, expected_inventory_id,
                                      timeout=remaining())
        _, files, _, _ = artifacts._admit(manifest_bytes)
        if parent is not None:
            parent_fd = artifacts._root(parent)
            try:
                st = os.fstat(parent_fd)
                if st.st_uid != os.geteuid() or st.st_mode & 0o077:
                    raise ValueError("staging refused")
            finally:
                os.close(parent_fd)
        stage_path = Path(tempfile.mkdtemp(prefix="embedding-stage-", dir=parent))
        root = artifacts._root(artifact_root)
        for item in files:
            remaining()
            target = stage_path / item.path
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            fd = artifacts._open_file(root, item.path)
            try:
                before = os.fstat(fd)
                digest = hashlib.sha256()
                count = 0
                with target.open("xb") as out:
                    os.chmod(target, 0o600)
                    while True:
                        remaining()
                        chunk = os.read(fd, 65536)
                        if not chunk:
                            break
                        count += len(chunk)
                        if count > item.size:
                            raise ValueError("staging refused")
                        digest.update(chunk)
                        out.write(chunk)
                if (count != item.size or digest.hexdigest() != item.sha256 or
                        artifacts._signature(before) != artifacts._signature(os.fstat(fd))):
                    raise ValueError("staging refused")
            finally:
                os.close(fd)
        staged_space = embedding_space.admit(
            manifest_bytes, stage_path, definition,
            replace(tokenizer_definition, artifact=stage_path / "tokenizer.json"),
            expected_inventory_id, timeout=remaining())
        if staged_space != space:
            raise ValueError("staging refused")
        for item in files:
            (stage_path / item.path).chmod(0o400)
        for directory, _, _ in os.walk(stage_path, topdown=False):
            os.chmod(directory, 0o500)
        yield Staged(stage_path, manifest_bytes, staged_space)
    finally:
        if root is not None:
            os.close(root)
        if stage_path is not None:
            for directory, _, _ in os.walk(stage_path):
                os.chmod(directory, 0o700)
            shutil.rmtree(stage_path)
