#!/usr/bin/env bash
#
# Install / update holo-epub-reader skill
# Usage: ./install.sh [--target <path>]
#
# Default: ~/.agents/skills/holo-epub-reader
# Override: ./install.sh --target /path/to/skills/holo-epub-reader
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

# ---- Install or update ----
if [ "$SCRIPT_DIR" = "$INSTALL_DIR" ]; then
  # Running from inside the install directory — just update
  echo "使用当前目录: $INSTALL_DIR"
  if [ -d "$INSTALL_DIR/.git" ]; then
    cd "$INSTALL_DIR" && git pull --ff-only || true
  fi
elif [ -d "$INSTALL_DIR/.git" ]; then
  echo "已存在，执行更新..."
  cd "$INSTALL_DIR" && git pull --ff-only
else
  echo "安装 $SKILL_NAME 到: $INSTALL_DIR"
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone https://github.com/helebest/$SKILL_NAME.git "$INSTALL_DIR"
fi

# ---- Verify environment ----
bash "$INSTALL_DIR/scripts/doctor.sh"

echo ""
echo "=== $SKILL_NAME 就绪 ==="
echo "安装位置: $INSTALL_DIR"
echo "升级: cd $INSTALL_DIR && bash install.sh"
echo "卸载: rm -rf $INSTALL_DIR"
