---
name: epub-reader-skill
description: Use when you need to parse EPUB files into LLM-friendly text/image blocks, run the epub-reader CLI with uv isolation, validate outputs, or explain the output schema and verification steps.
---

# Epub Reader Skill

## Overview

Parse EPUB files into LLM-friendly blocks (text, headings, images) and validate the outputs. Default output is Markdown. Prefer running the CLI via `uv run` to keep dependencies isolated.

## Quick Start

1. From the repo root, ensure the uv environment is ready:
   - `uv sync`
2. Parse an EPUB into an output folder:
   - `uv run epub-reader parse /path/to/book.epub --out /path/to/out`
3. Offline or no-install mode (src layout):
   - `PYTHONPATH=./src uv run --no-project --isolated --no-sync python -m epub_reader.cli parse /path/to/book.epub --out /path/to/out`
3. Validate the generated output:
   - `uv run epub-reader validate /path/to/out`

## Workflow

1. Parse the EPUB with `epub-reader parse`.
2. Inspect `content.md`, `manifest.json`, and `images/`.
3. Run `epub-reader validate` to confirm counts and file integrity.

## Progressive Disclosure

Load details only when needed:
- CLI flags, examples, and behavior: `references/cli.md`
- Output schema and field meanings: `references/output-schema.md`
- Validation checks and troubleshooting: `references/validation.md`
