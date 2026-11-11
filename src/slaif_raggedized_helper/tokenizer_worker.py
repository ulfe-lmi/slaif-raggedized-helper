"""Fixed worker; only launched inside the configured OS sandbox."""
import json
import os
import sys
from importlib.metadata import version


def main():
    try:
        with open('/request.json', encoding='utf-8') as source:
            request = json.load(source)
        if version('tokenizers') != request['version']:
            raise ValueError
        from tokenizers import Tokenizer
        tokenizer = Tokenizer.from_file('/artifact.json')
        tokenizer.no_truncation()
        tokenizer.no_padding()
        if tokenizer.truncation is not None or tokenizer.padding is not None:
            raise ValueError
        encoded = tokenizer.encode(request['text'], request['pair'], add_special_tokens=True)
        sys.stdout.write(json.dumps({'nonce': request['nonce'], 'count': len(encoded.ids),
                                     'version': request['version']}, separators=(',', ':')))
        return 0
    except BaseException:
        try:
            os.write(1, b'{"error":"refused"}')
        except OSError:
            pass
        return 1


if __name__ == '__main__':
    sys.exit(main())
