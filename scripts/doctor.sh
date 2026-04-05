#!/usr/bin/env bash
# 环境诊断脚本
# 用法: bash doctor.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR/_resolve_python.sh"

cd "$PROJECT_ROOT"

exec "$PYTHON_CMD" -m holo_epub_reader.cli doctor
