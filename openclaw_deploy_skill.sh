#!/usr/bin/env bash
#
# Deploy script for Holo Epub Reader Skill
# Usage: ./openclaw_deploy_skill.sh <target-path>
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GLOBAL_VENV="$HOME/.openclaw/.venv"
GLOBAL_PYTHON="$GLOBAL_VENV/bin/python3"

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <target-path>"
    exit 1
fi

TARGET_PATH="$1"

if [[ "$TARGET_PATH" != /* ]]; then
    echo "Error: Target path must be absolute"
    exit 1
fi

if [ ! -x "$GLOBAL_PYTHON" ]; then
    echo "Error: Required python not found: $GLOBAL_PYTHON"
    echo "Please initialize OpenClaw global venv first."
    exit 1
fi

echo "Deploying Holo Epub Reader to: $TARGET_PATH"

echo "Reading dependencies from pyproject.toml..."
DEPS=$("$GLOBAL_PYTHON" -c "
import ast
import re
from pathlib import Path

text = Path('$SCRIPT_DIR/pyproject.toml').read_text(encoding='utf-8')
data = None

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        tomllib = None

if tomllib is not None:
    data = tomllib.loads(text)

deps = []
if isinstance(data, dict):
    deps = data.get('project', {}).get('dependencies', [])

if not deps:
    match = re.search(r'(?ms)^\\[project\\].*?^dependencies\\s*=\\s*(\\[[^\\]]*\\])', text)
    if match:
        deps = ast.literal_eval(match.group(1))

print(' '.join(deps))
")

if [ -z "$DEPS" ]; then
    echo "No dependencies found, skipping installation"
else
    echo "Dependencies: $DEPS"
    echo "Installing dependencies to global venv..."
    uv pip install --python "$GLOBAL_PYTHON" $DEPS
fi

mkdir -p "$TARGET_PATH"

DEPLOY_ITEMS=(
    "SKILL.md"
    "scripts"
)

for item in "${DEPLOY_ITEMS[@]}"; do
    if [ -e "$SCRIPT_DIR/$item" ]; then
        echo "Copying $item..."
        rm -rf "$TARGET_PATH/$item"
        cp -r "$SCRIPT_DIR/$item" "$TARGET_PATH/"
    else
        echo "Warning: $item not found, skipping"
    fi
done

if command -v find >/dev/null 2>&1; then
    find "$TARGET_PATH" -type d -name __pycache__ -prune -exec rm -rf {} +
fi

echo ""
echo "✅ Deployment complete!"
