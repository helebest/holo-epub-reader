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

# holo-epub-reader (Claude Code plugin entry)

This is the Claude Code plugin entry point. The runtime files (scripts/ and
holo_epub_reader/) are at the plugin root — two directories above this file.

For full documentation, see the root SKILL.md. Below is the essential usage:

```bash
# Determine the plugin root (parent of skills/)
PLUGIN_ROOT="<two levels up from this SKILL.md>"

# Environment check
bash "$PLUGIN_ROOT/scripts/doctor.sh"

# Parse EPUB
bash "$PLUGIN_ROOT/scripts/parse.sh" /path/to/book.epub /path/to/output

# Validate output
bash "$PLUGIN_ROOT/scripts/validate.sh" /path/to/output
```

CLI flags: `--no-images`, `--keep-nav`, `--max-chunk N`, `--quiet`

Exit codes: 0 (success), 1 (error), 2 (doctor check failed)

Set `EPUB_READER_PYTHON` to override Python interpreter discovery.
