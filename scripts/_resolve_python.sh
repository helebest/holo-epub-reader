#!/usr/bin/env bash
# Shared Python resolution logic.
# Sourced by doctor.sh, parse.sh, validate.sh.
#
# Resolution chain:
#   1. $EPUB_READER_PYTHON  (explicit override)
#   2. $HOME/.openclaw/.venv/bin/python3  (OpenClaw — preferred, known-good)
#   3. python3 on PATH      (system fallback)
#   4. python on PATH       (Git Bash / Windows fallback)
#
# Sets and exports PYTHON_CMD and EPUB_READER_PYTHON.

# _check_python_version CMD: verify interpreter is Python >= 3.10
_check_python_version() {
    "$1" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null
}

if [ -n "${EPUB_READER_PYTHON:-}" ] && [ -x "$EPUB_READER_PYTHON" ] && _check_python_version "$EPUB_READER_PYTHON"; then
    PYTHON_CMD="$EPUB_READER_PYTHON"
elif [ -x "${HOME:-.}/.openclaw/.venv/bin/python3" ] && _check_python_version "$HOME/.openclaw/.venv/bin/python3"; then
    PYTHON_CMD="$HOME/.openclaw/.venv/bin/python3"
elif command -v python3 >/dev/null 2>&1 && _check_python_version python3; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1 && _check_python_version python; then
    PYTHON_CMD="python"
else
    echo "Error: No suitable Python >= 3.10 found." >&2
    echo "Set EPUB_READER_PYTHON or ensure python3 >= 3.10 is on PATH." >&2
    exit 2
fi

export PYTHON_CMD
export EPUB_READER_PYTHON="$PYTHON_CMD"
