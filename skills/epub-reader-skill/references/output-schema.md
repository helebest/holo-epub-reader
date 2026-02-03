# Output Schema

## content.md

Output format. Structure:
- Optional book header: `# {title}` and `_作者: {creator}_`.
- TOC section uses `## 目录`, generated from the Markdown body and limited to the first two heading levels it finds (nested list). Placeholder headings like `chapter-001`, `Contents`, or `目录` are omitted.
- Chapters use `## {chapter}` with `---` separators between chapters.
- Headings use `###` through `######` (based on original heading level).
- Text blocks are paragraphs.
- List items render as `- item`.
- Ordered list items render as `1. item`.
- Blockquotes render as `> quote`.
- Code blocks render as fenced Markdown.
- Images use `![alt](path)` with relative image paths.

## manifest.json

Summary metadata and counts:
- `source_epub`: Source EPUB path.
- `title`: Book title (if found).
- `creator`: Author/creator (if found).
- `chapters`: Spine item count.
- `blocks`: Total block count.
- `images`: Extracted image paths.
- `images_extracted`: Whether images were extracted.
- `missing_images`: Image hrefs referenced but not found in the EPUB.
- `generated_at`: UTC timestamp.
