from pathlib import Path

from pypdf import PdfReader


def extract_pages(path: Path) -> list[tuple[int | None, str]]:
    if path.suffix == ".md":
        return [(None, path.read_text(encoding="utf-8"))]

    reader = PdfReader(path)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text.strip():
            pages.append((number, text))

    if not pages:
        raise ValueError("PDF has no extractable text")
    return pages