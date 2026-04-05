# holo-epub-reader

[![CI](https://github.com/helebest/holo-epub-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/helebest/holo-epub-reader/actions/workflows/ci.yml)
[![Latest Release](https://img.shields.io/github/v/release/helebest/holo-epub-reader?display_name=tag)](https://github.com/helebest/holo-epub-reader/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

Parse EPUB files into LLM-friendly text and image blocks.

## 安装

### Claude Code（插件方式）

在 Claude Code 中运行：

```
/plugin marketplace add helebest/holo-epub-reader
/plugin install holo-epub-reader@holo-epub-reader
```

升级时 Claude Code 会自动检测新版本并提示。

### Codex CLI

在 Codex 中请求安装：

> Install the holo-epub-reader skill from https://github.com/helebest/holo-epub-reader

### OpenClaw

```bash
./openclaw_deploy_skill.sh <target-path>
```

## 开发

```bash
# 安装依赖（含测试工具）
uv sync --extra dev

# 运行测试（覆盖率门禁 90%+）
uv run pytest --cov=holo_epub_reader --cov-report=term-missing --cov-fail-under=90
```

## CI / CD

- `CI` workflow: 在 `push main` 和 `pull_request -> main` 触发，矩阵测试 Python `3.10 / 3.11 / 3.12`，并执行 90% 覆盖率门禁。
- `Release` workflow: 在推送 `v*` tag 时触发，执行测试、构建 `sdist/wheel`、创建 GitHub Release。
- 可选发布到 PyPI: 配置仓库 secret `PYPI_API_TOKEN` 后，Release workflow 会自动执行 `uv publish`。

## 使用

```bash
# 前置检查（必须先通过）
bash <skill-path>/scripts/doctor.sh

# 解析 EPUB（输出目录必填）
bash <skill-path>/scripts/parse.sh <epub文件路径> <输出目录>

# 验证输出
bash <skill-path>/scripts/validate.sh <输出目录>
```

也可直接使用 Python CLI：

```bash
python3 -m holo_epub_reader.cli doctor
python3 -m holo_epub_reader.cli parse <epub文件路径> --out <输出目录>
python3 -m holo_epub_reader.cli validate <输出目录>
```

### 多平台支持

Shell 脚本自动按以下优先级查找 Python：

1. `$EPUB_READER_PYTHON` 环境变量（显式指定）
2. `$HOME/.openclaw/.venv/bin/python3`（OpenClaw 优先）
3. 系统 `python3`（PATH 中）
4. 系统 `python`（Git Bash / Windows 兼容）

直接使用 Python CLI 时（`python3 -m holo_epub_reader.cli ...`），当前解释器（`sys.executable`）也会作为候选。

```bash
# 指定 Python 解释器
export EPUB_READER_PYTHON=/usr/bin/python3.12
bash scripts/parse.sh book.epub output/
```

## 输出

默认输出为 Markdown (`content.md`)，包含：
- 文本块
- 标题层级
- 图像（保存到 `images/` 目录）
- 元数据 (`manifest.json`)
