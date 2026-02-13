# epub-reader

Parse EPUB files into LLM-friendly text and image blocks.

## 开发

```bash
# 安装依赖
uv sync

# 运行测试
uv run pytest
```

## 部署

```bash
# 部署到 OpenClaw skills 目录
./deploy_skill.sh <target-path>
```

部署后的目录结构：

```
skill-name/
├── SKILL.md
└── scripts/
    ├── parse.sh
    ├── validate.sh
    ├── cli.py
    ├── epub.py
    ├── reader.py
    └── ...
```

## 使用

```bash
# 解析 EPUB
bash <skill-path>/scripts/parse.sh <epub文件路径> [输出目录]

# 验证输出
bash <skill-path>/scripts/validate.sh <输出目录>
```

## 输出

默认输出为 Markdown (`content.md`)，包含：
- 文本块
- 标题层级
- 图像（保存到 `images/` 目录）
- 元数据 (`manifest.json`)
