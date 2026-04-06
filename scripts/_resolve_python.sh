#!/usr/bin/env bash
# Shared Python resolution logic.
# Sourced by doctor.sh, parse.sh, validate.sh.
#
# Resolution chain:
#   1. $EPUB_READER_PYTHON  (explicit override)
#   2. Project .venv in CWD (auto-detect .venv/Scripts/python.exe or .venv/bin/python3)
#   3. $HOME/.openclaw/.venv/bin/python3  (OpenClaw — preferred, known-good)
#   4. python3 on PATH      (system fallback)
#   5. python on PATH       (Git Bash / Windows fallback)
#
# Sets and exports PYTHON_CMD and EPUB_READER_PYTHON.

# Windows UTF-8 fix (GBK cannot encode some characters)
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"

# _check_python_version CMD: verify interpreter is Python >= 3.10
_check_python_version() {
    "$1" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null
}

# _find_project_venv: detect .venv in caller's working directory (cross-platform)
# Returns absolute path so it survives later cd.
_find_project_venv() {
    local _cwd
    _cwd="$(pwd)"
    if [ -x "$_cwd/.venv/Scripts/python.exe" ]; then
        echo "$_cwd/.venv/Scripts/python.exe"
    elif [ -x "$_cwd/.venv/bin/python3" ]; then
        echo "$_cwd/.venv/bin/python3"
    elif [ -x "$_cwd/.venv/bin/python" ]; then
        echo "$_cwd/.venv/bin/python"
    fi
}

if [ -n "${EPUB_READER_PYTHON:-}" ] && [ -x "$EPUB_READER_PYTHON" ] && _check_python_version "$EPUB_READER_PYTHON"; then
    PYTHON_CMD="$EPUB_READER_PYTHON"
elif _VENV_PY="$(_find_project_venv)" && [ -n "$_VENV_PY" ] && _check_python_version "$_VENV_PY"; then
    PYTHON_CMD="$_VENV_PY"
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
