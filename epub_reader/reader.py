from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import zipfile
from typing import Dict, Iterable, List, Tuple

from .epub import OpfPackage, parse_opf, read_container, resolve_href
from .html_extract import extract_blocks
from .models import Block, ImageRef


class EpubParseError(RuntimeError):
    pass


def _image_output_relpath(image_href: str) -> str:
    return str(Path("images") / image_href)


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    cleaned: List[str] = []
    for ch in text.strip().lower():
        if ch.isalnum():
            cleaned.append(ch)
        elif ch.isspace() or ch in {"-", "_"}:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "section"


def _write_markdown(
    path: Path,
    blocks: List[Block],
    *,
    title: str | None = None,
    creator: str | None = None,
) -> None:
    _ensure_parent(path)
    header_lines: List[str] = []
    body_lines: List[str] = []
    in_list = False

    if title:
        header_lines.append(f"# {title}")
        header_lines.append("")
    if creator:
        header_lines.append(f"_作者: {creator}_")
        header_lines.append("")
    if title or creator:
        header_lines.append("---")
        header_lines.append("")

    current_chapter: str | None = None
    for block in blocks:
        if block.chapter != current_chapter:
            if current_chapter is not None:
                body_lines.append("---")
                body_lines.append("")
            in_list = False
            current_chapter = block.chapter
            if current_chapter:
                body_lines.append(f"## {current_chapter}")
                body_lines.append("")

        if block.type == "heading" and block.text:
            if in_list:
                body_lines.append("")
                in_list = False
            if current_chapter and block.text.strip() == current_chapter.strip():
                continue
            level = (block.level or 1) + 2
            level = min(max(level, 1), 6)
            body_lines.append(f"{'#' * level} {block.text}")
            body_lines.append("")
        elif block.type == "text" and block.text:
            if block.tag == "li":
                if block.list_type == "ol" and block.list_index is not None:
                    body_lines.append(f"{block.list_index}. {block.text}")
                else:
                    body_lines.append(f"- {block.text}")
                in_list = True
                continue
            if in_list:
                body_lines.append("")
                in_list = False
            if block.tag == "blockquote":
                for line in (block.text.splitlines() or [""]):
                    body_lines.append(f"> {line}".rstrip())
                body_lines.append("")
                continue
            if block.tag == "pre":
                body_lines.append("```")
                body_lines.extend(block.text.splitlines())
                body_lines.append("```")
                body_lines.append("")
                continue
            body_lines.append(block.text)
            body_lines.append("")
        elif block.type == "image" and block.image:
            if in_list:
                body_lines.append("")
                in_list = False
            alt = block.alt or ""
            body_lines.append(f"![{alt}]({block.image})")
            body_lines.append("")

    toc_lines: List[str] = []

    headings: List[tuple[int, str]] = []
    in_code_block = False
    for line in body_lines:
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if not line.startswith("#"):
            continue
        stripped = line.lstrip("#")
        level = len(line) - len(stripped)
        text = stripped.strip()
        if text:
            headings.append((level, text))

    if headings:
        unique_levels = sorted({level for level, _ in headings})
        level_one = unique_levels[0]
        level_two = unique_levels[1] if len(unique_levels) > 1 else None
        slug_counts: dict[str, int] = {}
        placeholder_titles = {
            "contents",
            "table of contents",
            "toc",
            "目录",
            "封面",
            "cover",
            "titlepage",
            "title page",
            "版权页",
            "copyright",
            "index",
            "索引",
        }

        def _is_placeholder_heading(text: str) -> bool:
            normalized = text.strip().casefold()
            if normalized in {item.casefold() for item in placeholder_titles}:
                return True
            if normalized.startswith("chapter-") and normalized[8:].isdigit():
                return True
            if normalized.startswith("chapter_") and normalized[8:].isdigit():
                return True
            if normalized.startswith("chapter ") and normalized[8:].isdigit():
                return True
            return False

        def _next_slug(text: str) -> str:
            slug = _slugify(text)
            count = slug_counts.get(slug, 0) + 1
            slug_counts[slug] = count
            if count > 1:
                slug = f"{slug}-{count}"
            return slug

        if title:
            _next_slug(title)
        _next_slug("目录")

        toc_lines.append("## 目录")
        has_level_one = False
        for level, text in headings:
            if level != level_one and (level_two is None or level != level_two):
                continue
            if _is_placeholder_heading(text):
                if level == level_one:
                    has_level_one = False
                continue
            slug = _next_slug(text)
            if level == level_one:
                toc_lines.append(f"- [{text}](#{slug})")
                has_level_one = True
            else:
                if has_level_one:
                    toc_lines.append(f"  - [{text}](#{slug})")
                else:
                    toc_lines.append(f"- [{text}](#{slug})")
        toc_lines.append("")
        toc_lines.append("---")
        toc_lines.append("")

    lines = header_lines + toc_lines + body_lines
    content = "\n".join(lines).rstrip() + "\n"
    with path.open("w", encoding="utf-8") as handle:
        handle.write(content)


def _write_manifest(path: Path, payload: dict) -> None:
    _ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_epub(
    epub_path: Path,
    out_dir: Path,
    *,
    include_images: bool = True,
    strip_nav: bool = True,
    max_chunk_chars: int = 1200,
) -> dict:
    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB not found: {epub_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    blocks: List[Block] = []
    image_refs: Dict[str, ImageRef] = {}

    with zipfile.ZipFile(epub_path, "r") as zf:
        try:
            container_xml = zf.read("META-INF/container.xml")
        except KeyError as exc:
            raise EpubParseError("Missing META-INF/container.xml") from exc

        opf_path = read_container(container_xml)
        try:
            opf_xml = zf.read(opf_path)
        except KeyError as exc:
            raise EpubParseError(f"Missing OPF file: {opf_path}") from exc

        package = parse_opf(opf_xml, opf_path)
        zip_names = set(zf.namelist())

        order = 0
        for index, idref in enumerate(package.spine):
            item = package.manifest.get(idref)
            if item is None:
                continue
            html_path = resolve_href(package.opf_dir, item.href)
            if html_path not in zip_names:
                continue
            html_bytes = zf.read(html_path)
            chapter_fallback = f"chapter-{index + 1:03d}"
            _, html_blocks, image_list = extract_blocks(
                html_bytes,
                html_path,
                chapter_fallback,
                strip_nav=strip_nav,
                max_chunk_chars=max_chunk_chars,
            )
            for block in html_blocks:
                order += 1
                block.order = order
                block.id = f"b{order:06d}"
                if block.type == "image" and block.image:
                    block.image = _image_output_relpath(block.image)
                blocks.append(block)
            for image_ref in image_list:
                image_refs.setdefault(image_ref.href, image_ref)

        extracted_images: List[str] = []
        missing_images: List[str] = []
        if include_images:
            images_root = out_dir / "images"
            for href in sorted(image_refs.keys()):
                if href not in zip_names:
                    missing_images.append(href)
                    continue
                target_path = images_root / href
                _ensure_parent(target_path)
                with target_path.open("wb") as handle:
                    handle.write(zf.read(href))
                extracted_images.append(str(Path("images") / href))

    markdown_path = out_dir / "content.md"
    _write_markdown(markdown_path, blocks, title=package.title, creator=package.creator)

    manifest = {
        "source_epub": str(epub_path),
        "title": package.title,
        "creator": package.creator,
        "chapters": len(package.spine),
        "blocks": len(blocks),
        "images": extracted_images,
        "images_extracted": include_images,
        "missing_images": missing_images,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = out_dir / "manifest.json"
    _write_manifest(manifest_path, manifest)

    return manifest


def validate_output(out_dir: Path) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    content_md = out_dir / "content.md"
    has_md = content_md.exists()

    if not has_md:
        errors.append("content.md not found")
        return False, errors

    manifest_path = out_dir / "manifest.json"
    manifest = None
    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as handle:
            try:
                manifest = json.load(handle)
            except json.JSONDecodeError:
                errors.append("manifest.json is invalid JSON")

    images_extracted = True
    if isinstance(manifest, dict):
        images_extracted = bool(manifest.get("images_extracted", True))

    if images_extracted:
        if isinstance(manifest, dict):
            for image_path in manifest.get("images", []):
                target = out_dir / image_path
                if not target.exists():
                    errors.append(f"Missing image file: {image_path}")

    return len(errors) == 0, errors
