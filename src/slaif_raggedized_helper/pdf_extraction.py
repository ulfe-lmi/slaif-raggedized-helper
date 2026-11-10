"""Native PDF candidate: bounded verified input and isolated fixed worker."""
from __future__ import annotations

import hashlib
import json
import math
import os
import selectors
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from .provenance_records import Block, Dependency, Scope, catalog, extraction_id
from .schema import fingerprint
from .source_admission import OriginalStore, Revision


class PdfError(ValueError):
    """Safe, input-free extraction failure."""


class PdfPrerequisiteError(PdfError):
    """The configured sandbox or exact development backend is unavailable."""


@dataclass(frozen=True)
class PdfPolicy:
    max_bytes: int = 2_000_000
    max_pages: int = 32
    max_objects: int = 20000
    max_chars: int = 500000
    max_output: int = 2_000_000
    wall_seconds: float = 2.0

    def __post_init__(self):
        for v, cap in ((self.max_bytes, 2_000_000), (self.max_pages, 32),
                       (self.max_objects, 20000), (self.max_chars, 500000),
                       (self.max_output, 2_000_000)):
            if type(v) is not int or not 1 <= v <= cap:
                raise PdfError('invalid PDF policy')
        if (type(self.wall_seconds) not in (int, float) or not math.isfinite(self.wall_seconds)
                or not 0 < self.wall_seconds <= 2.0):
            raise PdfError('invalid PDF policy')

    @property
    def definition(self):
        return json.dumps({'adapter': 'pdfminer.six-20260107', 'version': 1,
                           **self.__dict__, 'geometry': 'pdf-points-bottom-left',
                           'isolation': 'bwrap-linux-v1'}, sort_keys=True, separators=(',', ':'))


@dataclass(frozen=True)
class PdfRuntime:
    """Trusted operator configuration; never taken from a PDF or JSON input."""
    runtime_dir: Path
    packages_dir: Path


@dataclass(frozen=True)
class PdfResult:
    revision: Revision
    scope: Scope
    dependency: Dependency
    blocks: tuple[Block, ...]
    pages: tuple[tuple[int, str], ...]
    status: str
    uncertainty: str = 'Native layout reading order is heuristic; visual content is not extracted.'


def _argv(runtime: PdfRuntime, input_path: Path, args: list[str]) -> list[str]:
    try:
        root = Path(runtime.runtime_dir).resolve(strict=True)
        packages = Path(runtime.packages_dir).resolve(strict=True)
        worker = Path(__file__).with_name('pdf_worker.py').resolve(strict=True)
    except (OSError, TypeError, ValueError):
        raise PdfPrerequisiteError('pdf isolation or backend unavailable') from None
    if (not (root / 'bin/python3.12').is_file() or not (packages / 'pdfminer/__init__.py').is_file()
            or not Path('/usr/bin/bwrap').is_file() or not Path('/usr/bin/prlimit').is_file()):
        raise PdfPrerequisiteError('pdf isolation or backend unavailable')
    return ['/usr/bin/prlimit', '--as=268435456', '--cpu=1', '--nofile=32', '--fsize=2097152',
            '/usr/bin/bwrap', '--unshare-user', '--unshare-pid', '--unshare-net',
            '--unshare-ipc', '--unshare-uts', '--die-with-parent', '--new-session', '--clearenv',
            '--setenv', 'PYTHONPATH', '/packages', '--setenv', 'PYTHONDONTWRITEBYTECODE', '1',
            '--setenv', 'HOME', '/tmp', '--ro-bind', str(root), '/runtime', '--ro-bind',
            str(packages), '/packages', '--ro-bind', str(input_path), '/input.pdf',
            '--ro-bind', str(worker), '/worker.py', '--ro-bind', '/usr/lib/x86_64-linux-gnu',
            '/usr/lib/x86_64-linux-gnu', '--ro-bind', '/usr/lib64', '/usr/lib64',
            '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
            '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--chdir', '/tmp',
            '/runtime/bin/python3.12', '/worker.py', *args]


def _run(argv: list[str], cap: int, deadline: float) -> bytes:
    try:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, close_fds=True)
    except OSError:
        raise PdfPrerequisiteError('pdf isolation or backend unavailable') from None
    selector = None
    try:
        selector = selectors.DefaultSelector()
        assert child.stdout is not None
        selector.register(child.stdout, selectors.EVENT_READ)
        data = bytearray()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not selector.select(remaining):
                raise PdfError('pdf worker timeout')
            chunk = os.read(child.stdout.fileno(), min(65536, cap + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > cap:
                raise PdfError('pdf worker output limit')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise PdfError('pdf worker timeout')
        try:
            code = child.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            raise PdfError('pdf worker timeout') from None
        if code:
            if data.strip() == b'{"error":"backend_unavailable"}' or not data:
                raise PdfPrerequisiteError('pdf isolation or backend unavailable')
            raise PdfError('pdf worker refused input')
        return bytes(data)
    finally:
        if selector is not None:
            selector.close()
        if child.stdout is not None:
            child.stdout.close()
        if child.poll() is None:
            try:
                child.terminate()
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=0.4)
            except subprocess.TimeoutExpired:
                try:
                    child.kill()
                except ProcessLookupError:
                    pass
                child.wait(timeout=0.5)


def extract(store: OriginalStore, revision_id: str, runtime: PdfRuntime,
            policy: PdfPolicy | None = None) -> PdfResult:
    """Extract native PDF text; runtime must be explicitly trusted by the operator."""
    try:
        if type(store) is not OriginalStore or type(runtime) is not PdfRuntime:
            raise ValueError
        if policy is not None and type(policy) is not PdfPolicy:
            raise ValueError
        policy = PdfPolicy() if policy is None else PdfPolicy(**policy.__dict__)
        deadline = time.monotonic() + policy.wall_seconds
        revision, raw = store.read_verified(revision_id, max_bytes=policy.max_bytes)
        scope = catalog((revision,))[0]
        if revision.source.media_type != 'application/pdf':
            raise ValueError
        definition = policy.definition
        dep = Dependency(schema_version=1, revision_id=revision_id,
                         extraction_id=extraction_id(definition), definition=definition)
        nonce = uuid.uuid4().hex
        with tempfile.TemporaryDirectory(prefix='pdf-worker-') as directory:
            input_path = Path(directory) / 'input.pdf'
            input_path.write_bytes(raw)
            if time.monotonic() >= deadline:
                raise PdfError('pdf worker timeout')
            argv = _argv(runtime, input_path, [revision_id, dep.extraction_id, nonce,
                         str(policy.max_pages), str(policy.max_objects), str(policy.max_chars)])
            output = _run(argv, policy.max_output, deadline)
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError
                result[key] = value
            return result

        obj = json.loads(output.decode('utf-8'), object_pairs_hook=unique,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if (type(obj) is not dict or set(obj) != {'revision', 'policy', 'request', 'pages',
                                                   'blocks', 'objects'}
                or (obj['revision'], obj['policy'], obj['request'])
                != (revision_id, dep.extraction_id, nonce)
                or type(obj['objects']) is not int or not 0 <= obj['objects'] <= policy.max_objects
                or type(obj['pages']) is not list or not 1 <= len(obj['pages']) <= policy.max_pages
                or type(obj['blocks']) is not list or len(obj['blocks']) > 4096):
            raise ValueError
        pages = []
        for i, page in enumerate(obj['pages'], 1):
            if (type(page) is not dict or set(page) != {'page', 'status'}
                    or type(page['page']) is not int or page['page'] != i
                    or page['status'] not in ('native_text', 'visual_needed')):
                raise ValueError
            pages.append((i, page['status']))
        blocks = []
        chars = 0
        last_page = 0
        counts = [0] * len(pages)
        for index, item in enumerate(obj['blocks']):
            if time.monotonic() >= deadline:
                raise PdfError('pdf worker timeout')
            if (type(item) is not dict or set(item) != {'page', 'text', 'bbox'}
                    or type(item['page']) is not int or not last_page <= item['page'] <= len(pages)
                    or item['page'] < 1 or type(item['text']) is not str
                    or not 1 <= len(item['text']) <= 200000 or type(item['bbox']) is not list
                    or len(item['bbox']) != 4):
                raise ValueError
            bbox = item['bbox']
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in bbox):
                raise ValueError
            if bbox[0] > bbox[2] or bbox[1] > bbox[3]:
                raise ValueError
            chars += len(item['text'])
            if chars > policy.max_chars:
                raise ValueError
            last_page = item['page']
            counts[last_page - 1] += 1
            digest = hashlib.sha256(item['text'].encode('utf-8')).hexdigest()
            anchor = f'page:{last_page}'
            ident = fingerprint({'kind': 'pdf-native-block', 'version': 1,
                                 'revision_id': revision_id, 'extraction_id': dep.extraction_id,
                                 'order': index, 'page': last_page, 'text_sha256': digest,
                                 'geometry': bbox})
            blocks.append(Block(schema_version=1, block_id=ident, revision_id=revision_id,
                                extraction_id=dep.extraction_id, order=index, kind='text',
                                anchor=anchor, text=item['text'], text_sha256=digest,
                                origin='native', page_ref=anchor,
                                geometry=tuple(float(v) for v in bbox),
                                uncertainty='PDF native text and order are layout heuristic.'))
        if any((count > 0) != (status == 'native_text')
               for count, (_, status) in zip(counts, pages)):
            raise ValueError
        if time.monotonic() >= deadline:
            raise PdfError('pdf worker timeout')
        return PdfResult(revision, scope, dep, tuple(blocks), tuple(pages),
                         'partial_visual_needed' if any(not n for n in counts) else 'native_text')
    except PdfError:
        raise
    except Exception:
        raise PdfError('pdf extraction refused') from None
