#!/bin/bash
# 输出验证脚本
# 用法: bash validate.sh <输出目录>

# 检查参数
if [ -z "$1" ]; then
    echo "用法: bash validate.sh <输出目录>"
    echo "示例: bash validate.sh /path/to/output"
    exit 1
fi

OUTPUT_DIR="$1"

# 获取绝对路径
OUTPUT_DIR=$(realpath "$OUTPUT_DIR")

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "错误: 目录不存在 $OUTPUT_DIR"
    exit 1
fi

# 获取脚本所在目录，然后切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 使用全局 venv（依赖由 openclaw_deploy_skill.sh 安装）
PYTHON_CMD="$HOME/.openclaw/.venv/bin/python3"

# 运行验证
echo "正在验证: $OUTPUT_DIR"
$PYTHON_CMD scripts/cli.py validate "$OUTPUT_DIR"

if [ $? -eq 0 ]; then
    echo "✅ 验证成功!"
else
    echo "❌ 验证失败"
    exit 1
fi
