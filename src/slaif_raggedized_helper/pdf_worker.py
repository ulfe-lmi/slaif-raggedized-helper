"""Fixed isolated pdfminer worker. Not a public unsandboxed entrypoint."""

from __future__ import annotations

import json
import os
import sys
from importlib.metadata import PackageNotFoundError, version


def main() -> int:
    try:
        try:
            installed = version("pdfminer.six")
        except PackageNotFoundError:
            installed = None
        if installed != "20260107":
            print('{"error":"backend_unavailable"}')
            return 2
        try:
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LTChar, LTContainer, LTText, LTTextContainer
            from pdfminer.pdfdocument import PDFDocument
            from pdfminer.pdfparser import PDFParser
        except ImportError:
            print('{"error":"backend_unavailable"}')
            return 2

        with open('/input.pdf', 'rb') as source:
            document = PDFDocument(PDFParser(source))
            if document.encryption is not None:
                raise ValueError

        pages_limit, objects_limit, chars_limit = map(int, sys.argv[4:7])
        pages = []
        blocks = []
        objects = chars = 0
        for number, page in enumerate(extract_pages('/input.pdf', maxpages=pages_limit + 1), 1):
            if number > pages_limit:
                raise ValueError
            # Preorder retains pdfminer's layout order. Text containers already
            # aggregate descendants; count those descendants but never emit twice.
            stack = [(obj, False) for obj in reversed(list(page))]
            count = 0
            incomplete = False
            while stack:
                obj, covered = stack.pop()
                objects += 1
                if objects > objects_limit:
                    raise ValueError
                emit = not covered and isinstance(obj, (LTTextContainer, LTChar))
                if emit:
                    text = obj.get_text()
                    chars += len(text)
                    if not text or chars > chars_limit or len(text) > 200000:
                        raise ValueError
                    blocks.append({'page': number, 'text': text, 'bbox': list(obj.bbox)})
                    count += 1
                elif not covered and isinstance(obj, LTText) and not isinstance(obj, LTContainer):
                    # Unsupported text leaf: no fabricated geometry or silent omission.
                    incomplete = True
                if isinstance(obj, LTContainer):
                    stack.extend((child, covered or emit) for child in reversed(list(obj)))
            pages.append({'page': number, 'status':
                          'visual_needed' if incomplete or not count else 'native_text'})
        if not pages:
            raise ValueError
        result = {'revision': sys.argv[1], 'policy': sys.argv[2], 'request': sys.argv[3],
                  'pages': pages, 'blocks': blocks, 'objects': objects}
        sys.stdout.write(json.dumps(result, ensure_ascii=True, allow_nan=False,
                                    separators=(',', ':')))
        return 0
    except BaseException:
        # Never emit parser exceptions, input bytes, or file paths.
        try:
            os.write(1, b'{"error":"parse_refused"}')
        except OSError:
            pass
        return 1


if __name__ == '__main__':
    sys.exit(main())
