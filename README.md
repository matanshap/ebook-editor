# ebook-editor (bilingual PDF builder)

This repository includes:

- a **CLI** to build an interleaved bilingual PDF from two PDFs.
- a **desktop GUI** (Tkinter) for Windows/macOS/Linux local usage.
- a modular **core processing layer** so future features (new aligners, previews,
  export formats, batch jobs, plugins) can be added without rewriting interfaces.

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

## CLI usage

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

## GUI usage (recommended for Windows)

Run:

```bash
python gui_app.py
```

Then in the window:

1. Select left/right PDFs.
2. Pick output file path.
3. Optionally choose a `.ttf` font.
4. Click **Build PDF** and monitor progress logs.

## Extensibility notes

The new `ebook_editor_core.py` module contains all processing logic behind
`BuildRequest -> BuildResult`, which is consumed by both CLI and GUI.
This makes it straightforward to add:

- richer alignment strategies,
- paragraph/chapter-aware modes,
- batch processing,
- REST/local web front-ends,
- and advanced editor workflows.

## Notes on alignment quality

- PDF extraction quality strongly affects sentence alignment.
- This is a length-based aligner; for best results, use clean text-based PDFs.
- OCR-heavy scans may need preprocessing (OCR + cleanup) before alignment.
