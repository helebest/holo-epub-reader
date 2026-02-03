# epub-reader

Parse EPUB files into LLM-friendly text and image blocks.

Source layout uses `src/epub_reader`.

Run without installing (offline-friendly):
```bash
PYTHONPATH=./src uv run --no-project --isolated --no-sync python -m epub_reader.cli parse /path/to/book.epub --out /path/to/out
```

Run after install:
```bash
uv run epub-reader parse /path/to/book.epub --out /path/to/out
```

Default output is Markdown (`content.md`).
