#!/bin/bash
# EPUB 文件解析脚本
# 用法: bash parse.sh <epub文件路径> [输出目录]

# 检查参数
if [ -z "$1" ]; then
    echo "用法: bash parse.sh <epub文件路径> [输出目录]"
    echo "示例: bash parse.sh /path/to/book.epub /path/to/output"
    exit 1
fi

EPUB_PATH="$1"
OUTPUT_DIR="${2:-./output}"

# 检查文件是否存在
if [ ! -f "$EPUB_PATH" ]; then
    echo "错误: 文件不存在 $EPUB_PATH"
    exit 1
fi

# 获取脚本所在目录，然后切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 获取绝对路径
EPUB_PATH=$(realpath "$EPUB_PATH")

# 运行解析
echo "正在解析: $EPUB_PATH"
echo "输出目录: $OUTPUT_DIR"

uv run epub-reader parse "$EPUB_PATH" --out "$OUTPUT_DIR"

if [ $? -eq 0 ]; then
    echo "✅ 解析成功!"
    echo "输出文件:"
    ls -la "$OUTPUT_DIR"
else
    echo "❌ 解析失败"
    exit 1
fi
