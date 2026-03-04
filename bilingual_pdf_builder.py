#!/usr/bin/env python3
"""Build an interleaved bilingual PDF from two input PDFs.

Output format:
L1(S1)
L2(S1)

L1(S2)
L2(S2)
... 
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

LATIN_SENTENCE_RE = re.compile(r"(?<=[.!?…])\s+")
CJK_SENTENCE_RE = re.compile(r"(?<=[。！？])")


@dataclass
class SentencePair:
    left: str
    right: str


def extract_text_from_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    text = normalize_whitespace(text)
    if not text:
        return []

    # Mixed-language splitter: split first on newlines, then by punctuation rules.
    segments: List[str] = []
    for chunk in text.split("\n"):
        chunk = chunk.strip()
        if not chunk:
            continue

        cjk_parts = [part.strip() for part in CJK_SENTENCE_RE.split(chunk) if part.strip()]
        if len(cjk_parts) > 1:
            for part in cjk_parts:
                latin_parts = [s.strip() for s in LATIN_SENTENCE_RE.split(part) if s.strip()]
                segments.extend(latin_parts)
            continue

        latin_parts = [s.strip() for s in LATIN_SENTENCE_RE.split(chunk) if s.strip()]
        segments.extend(latin_parts if latin_parts else [chunk])

    return [s for s in segments if s]


def _join(sentences: Sequence[str], start: int, width: int) -> str:
    return " ".join(sentences[start : start + width]).strip()


def _cost(a: str, b: str) -> float:
    # Length-ratio cost with extra penalty for empty side.
    la = max(1, len(a))
    lb = max(1, len(b))
    ratio = la / lb
    return abs(math.log(ratio))


def align_sentences(left: Sequence[str], right: Sequence[str]) -> List[SentencePair]:
    """Align sentence lists with dynamic programming.

    Allows 1-1, 2-1, and 1-2 alignments to absorb segmentation differences.
    """
    n, m = len(left), len(right)
    inf = float("inf")
    dp = [[inf] * (m + 1) for _ in range(n + 1)]
    back: List[List[Tuple[int, int] | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0

    moves = [(1, 1), (2, 1), (1, 2)]

    for i in range(n + 1):
        for j in range(m + 1):
            if dp[i][j] == inf:
                continue
            for di, dj in moves:
                ni, nj = i + di, j + dj
                if ni <= n and nj <= m:
                    ltxt = _join(left, i, di)
                    rtxt = _join(right, j, dj)
                    c = _cost(ltxt, rtxt)
                    if dp[i][j] + c < dp[ni][nj]:
                        dp[ni][nj] = dp[i][j] + c
                        back[ni][nj] = (i, j)

    if dp[n][m] == inf:
        # Fallback: zip to shortest, pad remainder.
        pairs = [SentencePair(l, r) for l, r in zip(left, right)]
        if n > m:
            pairs.extend(SentencePair(l, "") for l in left[m:])
        else:
            pairs.extend(SentencePair("", r) for r in right[n:])
        return pairs

    pairs_rev: List[SentencePair] = []
    i, j = n, m
    while i > 0 and j > 0:
        prev = back[i][j]
        if prev is None:
            break
        pi, pj = prev
        ltxt = _join(left, pi, i - pi)
        rtxt = _join(right, pj, j - pj)
        pairs_rev.append(SentencePair(ltxt, rtxt))
        i, j = pi, pj

    pairs_rev.reverse()
    return pairs_rev


def wrap_line(text: str, max_chars: int = 95) -> List[str]:
    words = text.split(" ")
    lines: List[str] = []
    current = ""
    for w in words:
        candidate = w if not current else f"{current} {w}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [""]


def _register_font(font_path: Path | None) -> str:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if not font_path:
        return "Helvetica"
    font_name = font_path.stem
    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    return font_name


def write_interleaved_pdf(
    pairs: Iterable[SentencePair],
    output_path: Path,
    left_label: str,
    right_label: str,
    font_name: str = "Helvetica",
) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    top = height - 56
    bottom = 48
    line_h = 14
    y = top

    c.setFont(font_name, 11)

    def newline(lines: int = 1) -> None:
        nonlocal y
        y -= line_h * lines
        if y < bottom:
            c.showPage()
            c.setFont(font_name, 11)
            y = top

    for idx, pair in enumerate(pairs, start=1):
        header = f"[{idx}]"
        c.drawString(44, y, header)
        newline()

        left_lines = wrap_line(f"{left_label}: {pair.left}")
        for ln in left_lines:
            c.drawString(56, y, ln)
            newline()

        right_lines = wrap_line(f"{right_label}: {pair.right}")
        for ln in right_lines:
            c.drawString(56, y, ln)
            newline()

        newline()

    c.save()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create an interleaved bilingual PDF from two PDFs.")
    p.add_argument("--left", required=True, type=Path, help="Path to source PDF in language 1")
    p.add_argument("--right", required=True, type=Path, help="Path to source PDF in language 2")
    p.add_argument("--output", required=True, type=Path, help="Output PDF path")
    p.add_argument("--left-label", default="L1", help="Label for language 1 lines")
    p.add_argument("--right-label", default="L2", help="Label for language 2 lines")
    p.add_argument("--font", type=Path, default=None, help="Optional .ttf font path for non-Latin scripts")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    left_text = extract_text_from_pdf(args.left)
    right_text = extract_text_from_pdf(args.right)

    left_sentences = split_into_sentences(left_text)
    right_sentences = split_into_sentences(right_text)

    pairs = align_sentences(left_sentences, right_sentences)
    font_name = _register_font(args.font)
    write_interleaved_pdf(
        pairs,
        args.output,
        left_label=args.left_label,
        right_label=args.right_label,
        font_name=font_name,
    )

    print(
        f"Wrote {len(pairs)} aligned sentence pairs to {args.output} "
        f"(left={len(left_sentences)}, right={len(right_sentences)})."
    )


if __name__ == "__main__":
    main()
