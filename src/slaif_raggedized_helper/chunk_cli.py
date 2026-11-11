"""Installed private chunk and inspect commands."""

import argparse
import json
import sys
import time

from . import ingestion_prepare, ingestion_profile


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError


def main(argv=None):
    end = time.monotonic() + 180
    parser = Parser(prog='raggedized chunk')
    parser.add_argument('--original-store', required=True)
    parser.add_argument('--derived-store', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--adapter', required=True, choices=('structured_text', 'pdf_extraction'))
    parser.add_argument('--profile', required=True)
    parser.add_argument('--query', default='')
    inspect_parser = Parser(prog='raggedized chunk inspect')
    inspect_parser.add_argument('--original-store', required=True)
    inspect_parser.add_argument('--derived-store', required=True)
    inspect_parser.add_argument('--bundle', required=True)
    args = sys.argv[1:] if argv is None else argv
    try:
        if args and args[0] == 'inspect':
            parsed = inspect_parser.parse_args(args[1:])
            result = ingestion_prepare.inspect(parsed.original_store, parsed.derived_store,
                                               parsed.bundle, end)
        else:
            parsed = parser.parse_args(args)
            if len(parsed.query) > 10000:
                raise ValueError
            parsed.query.encode('utf-8')
            profile = ingestion_profile.load_profile(parsed.profile)
            result = ingestion_prepare.prepare(parsed.original_store, parsed.derived_store,
                                               parsed.revision, parsed.adapter, profile,
                                               parsed.query, end)
        try:
            output = json.dumps(result, sort_keys=True)
        except (TypeError, ValueError, OverflowError):
            raise ingestion_prepare.PrepareError(result.get('bundle_id')) from None
        if len(output) > 65536 or time.monotonic() >= end:
            raise ingestion_prepare.PrepareError(result.get('bundle_id'))
        print(output)
        return 1 if result['status'] == 'no_native_chunks' else 0
    except (ValueError, UnicodeError, ingestion_profile.ProfileError) as exc:
        if isinstance(exc, ingestion_prepare.PrepareError):
            result = {'error': 'ingestion_failed'}
            if exc.published_bundle_id:
                result['published_bundle_id'] = exc.published_bundle_id
            print(json.dumps(result, sort_keys=True))
            return 1
        print(json.dumps({'error': 'invalid_input'}))
        return 2
