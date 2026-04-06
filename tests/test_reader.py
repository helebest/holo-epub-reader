from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from epub import _first_text, read_container, resolve_href
from html_extract import _chunk_text, _normalize_title, _is_placeholder_title
from models import Block
from reader import EpubParseError, parse_epub, validate_output


def _create_epub(
    tmp_path: Path,
    *,
    body: str,
    include_container: bool = True,
    include_opf: bool = True,
    include_image_tag: bool = True,
    include_image_file: bool = True,
) -> Path:
    root = tmp_path / "sample"
    meta_inf = root / "META-INF"
    oebps = root / "OEBPS"
    images = oebps / "images"
    meta_inf.mkdir(parents=True)
    images.mkdir(parents=True)

    if include_container:
        container_xml = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
"""
        (meta_inf / "container.xml").write_text(container_xml, encoding="utf-8")

    if include_opf:
        image_item = (
            '<item id="img1" href="images/pic.jpg" media-type="image/jpeg" />'
            if include_image_tag
            else ""
        )
        content_opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Sample</dc:title>
    <dc:creator>Tester</dc:creator>
  </metadata>
  <manifest>
    <item id="chap1" href="chapter1.xhtml" media-type="application/xhtml+xml" />
    {image_item}
  </manifest>
  <spine toc="ncx">
    <itemref idref="chap1" />
  </spine>
</package>
"""
        (oebps / "content.opf").write_text(content_opf, encoding="utf-8")

    image_html = '<img src="images/pic.jpg" alt="A pic" />' if include_image_tag else ""
    chapter1 = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>未知</title>
  </head>
  <body>
    {body}
    {image_html}
  </body>
</html>
"""
    (oebps / "chapter1.xhtml").write_text(chapter1, encoding="utf-8")

    if include_image_file:
        (images / "pic.jpg").write_bytes(b"\x00\x01\x02")

    epub_path = tmp_path / "sample.epub"
    with zipfile.ZipFile(epub_path, "w") as zf:
        for path in root.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(root))

    return epub_path


def test_block_to_dict_filters_none() -> None:
    block = Block(id="b1", type="text", chapter="ch1", order=0, text="hello")
    d = block.to_dict()
    assert d["text"] == "hello"
    assert "image" not in d
    assert "alt" not in d


def test_first_text_returns_none_for_none() -> None:
    assert _first_text(None) is None


def test_read_container_missing_rootfile() -> None:
    xml = b'<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles></rootfiles></container>'
    with pytest.raises(ValueError, match="missing rootfile"):
        read_container(xml)


def test_read_container_missing_full_path() -> None:
    xml = b'<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile /></rootfiles></container>'
    with pytest.raises(ValueError, match="missing full-path"):
        read_container(xml)


def test_resolve_href_empty_base_dir() -> None:
    result = resolve_href("", "chapter1.xhtml")
    assert result == "chapter1.xhtml"


def test_chunk_text_splits_by_words() -> None:
    text = "one two three four five"
    chunks = _chunk_text(text, 10)
    assert len(chunks) > 1
    assert all(len(c) <= 12 for c in chunks)  # allow word boundary


def test_normalize_title_none() -> None:
    assert _normalize_title(None) is None


def test_is_placeholder_title_empty() -> None:
    assert _is_placeholder_title("") is True
    assert _is_placeholder_title(None) is True


def test_parse_and_validate_happy_path(tmp_path: Path) -> None:
    body = """
    <h1>Chapter One</h1>
    <h2>Section A</h2>
    <h2>Contents</h2>
    <p>Hello world.</p>
    <ol>
      <li>First item</li>
      <li>Second item</li>
    </ol>
    """
    epub_path = _create_epub(tmp_path, body=body)
    out_dir = tmp_path / "out"

    manifest = parse_epub(epub_path, out_dir, include_images=True)

    assert (out_dir / "content.md").exists()
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "images" / "OEBPS" / "images" / "pic.jpg").exists()
    assert manifest["images_extracted"] is True

    ok, errors = validate_output(out_dir)
    assert ok, errors

    content = (out_dir / "content.md").read_text(encoding="utf-8")
    assert "## Chapter One" in content
    assert "## 目录" in content
    assert "- [Chapter One]" in content
    assert "  - [Section A]" in content
    assert "#### Contents" in content
    assert "- [Contents]" not in content
    assert "1. First item" in content
    assert "2. Second item" in content
    assert "![A pic]" in content


def test_parse_supports_blockquote_pre_and_unordered_list(tmp_path: Path) -> None:
    body = """
    <h1>Chapter One</h1>
    <blockquote>line1\nline2</blockquote>
    <pre>code\nline</pre>
    <ul><li>bullet</li></ul>
    """
    epub_path = _create_epub(tmp_path, body=body)
    out_dir = tmp_path / "out"

    parse_epub(epub_path, out_dir, include_images=True)
    content = (out_dir / "content.md").read_text(encoding="utf-8")

    assert "> line1" in content
    assert "```" in content
    assert "- bullet" in content


def test_parse_without_image_extraction_sets_manifest_flag(tmp_path: Path) -> None:
    body = "<h1>Chapter One</h1><p>Text</p>"
    epub_path = _create_epub(tmp_path, body=body, include_image_tag=True, include_image_file=False)
    out_dir = tmp_path / "out"

    manifest = parse_epub(epub_path, out_dir, include_images=False)

    assert manifest["images_extracted"] is False
    assert manifest["images"] == []

    ok, errors = validate_output(out_dir)
    assert ok, errors


def test_parse_collects_missing_images(tmp_path: Path) -> None:
    body = "<h1>Chapter One</h1><p>Text</p>"
    epub_path = _create_epub(tmp_path, body=body, include_image_tag=True, include_image_file=False)
    out_dir = tmp_path / "out"

    manifest = parse_epub(epub_path, out_dir, include_images=True)

    assert manifest["missing_images"] == ["OEBPS/images/pic.jpg"]
    assert manifest["images"] == []


def test_parse_chunks_long_unspaced_text(tmp_path: Path) -> None:
    long_word = "a" * 25
    body = f"<h1>Chapter One</h1><p>{long_word}</p>"
    epub_path = _create_epub(tmp_path, body=body, include_image_tag=False)
    out_dir = tmp_path / "out"

    parse_epub(epub_path, out_dir, include_images=False, max_chunk_chars=10)
    content = (out_dir / "content.md").read_text(encoding="utf-8")

    assert "aaaaaaaaaa" in content
    assert "aaaaa" in content


def test_parse_raises_when_container_missing(tmp_path: Path) -> None:
    body = "<h1>Chapter One</h1><p>Text</p>"
    epub_path = _create_epub(
        tmp_path,
        body=body,
        include_container=False,
        include_opf=True,
        include_image_tag=False,
    )

    with pytest.raises(EpubParseError, match="Missing META-INF/container.xml"):
        parse_epub(epub_path, tmp_path / "out")


def test_parse_raises_when_opf_missing(tmp_path: Path) -> None:
    body = "<h1>Chapter One</h1><p>Text</p>"
    epub_path = _create_epub(
        tmp_path,
        body=body,
        include_container=True,
        include_opf=False,
        include_image_tag=False,
    )

    with pytest.raises(EpubParseError, match="Missing OPF file"):
        parse_epub(epub_path, tmp_path / "out")


def test_validate_output_missing_content_file(tmp_path: Path) -> None:
    ok, errors = validate_output(tmp_path)
    assert not ok
    assert "content.md not found" in errors


def test_validate_output_invalid_manifest_json(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    (out_dir / "content.md").write_text("ok", encoding="utf-8")
    (out_dir / "manifest.json").write_text("{invalid", encoding="utf-8")

    ok, errors = validate_output(out_dir)
    assert not ok
    assert "manifest.json is invalid JSON" in errors


def test_parse_raises_when_epub_not_found(tmp_path: Path) -> None:
    fake = tmp_path / "nonexistent.epub"
    with pytest.raises(FileNotFoundError, match="EPUB not found"):
        parse_epub(fake, tmp_path / "out")


def test_parse_text_chunk_splits_long_text(tmp_path: Path) -> None:
    """Cover _chunk_text word-splitting logic (html_extract lines 24-41)."""
    long_text = " ".join(["word"] * 200)
    body = f"<h1>Chapter One</h1><p>{long_text}</p>"
    epub_path = _create_epub(tmp_path, body=body, include_image_tag=False)
    out_dir = tmp_path / "out"

    parse_epub(epub_path, out_dir, include_images=False, max_chunk_chars=50)
    content = (out_dir / "content.md").read_text(encoding="utf-8")
    assert "word" in content


def test_parse_keeps_nav_content(tmp_path: Path) -> None:
    """Cover ignore_stack logic (html_extract lines 91-92, 200)."""
    body = """
    <h1>Chapter One</h1>
    <nav><p>Navigation content</p></nav>
    <p>Main text</p>
    """
    epub_path = _create_epub(tmp_path, body=body, include_image_tag=False)
    out_dir = tmp_path / "out"

    parse_epub(epub_path, out_dir, include_images=False, strip_nav=False)
    content = (out_dir / "content.md").read_text(encoding="utf-8")
    assert "Navigation content" in content


def test_parse_strips_nav_by_default(tmp_path: Path) -> None:
    """Verify nav stripping (html_extract lines 91-92, 200)."""
    body = """
    <h1>Chapter One</h1>
    <nav><p>Navigation content</p></nav>
    <p>Main text</p>
    """
    epub_path = _create_epub(tmp_path, body=body, include_image_tag=False)
    out_dir = tmp_path / "out"

    parse_epub(epub_path, out_dir, include_images=False, strip_nav=True)
    content = (out_dir / "content.md").read_text(encoding="utf-8")
    assert "Navigation content" not in content
    assert "Main text" in content


def test_parse_chapter_separator_between_chapters(tmp_path: Path) -> None:
    """Cover chapter separator lines (reader lines 65-66).

    Create an EPUB with two spine items to trigger chapter transitions.
    """
    root = tmp_path / "sample"
    meta_inf = root / "META-INF"
    oebps = root / "OEBPS"
    meta_inf.mkdir(parents=True)
    oebps.mkdir(parents=True)

    container_xml = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
"""
    (meta_inf / "container.xml").write_text(container_xml, encoding="utf-8")

    content_opf = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Multi</dc:title>
    <dc:creator>Tester</dc:creator>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml" />
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml" />
  </manifest>
  <spine>
    <itemref idref="ch1" />
    <itemref idref="ch2" />
  </spine>
</package>
"""
    (oebps / "content.opf").write_text(content_opf, encoding="utf-8")

    ch1 = """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body><h1>Chapter One</h1><p>Text one.</p></body>
</html>
"""
    ch2 = """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body><h1>Chapter Two</h1><p>Text two.</p></body>
</html>
"""
    (oebps / "ch1.xhtml").write_text(ch1, encoding="utf-8")
    (oebps / "ch2.xhtml").write_text(ch2, encoding="utf-8")

    epub_path = tmp_path / "multi.epub"
    with zipfile.ZipFile(epub_path, "w") as zf:
        for path in root.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(root))

    out_dir = tmp_path / "out"
    parse_epub(epub_path, out_dir, include_images=False)
    content = (out_dir / "content.md").read_text(encoding="utf-8")

    assert "## Chapter One" in content
    assert "## Chapter Two" in content
    assert "---" in content


def test_parse_heading_after_list_ends_list(tmp_path: Path) -> None:
    """Cover in_list reset on heading (reader lines 75-76) and text (92-93)."""
    body = """
    <h1>Chapter One</h1>
    <ul><li>item1</li><li>item2</li></ul>
    <h2>Next Section</h2>
    <ul><li>item3</li></ul>
    <p>Paragraph after list</p>
    """
    epub_path = _create_epub(tmp_path, body=body, include_image_tag=False)
    out_dir = tmp_path / "out"

    parse_epub(epub_path, out_dir, include_images=False)
    content = (out_dir / "content.md").read_text(encoding="utf-8")
    assert "- item1" in content
    assert "### Next Section" in content
    assert "Paragraph after list" in content


def test_parse_invalid_ol_start_attribute(tmp_path: Path) -> None:
    """Cover ValueError on invalid ol start (html_extract lines 104-105)."""
    body = """
    <h1>Chapter One</h1>
    <ol start="abc"><li>Item</li></ol>
    """
    epub_path = _create_epub(tmp_path, body=body, include_image_tag=False)
    out_dir = tmp_path / "out"

    parse_epub(epub_path, out_dir, include_images=False)
    content = (out_dir / "content.md").read_text(encoding="utf-8")
    assert "1. Item" in content


def test_parse_rejects_path_traversal_in_image(tmp_path: Path) -> None:
    """Malicious EPUB with ../../ in image href must not write outside output dir."""
    root = tmp_path / "malicious"
    meta_inf = root / "META-INF"
    oebps = root / "OEBPS"
    meta_inf.mkdir(parents=True)
    oebps.mkdir(parents=True)

    container_xml = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
"""
    (meta_inf / "container.xml").write_text(container_xml, encoding="utf-8")

    # After resolve_href normalizes "images/../../../../evil.txt" relative to
    # "OEBPS", the key becomes "../../evil.txt". The ZIP entry must match this
    # normalized name for the traversal to succeed.
    normalized_href = "../../evil.txt"
    content_opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Evil</dc:title>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml" />
    <item id="img1" href="images/../../../../evil.txt" media-type="image/jpeg" />
  </manifest>
  <spine><itemref idref="ch1" /></spine>
</package>
"""
    (oebps / "content.opf").write_text(content_opf, encoding="utf-8")

    ch1 = """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
  <h1>Chapter One</h1>
  <img src="images/../../../../evil.txt" alt="evil" />
</body>
</html>
"""
    (oebps / "ch1.xhtml").write_text(ch1, encoding="utf-8")

    epub_path = tmp_path / "evil.epub"
    with zipfile.ZipFile(epub_path, "w") as zf:
        for path in root.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(root))
        # ZIP entry exists so the code reaches the path containment check
        # (not short-circuited by the "not in zip_names" guard)
        zf.writestr(normalized_href, b"EVIL PAYLOAD")

    out_dir = tmp_path / "out"
    manifest = parse_epub(epub_path, out_dir, include_images=True)

    # The evil file must NOT exist outside out_dir
    evil_path = tmp_path / "evil.txt"
    assert not evil_path.exists(), "Path traversal: file written outside output dir!"

    # The exact traversal href should be rejected into missing_images
    assert normalized_href in manifest["missing_images"]


def test_validate_output_reports_missing_image_file(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    (out_dir / "content.md").write_text("ok", encoding="utf-8")
    payload = {
        "images_extracted": True,
        "images": ["images/missing.jpg"],
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )

    ok, errors = validate_output(out_dir)
    assert not ok
    assert "Missing image file: images/missing.jpg" in errors
