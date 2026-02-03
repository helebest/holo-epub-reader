from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import zipfile

from epub_reader.reader import parse_epub, validate_output


def _create_sample_epub(tmp_path: Path) -> Path:
    root = tmp_path / "sample"
    meta_inf = root / "META-INF"
    oebps = root / "OEBPS"
    images = oebps / "images"
    meta_inf.mkdir(parents=True)
    images.mkdir(parents=True)

    container_xml = """<?xml version=\"1.0\"?>
<container version=\"1.0\" xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\">
  <rootfiles>
    <rootfile full-path=\"OEBPS/content.opf\" media-type=\"application/oebps-package+xml\" />
  </rootfiles>
</container>
"""
    (meta_inf / "container.xml").write_text(container_xml, encoding="utf-8")

    content_opf = """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<package xmlns=\"http://www.idpf.org/2007/opf\" unique-identifier=\"BookId\" version=\"2.0\">
  <metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\">
    <dc:title>Sample</dc:title>
    <dc:creator>Tester</dc:creator>
  </metadata>
  <manifest>
    <item id=\"chap1\" href=\"chapter1.xhtml\" media-type=\"application/xhtml+xml\" />
    <item id=\"img1\" href=\"images/pic.jpg\" media-type=\"image/jpeg\" />
  </manifest>
  <spine toc=\"ncx\">
    <itemref idref=\"chap1\" />
  </spine>
</package>
"""
    (oebps / "content.opf").write_text(content_opf, encoding="utf-8")

    chapter1 = """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<html xmlns=\"http://www.w3.org/1999/xhtml\">
  <head>
    <title>未知</title>
  </head>
  <body>
    <h1>Chapter One</h1>
    <h2>Section A</h2>
    <h2>Contents</h2>
    <p>Hello world.</p>
    <ol>
      <li>First item</li>
      <li>Second item</li>
    </ol>
    <img src=\"images/pic.jpg\" alt=\"A pic\" />
  </body>
</html>
"""
    (oebps / "chapter1.xhtml").write_text(chapter1, encoding="utf-8")

    (images / "pic.jpg").write_bytes(b"\x00\x01\x02")

    epub_path = tmp_path / "sample.epub"
    with zipfile.ZipFile(epub_path, "w") as zf:
        for path in root.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(root))

    return epub_path


class ReaderTests(unittest.TestCase):
    def test_parse_and_validate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            epub_path = _create_sample_epub(tmp_path)
            out_dir = tmp_path / "out"

            manifest = parse_epub(epub_path, out_dir, include_images=True)

            self.assertTrue((out_dir / "content.md").exists())
            self.assertTrue((out_dir / "manifest.json").exists())
            self.assertTrue((out_dir / "images" / "OEBPS" / "images" / "pic.jpg").exists())

            self.assertGreaterEqual(manifest["blocks"], 2)
            self.assertTrue(manifest["images_extracted"])

            ok, errors = validate_output(out_dir)
            self.assertTrue(ok, f"Validation errors: {errors}")

            content = (out_dir / "content.md").read_text(encoding="utf-8")
            self.assertIn("## Chapter One", content)
            self.assertIn("## 目录", content)
            self.assertIn("- [Chapter One]", content)
            self.assertIn("  - [Section A]", content)
            self.assertIn("#### Contents", content)
            self.assertNotIn("- [Contents]", content)
            self.assertIn("Hello world.", content)
            self.assertIn("1. First item", content)
            self.assertIn("2. Second item", content)
            self.assertIn("![A pic]", content)


if __name__ == "__main__":
    unittest.main()
