#!/usr/bin/env python3
"""CLI for building an interleaved bilingual PDF from two input PDFs."""

from __future__ import annotations

import argparse
from pathlib import Path

from ebook_editor_core import BuildRequest, build_bilingual_pdf


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
    request = BuildRequest(
        left_pdf=args.left,
        right_pdf=args.right,
        output_pdf=args.output,
        left_label=args.left_label,
        right_label=args.right_label,
        font_path=args.font,
    )
    result = build_bilingual_pdf(request)
    print(
        f"Wrote {result.pair_count} aligned sentence pairs to {result.output_pdf} "
        f"(left={result.left_sentence_count}, right={result.right_sentence_count})."
    )


if __name__ == "__main__":
    main()
