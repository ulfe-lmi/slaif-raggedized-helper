"""Fixed data-only worker; invoked exclusively inside the native sandbox."""
import hashlib
import json
import re
import sys
from importlib.metadata import version


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def main():
    from tokenizers import Tokenizer

    if len(sys.argv) != 2 or sys.argv[1] != '/artifact.json' or version('tokenizers') != '0.21.4':
        raise ValueError
    tokenizer = Tokenizer.from_file(sys.argv[1])
    tokenizer.no_truncation()
    tokenizer.no_padding()
    if tokenizer.truncation is not None or tokenizer.padding is not None:
        raise ValueError
    print('{"ready":"0.21.4"}', flush=True)
    total_input = total_output = calls = 0
    while True:
        line = sys.stdin.buffer.readline(200_001)
        if not line:
            return
        total_input += len(line)
        calls += 1
        if (len(line) > 200_000 or not line.endswith(b'\n')
                or total_input > 32_000_000 or calls > 1024):
            raise ValueError
        request = json.loads(line.decode('utf-8', 'strict'), object_pairs_hook=unique,
                             parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if (type(request) is not dict or set(request) != {'text', 'nonce'}
                or type(request['text']) is not str or len(request['text']) > 100_000
                or type(request['nonce']) is not str
                or not re.fullmatch('[0-9a-f]{32}', request['nonce'])):
            raise ValueError
        request['text'].encode('utf-8', 'strict')
        inputs = json.dumps([request['text'], None], ensure_ascii=True,
                            separators=(',', ':')).encode()
        ids = tokenizer.encode(request['text'], add_special_tokens=True).ids
        if (not 2 <= len(ids) <= 1024
                or any(type(x) is not int or not 0 <= x <= 2**31 - 1 for x in ids)):
            raise ValueError
        response = {'nonce': request['nonce'], 'count': len(ids), 'ids': ids,
                    'digest': hashlib.sha256(inputs).hexdigest(), 'version': '0.21.4'}
        wire = json.dumps(response, separators=(',', ':')).encode() + b'\n'
        total_output += len(wire)
        if len(wire) > 16_384 or total_output > 16_000_000:
            raise ValueError
        sys.stdout.buffer.write(wire)
        sys.stdout.buffer.flush()


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        sys.exit(1)
