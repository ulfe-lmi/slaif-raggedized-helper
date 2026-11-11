"""Native counts remain supplied, unqualified chunking callbacks."""
from pathlib import Path
import hashlib

import pytest

from slaif_raggedized_helper import chunking
from slaif_raggedized_helper import native_tokenizers as n


def test_independent_callbacks_are_unqualified():
    root = Path('/tmp/slaif-tokenizer-spike-006')
    packages = root / 'venv/lib/python3.14/site-packages'
    a, b = root / 'a.json', root / 'b.json'
    if not a.exists() or not b.exists() or not packages.exists():
        pytest.skip('development-only fixtures unavailable')
    runtime = n.Runtime(Path('/usr'), packages)
    def definition(path, role):
        return n.Definition(path, hashlib.sha256(path.read_bytes()).hexdigest(), '0.21.4',
                            role, 'fixture', 'identity')
    body = definition(a, 'bge_body')
    representation = definition(a, 'bge_representation')
    pair = definition(b, 'reranker_pair')
    counters = chunking.Counters('body', 'representation', 'pair',
                                lambda t: n.count(body, runtime, t).count,
                                lambda t: n.count(representation, runtime, t).count,
                                lambda q, p: n.count(pair, runtime, q, p).count)
    assert counters.provenance == 'SUPPLIED_UNVERIFIED'
    assert counters.body('hello café 世界') == 5
    assert counters.pair('hello', 'café 世界') == 7
