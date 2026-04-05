---
name: holo-epub-reader
description: >-
  Use when you need to extract text, images, or chapter structure from EPUB
  files into LLM-friendly Markdown. Trigger on any mention of EPUB parsing,
  ebook text extraction, epub-to-markdown conversion, or extracting
  chapters/images/TOC from .epub files — even if the user just says "read
  this epub" or "get text from this ebook".
  解析 EPUB 为 LLM 友好的 Markdown 文本/图像块。
homepage: https://github.com/helebest/holo-epub-reader
---

# holo-epub-reader

Parse EPUB files into LLM-friendly Markdown + images with output validation. Zero external dependencies (Python stdlib only).

## Paths

Replace `<skill-dir>` below with the actual installed skill directory:
- **Claude Code plugin**: `~/.claude/plugins/cache/.../holo-epub-reader/<version>`
- **Codex CLI**: `~/.codex/skills/holo-epub-reader`
- **OpenClaw**: the deployed skill path

## When to Use

- Extract chapter text from EPUB into clean Markdown
- Get table of contents and heading structure from EPUB metadata
- Extract images alongside text content
- Validate that EPUB output is complete (all referenced images exist)

## When NOT to Use

- PDF files — this only handles EPUB (.epub)
- DRM-protected EPUB files — ZIP extraction will fail
- Already-extracted text or Markdown files

## Prerequisites

- Python >= 3.10
- EPUB file must be readable
- Output directory must be writable

## Quick Start

### 1) Environment check

```bash
bash <skill-dir>/scripts/doctor.sh
```

### 2) Parse EPUB

```bash
bash <skill-dir>/scripts/parse.sh /path/to/book.epub /path/to/output
```

### 3) Validate output

```bash
bash <skill-dir>/scripts/validate.sh /path/to/output
```

## CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--no-images` | off | Skip extracting image files (still emits image blocks in Markdown) |
| `--keep-nav` | off | Keep navigation/header/footer content instead of stripping |
| `--max-chunk` | 1200 | Maximum characters per text block |
| `--quiet` | off | Suppress manifest JSON summary output |

## Output Structure

```
output-dir/
├── content.md       # Markdown with auto-generated TOC, chapters, headings, images
├── manifest.json    # Metadata: title, creator, block count, image list, timestamps
└── images/          # Extracted images preserving EPUB paths (unless --no-images)
    └── OEBPS/images/
        └── cover.jpg
```

**content.md example:**

```markdown
# Book Title

_Author Name_

---

## Table of Contents
- [Chapter One](#chapter-one)
- [Chapter Two](#chapter-two)

---

## Chapter One

Paragraph text here...

![Alt text](images/OEBPS/images/fig1.jpg)

## Chapter Two

More text...
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Parse or validation error |
| 2 | Doctor check failed (Python not found or version too low) |

## Environment Configuration

Set `EPUB_READER_PYTHON` to override Python interpreter discovery:

```bash
export EPUB_READER_PYTHON=/usr/bin/python3.12
bash <skill-dir>/scripts/parse.sh book.epub output/
```

Resolution order: `$EPUB_READER_PYTHON` > `$HOME/.openclaw/.venv/bin/python3` > system `python3`
