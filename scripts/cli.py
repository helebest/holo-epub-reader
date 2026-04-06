from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from doctor import DoctorResult, run_doctor
from exit_codes import EXIT_DOCTOR_ERROR, EXIT_ERROR, EXIT_OK
from reader import parse_epub, validate_output


def _emit_doctor_failure(result: DoctorResult) -> None:
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)


def _run_doctor_check() -> DoctorResult:
    return run_doctor()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="holo-epub-reader",
        description="Parse EPUB files into LLM-friendly text and image blocks.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="Check runtime prerequisites")
    doctor_parser.set_defaults(func=_run_doctor)

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


def _run_doctor(_: argparse.Namespace) -> int:
    result = _run_doctor_check()
    if not result.ok:
        _emit_doctor_failure(result)
        return EXIT_DOCTOR_ERROR

    print(f"Doctor OK: {result.python_path} (Python {result.python_version})")
    return EXIT_OK


def _run_parse(args: argparse.Namespace) -> int:
    doctor = _run_doctor_check()
    if not doctor.ok:
        _emit_doctor_failure(doctor)
        return EXIT_DOCTOR_ERROR

    try:
        manifest = parse_epub(
            Path(args.epub),
            Path(args.out),
            include_images=not args.no_images,
            strip_nav=not args.keep_nav,
            max_chunk_chars=args.max_chunk,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if not args.quiet:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return EXIT_OK


def _run_validate(args: argparse.Namespace) -> int:
    doctor = _run_doctor_check()
    if not doctor.ok:
        _emit_doctor_failure(doctor)
        return EXIT_DOCTOR_ERROR

    ok, errors = validate_output(Path(args.out))
    if ok:
        print("Validation OK")
        return EXIT_OK
    for error in errors:
        print(f"ERROR: {error}")
    return EXIT_ERROR


def run(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def main(argv: list[str] | None = None) -> None:
    sys.exit(run(argv))


if __name__ == "__main__":
    main()
