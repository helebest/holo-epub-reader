# CLI Reference

## Commands

- `epub-reader parse <epub> --out <dir>`
- `epub-reader validate <dir>`

## Parse Options

- `--out <dir>`: Required output directory.
- `--no-images`: Skip extracting images (image blocks still emitted).
- `--keep-nav`: Keep nav/header/footer content (default strips them).
- `--max-chunk <n>`: Max characters per text block (default 1200).
- `--quiet`: Suppress manifest summary output.

## Examples

```
uv run epub-reader parse ./books/sample.epub --out ./out
uv run epub-reader parse ./books/sample.epub --out ./out --max-chunk 800
uv run epub-reader validate ./out
```

Offline / no-install:
```
PYTHONPATH=./src uv run --no-project --isolated --no-sync python -m epub_reader.cli parse ./books/sample.epub --out ./out
PYTHONPATH=./src uv run --no-project --isolated --no-sync python -m epub_reader.cli validate ./out
```
