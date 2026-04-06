#!/usr/bin/env bash
# EPUB 文件解析脚本
# 用法: bash parse.sh <epub文件路径> <输出目录> [options]

set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "用法: bash parse.sh <epub文件路径> <输出目录> [--no-images] [--keep-nav] [--max-chunk N] [--quiet]"
    echo "示例: bash parse.sh /path/to/book.epub /path/to/output"
    exit 1
fi

EPUB_PATH="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUTPUT_DIR="$(mkdir -p "$2" && cd "$2" && pwd)"
shift 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/_resolve_python.sh"

cd "$SCRIPT_DIR"

exec "$PYTHON_CMD" cli.py parse "$EPUB_PATH" --out "$OUTPUT_DIR" "$@"

