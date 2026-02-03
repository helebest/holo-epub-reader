# Validation

## What validate checks

`epub-reader validate <out>` performs:
- Checks that `content.md` exists.
- Image file existence checks based on `manifest.json` (skipped if `images_extracted` is false).

## Typical errors

- `content.md not found`: Parsing did not run or output folder is wrong.
- `Invalid JSON on line N`: Output file was edited or truncated.
- `Block count mismatch`: Output corrupted or partial.
- `Missing image file`: Image extraction failed or was skipped without updating manifest.
