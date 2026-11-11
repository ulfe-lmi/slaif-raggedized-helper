import pytest

from slaif_raggedized_helper import ingestion_bundle as b
from slaif_raggedized_helper.source_admission import OriginalStore


@pytest.mark.parametrize('case', ['metadata_type', 'metadata_cap', 'members_type', 'count',
                                 'member_type', 'member_shape', 'name_type', 'order',
                                 'payload_type', 'total'] +
                         [f'{kind}{i}' for kind in ('cap', 'name', 'type') for i in range(5)])
def test_raw_refusal_precedes_parse(monkeypatch, case):
    store = object.__new__(OriginalStore)
    metadata = b'{}'
    members = [(name, b'') for name in b.NAMES]
    caps = (4,) * 5
    monkeypatch.setattr(b, 'CAPS', caps)
    monkeypatch.setattr(b, 'METADATA_BYTES', 4)
    monkeypatch.setattr(b, 'TOTAL_BYTES', 22)
    if case == 'metadata_type':
        metadata = bytearray(metadata)
    elif case == 'metadata_cap':
        metadata = b'x' * 5
    elif case == 'members_type':
        members = list(members)
    elif case == 'count':
        members.pop()
    elif case == 'member_type':
        members[0] = list(members[0])
    elif case == 'member_shape':
        members[0] = ('blocks',)
    elif case == 'name_type':
        members[0] = (b'blocks', b'')
    elif case == 'order':
        members.reverse()
    elif case == 'payload_type':
        members[0] = ('blocks', bytearray())
    elif case == 'total':
        members = [(name, b'x' * 4) for name in b.NAMES]
        metadata = b'xxx'
    elif case.startswith('cap'):
        i = int(case[-1])
        members[i] = (b.NAMES[i], b'x' * 5)
    elif case.startswith('type'):
        i = int(case[-1])
        members[i] = (b.NAMES[i], bytearray())
    else:
        i = int(case[-1])
        members[i] = ('wrong', b'')
    if case != 'members_type':
        members = tuple(members)
    calls = []
    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise ValueError
    monkeypatch.setattr(b.native, '_parse', forbidden)
    monkeypatch.setattr(b.source, 'validate', forbidden)
    monkeypatch.setattr(b.native, 'validate', forbidden)
    with pytest.raises(b.BundleError, match='^ingestion bundle refused$'):
        b.validate(store, metadata, members)
    assert calls == []


def test_exact_raw_caps_are_admitted_to_parser(monkeypatch):
    monkeypatch.setattr(b, 'METADATA_BYTES', 4)
    monkeypatch.setattr(b, 'CAPS', (4,) * 5)
    monkeypatch.setattr(b, 'TOTAL_BYTES', 24)
    calls = []
    def parser(*args):
        calls.append(args)
        raise ValueError
    monkeypatch.setattr(b.native, '_parse', parser)
    with pytest.raises(b.BundleError, match='^ingestion bundle refused$'):
        b.validate(object.__new__(OriginalStore), b'xxxx',
                   tuple((name, b'xxxx') for name in b.NAMES))
    assert len(calls) == 1


@pytest.mark.parametrize('metadata', [
    b'{"schema_version":1,"kind":"native-ingestion-bundle","revision_id":"x",'
    b'"extraction":{},"chunking":{},"counts":{"blocks":true,"chunks":1,'
    b'"neighbors":1,"receipts":3}}',
    b'{"schema_version":1,"kind":"native-ingestion-bundle","revision_id":"x",'
    b'"extraction":{},"chunking":{},"counts":{"blocks":4097,"chunks":1,'
    b'"neighbors":1,"receipts":3}}',
    b'[' * 100 + b'0' + b']' * 100,
    b'[' + b','.join([b'0'] * 21000) + b']',
])
def test_metadata_refusal_before_source_or_native(monkeypatch, metadata):
    calls = []
    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise ValueError
    monkeypatch.setattr(b.source, 'validate', forbidden)
    monkeypatch.setattr(b.native, 'validate', forbidden)
    with pytest.raises(b.BundleError, match='^ingestion bundle refused$'):
        b.validate(object.__new__(OriginalStore), metadata,
                   tuple((name, b'') for name in b.NAMES))
    assert not calls
