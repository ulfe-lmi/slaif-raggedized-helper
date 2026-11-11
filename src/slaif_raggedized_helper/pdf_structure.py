"""Conservative, literal classification of already extracted PDF lines."""

from dataclasses import dataclass
import math
import re
import time

VERSION = "pdf-literal-structure-v1"


class StructureError(ValueError):
    """Invalid input or exhausted cooperative budget (never includes input)."""


@dataclass(frozen=True)
class Line:
    page: int
    text: str
    bbox: tuple[float, float, float, float]


def _columns(text):
    if "|" in text:
        parts = text.split("|")
        if parts[0].strip() == "":
            parts = parts[1:]
        if parts and parts[-1].strip() == "":
            parts = parts[:-1]
        if len(parts) < 2 or any(not p.strip() for p in parts):
            return None
        return ("pipe", len(parts))
    matches = [
        m
        for m in re.finditer(r"\S+", text)
        if m.start() == 0 or (m.start() >= 2 and text[m.start() - 2 : m.start()] == "  ")
    ]
    if len(matches) < 2:
        return None
    return ("space", tuple(m.start() for m in matches))


def _finite(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def classify(lines: tuple[Line, ...]) -> tuple[str, ...]:
    deadline = time.monotonic() + 2.0

    def check():
        if time.monotonic() >= deadline:
            raise StructureError("budget exceeded")

    if type(lines) is not tuple or len(lines) > 4096:
        raise StructureError("invalid input")
    total = 0
    texts = []
    for line in lines:
        check()
        if (
            type(line) is not Line
            or type(line.page) is not int
            or not 1 <= line.page <= 32
            or type(line.text) is not str
            or type(line.bbox) is not tuple
            or len(line.bbox) != 4
        ):
            raise StructureError("invalid input")
        if (
            any(not _finite(x) for x in line.bbox)
            or line.bbox[0] > line.bbox[2]
            or line.bbox[1] > line.bbox[3]
        ):
            raise StructureError("invalid input")
        total += len(line.text)
        if len(line.text) > 200000 or total > 500000:
            raise StructureError("invalid input")
        try:
            line.text.encode("utf-8")
        except UnicodeError:
            raise StructureError("invalid input") from None
        text = (
            line.text.removesuffix("\n").removesuffix("\r")
            if line.text.endswith("\n")
            else line.text
        )
        texts.append(text if "\n" not in text and "\r" not in text else "")
    columns = []
    for text in texts:
        check()
        columns.append(_columns(text))
    result = ["text"] * len(lines)
    for i, text in enumerate(texts):
        check()
        if re.match(r"^\s*(?:[-*•]|\d+[.)]) +\S", text):
            result[i] = "list"
    i = 0
    while i + 3 < len(lines):
        check()
        header = columns[i]
        rule = texts[i + 1].strip()
        if (
            not header
            or not rule
            or not re.fullmatch(r"[-+| ]+", rule)
            or rule.count("-") < 3
            or (
                header[0] == "pipe"
                and (
                    len(rule.strip("|").split("|")) != header[1]
                    or any(not re.fullmatch(r" *-+ *", part) for part in rule.strip("|").split("|"))
                )
            )
            or (
                header[0] == "space"
                and (
                    not re.fullmatch(r"[- ]+", rule)
                    or len(texts[i + 1].rstrip()) < len(texts[i].rstrip())
                )
            )
            or lines[i].page != lines[i + 1].page
        ):
            i += 1
            continue
        j = i + 2
        while j < len(lines) and lines[j].page == lines[i].page and columns[j] == header:
            check()
            if j + 1 < len(lines) and re.fullmatch(r"[-+| ]{3,}", texts[j + 1]):
                break
            j += 1
        if j >= i + 4:
            result[i] = "table_header"
            result[i + 1 : j] = ["table_row"] * (j - i - 1)
            i = j
        else:
            i += 1
    check()
    return tuple(result)
