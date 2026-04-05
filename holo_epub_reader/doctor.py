from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable, Mapping, Sequence

MIN_PYTHON_VERSION = (3, 10)
OPENCLAW_PYTHON_RELATIVE = Path(".openclaw") / ".venv" / "bin" / "python3"


@dataclass(frozen=True)
class DoctorResult:
    ok: bool
    python_path: Path | None
    python_version: str | None
    errors: list[str]


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _default_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), check=True, capture_output=True, text=True)


def _parse_version_payload(raw_stdout: str) -> tuple[int, int, int]:
    payload = json.loads(raw_stdout.strip())
    major = int(payload["major"])
    minor = int(payload["minor"])
    micro = int(payload["micro"])
    return major, minor, micro


def resolve_python(
    env: Mapping[str, str],
    *,
    include_current: bool = False,
) -> list[Path]:
    """Return candidate Python paths in priority order.

    Resolution chain:
    1. ``EPUB_READER_PYTHON`` env var (explicit override)
    2. ``sys.executable`` (current interpreter, when *include_current* is True)
    3. ``$HOME/.openclaw/.venv/bin/python3`` (OpenClaw legacy fallback)
    """
    candidates: list[Path] = []

    explicit = env.get("EPUB_READER_PYTHON")
    if explicit:
        candidates.append(Path(explicit))

    # The current interpreter is the most accurate choice when running the CLI
    # directly — it is the Python actually executing the code.
    if include_current:
        candidates.append(Path(sys.executable))

    home = env.get("HOME")
    if home:
        candidates.append(Path(home) / OPENCLAW_PYTHON_RELATIVE)

    return candidates


def run_doctor(
    *,
    env: Mapping[str, str] | None = None,
    run_command: CommandRunner | None = None,
) -> DoctorResult:
    runtime_env = os.environ if env is None else env
    runner = _default_runner if run_command is None else run_command

    # Include sys.executable when using the real environment (default call).
    candidates = resolve_python(runtime_env, include_current=(env is None))
    if not candidates:
        return DoctorResult(
            ok=False,
            python_path=None,
            python_version=None,
            errors=[
                "No Python interpreter found. "
                "Set EPUB_READER_PYTHON or ensure HOME is set."
            ],
        )

    # Try each candidate in priority order; return on first success.
    last_errors: list[str] = []
    for python_path in candidates:
        if not python_path.exists():
            last_errors.append(
                f"Python interpreter not found: {python_path}"
            )
            continue

        if not os.access(python_path, os.X_OK):
            last_errors.append(
                f"Python interpreter is not executable: {python_path}"
            )
            continue

        command = [
            str(python_path),
            "-c",
            (
                "import json, sys; "
                "print(json.dumps({'major': sys.version_info[0], "
                "'minor': sys.version_info[1], 'micro': sys.version_info[2]}))"
            ),
        ]

        try:
            completed = runner(command)
        except OSError as exc:
            last_errors.append(
                f"Failed to execute Python interpreter {python_path}: {exc}"
            )
            continue
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or "").strip()
            suffix = f": {details}" if details else ""
            last_errors.append(
                f"Python interpreter {python_path} returned non-zero exit code"
                f"{suffix}"
            )
            continue

        try:
            major, minor, micro = _parse_version_payload(completed.stdout)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            last_errors.append(
                f"Unable to parse Python version from {python_path}: {exc}"
            )
            continue

        python_version = f"{major}.{minor}.{micro}"
        if (major, minor) < MIN_PYTHON_VERSION:
            last_errors.append(
                f"Python {python_version} at {python_path} "
                f"is below minimum 3.10."
            )
            continue

        return DoctorResult(
            ok=True,
            python_path=python_path,
            python_version=python_version,
            errors=[],
        )

    # All candidates failed.
    return DoctorResult(
        ok=False,
        python_path=candidates[0],
        python_version=None,
        errors=last_errors,
    )
