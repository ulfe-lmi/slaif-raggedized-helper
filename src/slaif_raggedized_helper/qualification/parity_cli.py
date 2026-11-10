"""Operator-local supplied-value parity analysis; no model or network access."""

from __future__ import annotations

import argparse
import sys

from . import embedding_parity, parity_io, rerank_parity


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise parity_io.Refusal("invalid arguments")


def main(argv=None):
    parser = Parser(description="Analyze explicitly supplied, unverified parity values")
    parser.add_argument("kind", choices=("embedding", "rerank"))
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-supplied-input", action="store_true")
    try:
        args = parser.parse_args(argv)
        if not args.allow_supplied_input:
            raise parity_io.Refusal("explicit input opt-in required")
        document = parity_io.read_document(args.input)
        parity_io.preflight_output(args.output)
        analyzer = (
            embedding_parity.analyze
            if args.kind == "embedding"
            else rerank_parity.analyze_rerank_parity
        )

        def run(value):
            result = analyzer(value)
            return {
                "version": 1,
                "kind": args.kind,
                "input_sha256": document.sha256,
                "input_bytes": document.byte_count,
                "analysis": result,
                "real_qualification": "NOT_RUN",
            }

        try:
            evidence = parity_io.run_export(document.document, run, args.output)
        except parity_io.ExportError as error:
            try:
                payload = parity_io.render_json(
                    {"error": "export failed after analysis", "evidence": error.evidence}
                )
            except parity_io.Refusal:
                payload = b'{"error":"export failed after analysis","evidence_available":false}'
            sys.stdout.buffer.write(payload + b"\n")
            return 3
        sys.stdout.buffer.write(parity_io.render_json(evidence) + b"\n")
        return 0
    except (parity_io.Refusal, embedding_parity.ParityError, rerank_parity.ParityError):
        sys.stderr.write('{"error":"input or configuration refused"}\n')
        return 2


if __name__ == "__main__":
    sys.exit(main())
