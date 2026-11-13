"""Bounded, source-traceable lexical terms; no source access or authorization."""
from dataclasses import asdict, dataclass
import re
import time
import unicodedata

from .schema import fingerprint


class AnalyzerError(ValueError):
    """Input or resource policy refused without disclosing input."""


@dataclass(frozen=True)
class Policy:
    max_bytes: int = 1_000_000
    max_chars: int = 250_000
    max_token_chars: int = 4096
    max_terms: int = 100_000
    max_components: int = 128
    max_work: int = 2_000_000
    deadline_ms: int = 5000


@dataclass(frozen=True)
class Term:
    text: str
    start: int
    end: int
    derivation: str


@dataclass(frozen=True)
class Analysis:
    analyzer_id: str
    terms: tuple[Term, ...]


# Runs include Unicode marks, technical connectors and ASCII alphanumeric/Unicode words.
# Separators not in this alphabet are preserved as individual unknown literals.
_RUN = re.compile(r"[\w\u0300-\u036f./\\:+%=-]+|[^\s]", re.UNICODE)
_COMPONENT = re.compile(r"[^\W_]+(?:[\u0300-\u036f]+[^\W_]*)*", re.UNICODE)
_LIMITS = {'max_bytes': 4_000_000, 'max_chars': 1_000_000,
           'max_token_chars': 16384, 'max_terms': 500_000, 'max_components': 1024,
           'max_work': 10_000_000, 'deadline_ms': 60_000}


def _validate(policy: Policy) -> None:
    if type(policy) is not Policy:
        raise AnalyzerError('analysis refused')
    for key, value in asdict(policy).items():
        if type(value) is not int or not 1 <= value <= _LIMITS[key]:
            raise AnalyzerError('analysis refused')


def analyzer_id(policy: Policy = Policy()) -> str:
    _validate(policy)
    return fingerprint({'kind': 'technical-analyzer', 'version': 1,
                        'normalization': 'NFKC-casefold-alias',
                        'unicode_version': unicodedata.unidata_version,
                        'policy': asdict(policy)})


def analyze(text: str, policy: Policy = Policy()) -> Analysis:
    """Return ordered terms and half-open codepoint spans into the exact input."""
    _validate(policy)
    if type(text) is not str or len(text) > policy.max_chars:
        raise AnalyzerError('analysis refused')
    try:
        encoded = text.encode('utf-8', 'strict')
    except UnicodeError:
        raise AnalyzerError('analysis refused') from None
    if len(encoded) > policy.max_bytes:
        raise AnalyzerError('analysis refused')
    start_time = time.monotonic()
    terms: list[Term] = []
    work = 0

    def check(amount: int = 0) -> None:
        nonlocal work
        work += amount
        if work > policy.max_work or (time.monotonic() - start_time) * 1000 > policy.deadline_ms:
            raise AnalyzerError('analysis refused')

    def add(value: str, start: int, end: int, derivation: str) -> None:
        check(len(value) + 1)
        if len(value) > policy.max_token_chars or len(terms) >= policy.max_terms:
            raise AnalyzerError('analysis refused')
        terms.append(Term(value, start, end, derivation))

    for match in _RUN.finditer(text):
        raw = match.group()
        check(len(raw) + 1)
        if len(raw) > policy.max_token_chars:
            raise AnalyzerError('analysis refused')
        a, b = match.span()
        # Sentence-final punctuation is split without dropping any literal character.
        while len(raw) > 1 and raw[-1] in '.:':
            b -= 1
            raw = raw[:-1]
        add(raw, a, b, 'literal')
        alias = unicodedata.normalize('NFKC', raw).casefold()
        if alias != raw:
            add(alias, a, b, 'nfkc-casefold')
        count = 0
        for component in _COMPONENT.finditer(raw):
            ca, cb = component.span()
            if ca == 0 and cb == len(raw):
                continue
            count += 1
            if count > policy.max_components:
                raise AnalyzerError('analysis refused')
            value = component.group()
            add(value, a + ca, a + cb, 'component')
            normalized = unicodedata.normalize('NFKC', value).casefold()
            if normalized != value:
                add(normalized, a + ca, a + cb, 'component-nfkc-casefold')
        for pos in range(b, match.end()):
            add(text[pos], pos, pos + 1, 'literal')
    check()
    return Analysis(analyzer_id(policy), tuple(terms))
