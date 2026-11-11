"""Fixed session worker, invoked only under the native isolation boundary."""
import hashlib
import json
import sys
from importlib.metadata import version


def main():
    from tokenizers import Tokenizer
    if version('tokenizers') != '0.21.4':
        raise ValueError
    tokenizers = []
    for path in sys.argv[1:]:
        tokenizer = Tokenizer.from_file(path)
        tokenizer.no_truncation()
        tokenizer.no_padding()
        if tokenizer.truncation is not None or tokenizer.padding is not None:
            raise ValueError
        tokenizers.append(tokenizer)
    print('{"ready":"0.21.4"}', flush=True)
    for line in sys.stdin.buffer:
        request = json.loads(line)
        inputs = json.dumps([request['text'], request['pair']], ensure_ascii=True,
                            separators=(',', ':')).encode()
        digest = hashlib.sha256(inputs).hexdigest()
        count = len(tokenizers[request['artifact']].encode(
            request['text'], request['pair'], add_special_tokens=True).ids)
        response = {key: request[key] for key in ('nonce', 'role', 'artifact')}
        response.update(count=count, digest=digest, version='0.21.4')
        print(json.dumps(response, separators=(',', ':')), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        sys.exit(1)
