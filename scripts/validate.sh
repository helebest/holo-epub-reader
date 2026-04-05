#!/usr/bin/env bash
# 输出验证脚本
# 用法: bash validate.sh <输出目录>

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "用法: bash validate.sh <输出目录>"
    echo "示例: bash validate.sh /path/to/output"
    exit 1
fi

OUTPUT_DIR="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR/_resolve_python.sh"

cd "$PROJECT_ROOT"

exec "$PYTHON_CMD" -m holo_epub_reader.cli validate "$OUTPUT_DIR"

