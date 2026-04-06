#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="holo-epub-reader"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# If running from inside the repo (SKILL.md exists alongside this script),
# use the current checkout instead of cloning a new one.
if [ -f "$SCRIPT_DIR/SKILL.md" ]; then
  INSTALL_DIR="$SCRIPT_DIR"
  echo "使用当前目录: $INSTALL_DIR"
  if [ -d "$INSTALL_DIR/.git" ]; then
    cd "$INSTALL_DIR" && git pull --ff-only || true
  fi
else
  INSTALL_DIR="${SKILL_INSTALL_DIR:-$(pwd)/$SKILL_NAME}"
  if [ -d "$INSTALL_DIR/.git" ]; then
    echo "已存在，执行更新..."
    cd "$INSTALL_DIR" && git pull --ff-only
  else
    git clone https://github.com/helebest/$SKILL_NAME.git "$INSTALL_DIR"
  fi
fi

bash "$INSTALL_DIR/scripts/doctor.sh"
echo "=== $SKILL_NAME 就绪 ==="
