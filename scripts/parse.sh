#!/usr/bin/env bash
# EPUB 文件解析脚本
# 用法: bash parse.sh <epub文件路径> <输出目录>

set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "用法: bash parse.sh <epub文件路径> <输出目录>"
    echo "示例: bash parse.sh /path/to/book.epub /path/to/output"
    exit 1
fi

EPUB_PATH="$1"
OUTPUT_DIR="$2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

source "$SCRIPT_DIR/_resolve_python.sh"

cd "$PROJECT_ROOT"

exec "$PYTHON_CMD" -m holo_epub_reader.cli parse "$EPUB_PATH" --out "$OUTPUT_DIR"

