import copy
import json
from dataclasses import FrozenInstanceError

import pytest

from slaif_raggedized_helper import raw_snapshot_lexical as lex
from slaif_raggedized_helper.embedding_vectors import POLICY_ID


def payload():
    return dict(schema=1, kind='slaif-raw-lexical-v1', partition_id='sha256:'+'1'*64,
        row_map_sha256='2'*64, space_id='3'*64, definition_fingerprint='sha256:'+'4'*64,
        representation_policy_fingerprint='5'*64, chunk_policy_fingerprint='6'*64,
        normalization_policy_id=POLICY_ID, analyzer_fingerprint='7'*64,
        rows=[dict(ordinal=2, partition_row=0, chunk_id='sha256:'+'8'*64,
                   representation_id='9'*64, rendered_sha256='a'*64,
                   terms=[dict(text='α', start=0, end=1, derivation='literal')])])


def wire(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()


def test_detached_frozen_data_and_historical_fingerprint():
    data = wire(payload())
    result = lex.parse(data)
    assert result.record_bytes == data and result.rows[0].terms[0].text == 'α'
    with pytest.raises(FrozenInstanceError):
        result.rows[0].terms[0].text = 'other'


@pytest.mark.parametrize('mutate', [
    lambda o: o.update(extra=1), lambda o: o.update(schema=True),
    lambda o: o.update(partition_id='0'*64), lambda o: o.update(analyzer_fingerprint='A'*64),
    lambda o: o.update(normalization_policy_id='other'), lambda o: o.update(rows=[]),
    lambda o: o['rows'][0].update(ordinal=True),
    lambda o: o['rows'][0].update(partition_row=1),
    lambda o: o['rows'][0]['terms'][0].update(start=1),
    lambda o: o['rows'][0]['terms'][0].update(derivation='other'),
    lambda o: o['rows'][0]['terms'][0].update(text='\ud800'),
    lambda o: o['rows'].append(copy.deepcopy(o['rows'][0])),
])
def test_bad_shape(mutate):
    obj = payload()
    mutate(obj)
    with pytest.raises(lex.LexicalError):
        lex.parse(wire(obj))


def test_noncanonical_duplicate_and_large():
    data = wire(payload())
    for bad in (data+b'\n', data.replace(b'{', b'{"schema":1,', 1), b'x'*(16*1048576+1)):
        with pytest.raises(lex.LexicalError):
            lex.parse(bad)
