# holo-epub-reader

[![CI](https://github.com/helebest/holo-epub-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/helebest/holo-epub-reader/actions/workflows/ci.yml)
[![Latest Release](https://img.shields.io/github/v/release/helebest/holo-epub-reader?display_name=tag)](https://github.com/helebest/holo-epub-reader/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

Parse EPUB files into LLM-friendly text and image blocks.

## 安装

### Claude Code

```bash
bash deploy_skill.sh --target ~/.claude/skills/holo-epub-reader
```

### Codex CLI

```bash
bash deploy_skill.sh --target ~/.codex/skills/holo-epub-reader
```

### OpenClaw

```bash
bash deploy_skill.sh --target <target-path>
```

### 通用

```bash
# 默认安装到 ~/.agents/skills/holo-epub-reader
bash deploy_skill.sh

# 指定任意目录
bash deploy_skill.sh --target /path/to/skills/holo-epub-reader
```

升级？再跑一次 `bash deploy_skill.sh`。卸载？`rm -rf` 安装目录。

## 使用

```bash
# 前置检查
bash scripts/doctor.sh

# 解析 EPUB
bash scripts/parse.sh <epub文件路径> <输出目录> [--no-images] [--keep-nav] [--max-chunk N] [--quiet]

# 验证输出
bash scripts/validate.sh <输出目录>
```

### 多平台 Python 解析

Shell 脚本自动按以下优先级查找 Python >= 3.10：

1. `$EPUB_READER_PYTHON` 环境变量（显式指定）
2. `$HOME/.openclaw/.venv/bin/python3`（OpenClaw 优先）
3. 系统 `python3`（PATH 中）
4. 系统 `python`（Git Bash / Windows 兼容）

## 开发

```bash
uv sync --extra dev
uv run pytest
```

## 输出

默认输出为 Markdown (`content.md`)，包含：
- 文本块
- 标题层级
- 图像（保存到 `images/` 目录）
- 元数据 (`manifest.json`)
