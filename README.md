# ebook-editor (bilingual PDF builder)

This repository now includes a starter CLI to build a **bilingual, interleaved PDF** from two PDFs (original + translation).

## What it does

Given two PDFs of the same book in different languages, it:

1. Extracts text from each PDF.
2. Splits text into sentences (supports Latin and basic CJK punctuation).
3. Aligns sentences using dynamic programming (allows 1-1, 1-2, 2-1 matches).
4. Writes a new PDF where sentence pairs are interleaved:

- `L1(S1)`
- `L2(S1)`
- `L1(S2)`
- `L2(S2)`

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python bilingual_pdf_builder.py \
  --left /path/to/original.pdf \
  --right /path/to/translation.pdf \
  --output /path/to/aligned-output.pdf \
  --left-label "Original" \
  --right-label "Translation"
```

### Non-Latin fonts

If your languages require Unicode glyphs not covered by Helvetica, provide a TTF:

```bash
python bilingual_pdf_builder.py ... --font /path/to/NotoSans-Regular.ttf
```

## Notes on alignment quality

- PDF extraction quality strongly affects sentence alignment.
- This is a length-based aligner; for best results, use clean text-based PDFs.
- OCR-heavy scans may need preprocessing (OCR + cleanup) before alignment.
- The extractor runs in best-effort mode for malformed PDFs: unreadable pages are skipped with warnings instead of crashing the whole job.
