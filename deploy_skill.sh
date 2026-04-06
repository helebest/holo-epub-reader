#!/usr/bin/env bash
#
# Install / update holo-epub-reader skill
# Usage: ./deploy_skill.sh [--target <path>]
#
# Default: ~/.agents/skills/holo-epub-reader
# Override: ./deploy_skill.sh --target /path/to/skills/holo-epub-reader
#
# Only copies runtime files: SKILL.md + scripts/
#

set -euo pipefail

SKILL_NAME="holo-epub-reader"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_DIR="$HOME/.agents/skills/$SKILL_NAME"

# ---- Parse arguments ----
INSTALL_DIR="$DEFAULT_DIR"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      if [ "$#" -lt 2 ]; then
        echo "错误: --target 需要一个路径参数"
        exit 1
      fi
      INSTALL_DIR="$2"
      shift 2
      ;;
    *)
      echo "用法: $0 [--target <安装路径>]"
      echo "默认安装到: $DEFAULT_DIR"
      exit 1
      ;;
  esac
done

# ---- Source: use repo checkout or clone to temp ----
if [ -f "$SCRIPT_DIR/SKILL.md" ]; then
  # Running from inside the repo
  SRC_DIR="$SCRIPT_DIR"
else
  # Clone to temp for copying
  SRC_DIR="$(mktemp -d)"
  trap 'rm -rf "$SRC_DIR"' EXIT
  git clone --depth 1 https://github.com/helebest/$SKILL_NAME.git "$SRC_DIR"
fi

# ---- Deploy runtime files only ----
echo "安装 $SKILL_NAME 到: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

for item in SKILL.md scripts; do
  if [ -e "$SRC_DIR/$item" ]; then
    rm -rf "$INSTALL_DIR/$item"
    cp -r "$SRC_DIR/$item" "$INSTALL_DIR/"
  fi
done

# Clean __pycache__
find "$INSTALL_DIR" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

# ---- Verify environment ----
bash "$INSTALL_DIR/scripts/doctor.sh"

echo ""
echo "=== $SKILL_NAME 就绪 ==="
echo "安装位置: $INSTALL_DIR"
echo "升级: 在源仓库 git pull 后重新运行 bash deploy_skill.sh --target $INSTALL_DIR"
echo "卸载: rm -rf $INSTALL_DIR"
