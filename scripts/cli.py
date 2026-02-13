from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .reader import parse_epub, validate_output


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="epub-reader",
        description="Parse EPUB files into LLM-friendly text and image blocks.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_parser = subparsers.add_parser("parse", help="Parse an EPUB into blocks")
    parse_parser.add_argument("epub", help="Path to .epub file")
    parse_parser.add_argument("--out", required=True, help="Output directory")
    parse_parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip extracting images (still emits image blocks)",
    )
    parse_parser.add_argument(
        "--keep-nav",
        action="store_true",
        help="Keep navigation/header/footer content",
    )
    parse_parser.add_argument(
        "--max-chunk",
        type=int,
        default=1200,
        help="Maximum characters per text block",
    )
    parse_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress summary output",
    )
    parse_parser.set_defaults(func=_run_parse)

    validate_parser = subparsers.add_parser(
        "validate", help="Validate a parsed output directory"
    )
    validate_parser.add_argument("out", help="Output directory to validate")
    validate_parser.set_defaults(func=_run_validate)

    return parser


def _run_parse(args: argparse.Namespace) -> int:
    manifest = parse_epub(
        Path(args.epub),
        Path(args.out),
        include_images=not args.no_images,
        strip_nav=not args.keep_nav,
        max_chunk_chars=args.max_chunk,
    )
    if not args.quiet:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    ok, errors = validate_output(Path(args.out))
    if ok:
        print("Validation OK")
        return 0
    for error in errors:
        print(f"ERROR: {error}")
    return 1


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
