"""PDF text extraction with multi-column layout awareness using PyMuPDF."""

import re
import fitz  # PyMuPDF


def _cluster_columns(spans: list[dict], gap_threshold: float = 40.0) -> list[list[dict]]:
    """Group text spans into columns by clustering on x0 position."""
    if not spans:
        return []

    sorted_x = sorted(set(round(s["x0"] / gap_threshold) for s in spans))
    col_boundaries: list[float] = []
    prev = sorted_x[0]
    start = prev
    for x in sorted_x[1:]:
        if x - prev > 1:
            col_boundaries.append(start * gap_threshold)
            start = x
        prev = x
    col_boundaries.append(start * gap_threshold)

    if len(col_boundaries) <= 1:
        return [spans]

    columns: dict[int, list[dict]] = {i: [] for i in range(len(col_boundaries))}
    for s in spans:
        col_idx = 0
        for i, boundary in enumerate(col_boundaries):
            if s["x0"] >= boundary - gap_threshold / 2:
                col_idx = i
        columns[col_idx].append(s)

    return [columns[i] for i in sorted(columns) if columns[i]]


def _spans_to_text(spans: list[dict]) -> str:
    """Reconstruct readable text from span dicts, preserving line breaks."""
    if not spans:
        return ""

    lines: dict[int, list[dict]] = {}
    for s in spans:
        line_key = round(s["top"] / 4)
        lines.setdefault(line_key, []).append(s)

    result = []
    for key in sorted(lines):
        line_spans = sorted(lines[key], key=lambda s: s["x0"])
        result.append(" ".join(s["text"] for s in line_spans if s["text"].strip()))

    return "\n".join(line for line in result if line.strip())


def extract_text(pdf_path: str) -> str:
    """
    Extract text from a PDF preserving multi-column reading order.

    Returns a single string with columns read left-to-right and
    pages separated by ===PAGE BREAK===.
    """
    pages_text: list[str] = []

    doc = fitz.open(pdf_path)
    for page in doc:
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        spans: list[dict] = []
        for block in blocks:
            if block.get("type") != 0:  # type 0 = text
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    bbox = span["bbox"]  # (x0, y0, x1, y1)
                    spans.append({
                        "text": text,
                        "x0": bbox[0],
                        "top": bbox[1],
                    })

        if not spans:
            continue

        columns = _cluster_columns(spans)
        col_texts = [_spans_to_text(col) for col in columns]
        pages_text.append("\n\n---COLUMN BREAK---\n\n".join(col_texts))

    doc.close()
    return "\n\n===PAGE BREAK===\n\n".join(pages_text)
