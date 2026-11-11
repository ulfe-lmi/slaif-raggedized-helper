"""Private operator-local original import and inspection; no source serving."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

from .source_admission import AdmissionError, MAX_MANIFEST, OriginalStore, _changed, parse_manifest


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError("invalid arguments")


def _manifest_bytes(path: str) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_MANIFEST:
            raise ValueError
        data = bytearray()
        while len(data) <= MAX_MANIFEST:
            part = os.read(fd, min(65536, MAX_MANIFEST + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        if (
            len(data) > MAX_MANIFEST
            or len(data) != before.st_size
            or _changed(before, os.fstat(fd))
        ):
            raise ValueError
        return bytes(data)
    finally:
        os.close(fd)


def _parser() -> Parser:
    parser = Parser(description="Import or inspect local originals in a private operator store.")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    imp = commands.add_parser("import", help="Import an approved manifest")
    imp.add_argument("--root", required=True, help="Operator-approved source directory")
    imp.add_argument("--store", required=True, help="Private local store directory")
    imp.add_argument("--manifest", required=True, help="Manifest JSON file")
    inspect = commands.add_parser("inspect", help="Inspect a stored revision")
    inspect.add_argument("--store", required=True, help="Private local store directory")
    inspect.add_argument("--revision", required=True, help="Revision fingerprint")
    return parser


def main(argv: list[str] | None = None) -> int:
    completed: list[str] = []
    stage = "arguments"
    store = None
    try:
        args = _parser().parse_args(argv)
        if args.command == "import":
            stage = "manifest"
            manifest = parse_manifest(_manifest_bytes(args.manifest))
            if any(not source.processing_approved for source in manifest.sources):
                raise ValueError
            stage = "root"
            root_fd = os.open(args.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            os.close(root_fd)
            stage = "store"
            store = OriginalStore(Path(args.store))
            stage = "import"
            for source in manifest.sources:
                completed.append(store.admit(Path(args.root), source).revision_id)
            print(json.dumps({"status": "complete", "revisions": completed}))
        else:
            stage = "store"
            store = OriginalStore(Path(args.store))
            stage = "inspect"
            revision = store.inspect(args.revision)
            print(
                json.dumps(
                    {"status": "complete", "revision": revision.model_dump(mode="json")},
                    ensure_ascii=True,
                )
            )
        return 0
    except (AdmissionError, ValueError, TypeError, OSError, UnicodeError, RecursionError):
        print(
            json.dumps(
                {
                    "status": "failed",
                    "stage": stage,
                    "completed_revisions": completed,
                    "current_document": "unknown" if stage == "import" else None,
                }
            ),
            file=sys.stderr,
        )
        return 1
    finally:
        if store is not None:
            store.close()


if __name__ == "__main__":
    sys.exit(main())
