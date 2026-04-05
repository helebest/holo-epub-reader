# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development

Package manager is **uv**. Zero runtime dependencies (stdlib only).

```bash
# Install dependencies (including test tools)
uv sync --extra dev

# Run all tests with coverage (90% minimum enforced)
uv run pytest

# Run a single test file or test
uv run pytest tests/test_reader.py
uv run pytest tests/test_reader.py::test_function_name

# Build package
uv build
```

pytest options (coverage, testpaths, fail-under=90) are pre-configured in `pyproject.toml [tool.pytest.ini_options]`, so bare `uv run pytest` is sufficient.

## Architecture

EPUB parser that converts `.epub` files into LLM-friendly Markdown + images. Data flow:

```
EPUB (ZIP) → reader.parse_epub()
  ├→ epub.read_container()       # META-INF/container.xml → OPF path
  ├→ epub.parse_opf()            # OPF → metadata + manifest + spine order
  ├→ per spine item:
  │   └→ html_extract.extract_blocks()  # HTML → Block objects
  │       └→ _HTMLBlockParser (stdlib html.parser)
  ├→ reader._write_markdown()    # Blocks → content.md (with auto-TOC)
  ├→ image extraction            # → images/ directory
  └→ reader._write_manifest()    # → manifest.json
```

**Key modules:**

- `models.py` — `Block` and `ImageRef` dataclasses. Block types: text, heading, image, list_item, blockquote, code.
- `epub.py` — EPUB standard XML parsing (container.xml, OPF). Pure stdlib `xml.etree`.
- `html_extract.py` — Custom `HTMLParser` subclass. Handles chunking (configurable `max_chunk_chars`), list numbering, and skips nav/header/footer/aside by default.
- `reader.py` — Orchestrator. `parse_epub()` is the main entry point. Also handles TOC generation, heading normalization (filters placeholder titles), and output validation.
- `cli.py` — argparse CLI with subcommands: `doctor`, `parse`, `validate`. Doctor check gates parse/validate.
- `doctor.py` — Validates runtime environment. Resolves Python via `$EPUB_READER_PYTHON` env var, then `$HOME/.openclaw/.venv/bin/python3` (OpenClaw legacy), then `sys.executable` as fallback. Requires Python ≥3.10.

**CLI parse flags:** `--no-images`, `--keep-nav`, `--max-chunk` (default 1200), `--quiet`.

## CI

GitHub Actions matrix: Python 3.10/3.11/3.12. Release workflow triggers on `v*` tags and optionally publishes to PyPI.

## Conventions

- All modules use `from __future__ import annotations`.
- No external dependencies — everything uses Python stdlib (`zipfile`, `xml.etree`, `html.parser`, `json`, `argparse`).
- Tests use `tmp_path` fixtures and build real EPUB zip files in-memory for integration testing.
