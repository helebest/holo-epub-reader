from __future__ import annotations

from html.parser import HTMLParser
from typing import List, Optional, Tuple
import posixpath

from epub import resolve_href
from models import Block, ImageRef

BLOCK_TEXT_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
PLACEHOLDER_TITLES = {"未知", "unknown", "untitled", "title", "无标题"}


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def _chunk_text(text: str, max_chars: int) -> List[str]:
    if max_chars <= 0 or len(text) <= max_chars:
        return [text]
    if " " not in text:
        return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0
    for word in text.split():
        extra = 1 if current else 0
        if current_len + len(word) + extra > max_chars and current:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            if current:
                current_len += 1 + len(word)
            else:
                current_len = len(word)
            current.append(word)
    if current:
        chunks.append(" ".join(current))
    return chunks


def _resolve_image(html_path: str, src: str) -> str:
    base = posixpath.dirname(html_path)
    return resolve_href(base, src)


def _normalize_title(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    cleaned = _clean_text(text)
    return cleaned or None


def _is_placeholder_title(text: Optional[str]) -> bool:
    if not text:
        return True
    normalized = text.strip().casefold()
    return normalized in {item.casefold() for item in PLACEHOLDER_TITLES}


class _HTMLBlockParser(HTMLParser):
    def __init__(self, html_path: str, strip_nav: bool) -> None:
        super().__init__(convert_charrefs=True)
        self.html_path = html_path
        self.strip_nav = strip_nav
        self.blocks: List[Block] = []
        self.image_refs: List[ImageRef] = []
        self.title_parts: List[str] = []
        self.first_heading: Optional[str] = None
        self.current_tag: Optional[str] = None
        self.current_text_parts: List[str] = []
        self.ignore_stack: List[str] = []
        self.tag_stack: List[str] = []
        self._in_title = False
        self.list_stack: List[dict] = []
        self.current_list_type: Optional[str] = None
        self.current_list_index: Optional[int] = None

    def _is_ignored(self) -> bool:
        return bool(self.ignore_stack)

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        self.tag_stack.append(tag)

        if tag in {"script", "style", "noscript"} or (
            self.strip_nav and tag in {"nav", "header", "footer", "aside"}
        ):
            self.ignore_stack.append(tag)
            return

        if tag == "title":
            self._in_title = True
            return

        attrs_dict = {key: value for key, value in attrs}

        if tag == "ol" and not self._is_ignored():
            start = attrs_dict.get("start")
            try:
                start_index = int(start) if start else 1
            except ValueError:
                start_index = 1
            self.list_stack.append({"type": "ol", "index": start_index - 1})
            return

        if tag == "ul" and not self._is_ignored():
            self.list_stack.append({"type": "ul", "index": 0})
            return

        if tag == "img" and not self._is_ignored():
            src = attrs_dict.get("src")
            if src:
                href = _resolve_image(self.html_path, src)
                alt = attrs_dict.get("alt") or attrs_dict.get("title")
                self.blocks.append(
                    Block(
                        id="",
                        type="image",
                        chapter=None,
                        order=0,
                        text=None,
                        image=href,
                        alt=_clean_text(alt) if alt else None,
                        source_href=href,
                        level=None,
                        tag="img",
                    )
                )
                self.image_refs.append(ImageRef(href=href, alt=alt, source_html=self.html_path))
            return

        if tag in BLOCK_TEXT_TAGS and not self._is_ignored() and self.current_tag is None:
            self.current_tag = tag
            self.current_text_parts = []
            if tag == "li" and self.list_stack:
                current_list = self.list_stack[-1]
                if current_list["type"] == "ol":
                    current_list["index"] += 1
                    self.current_list_index = current_list["index"]
                self.current_list_type = current_list["type"]

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if self.current_tag == tag:
            raw_text = "".join(self.current_text_parts)
            if tag == "pre":
                text = raw_text.replace("\r\n", "\n").strip("\n")
            else:
                text = _clean_text(raw_text)
            if text:
                if tag in HEADING_TAGS:
                    level = int(tag[1])
                    if self.first_heading is None:
                        self.first_heading = text
                    self.blocks.append(
                        Block(
                            id="",
                            type="heading",
                            chapter=None,
                            order=0,
                            text=text,
                            image=None,
                            alt=None,
                            source_href=self.html_path,
                            level=level,
                            tag=tag,
                        )
                    )
                else:
                    self.blocks.append(
                        Block(
                            id="",
                            type="text",
                            chapter=None,
                            order=0,
                            text=text,
                            image=None,
                            alt=None,
                            source_href=self.html_path,
                            level=None,
                            tag=tag,
                            list_type=self.current_list_type,
                            list_index=self.current_list_index,
                        )
                    )
            self.current_tag = None
            self.current_text_parts = []
            self.current_list_type = None
            self.current_list_index = None

        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

        if self.ignore_stack and self.ignore_stack[-1] == tag:
            self.ignore_stack.pop()

        if self.list_stack and self.list_stack[-1]["type"] == tag:
            self.list_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if not self._is_ignored() and self.current_tag is not None:
            self.current_text_parts.append(data)

    @property
    def title_text(self) -> Optional[str]:
        title = _clean_text("".join(self.title_parts))
        return title or None


def extract_blocks(
    html_bytes: bytes,
    html_path: str,
    chapter_fallback: str,
    *,
    strip_nav: bool = True,
    max_chunk_chars: int = 1200,
) -> Tuple[str, List[Block], List[ImageRef]]:
    parser = _HTMLBlockParser(html_path, strip_nav=strip_nav)
    parser.feed(html_bytes.decode("utf-8", errors="replace"))
    parser.close()

    blocks: List[Block] = []
    for block in parser.blocks:
        if block.type == "text" and block.text:
            if block.tag in {"li", "blockquote", "pre"}:
                blocks.append(block)
            else:
                for chunk in _chunk_text(block.text, max_chunk_chars):
                    blocks.append(
                        Block(
                            id=block.id,
                            type=block.type,
                            chapter=None,
                            order=block.order,
                            text=chunk,
                            image=None,
                            alt=None,
                            source_href=block.source_href,
                            level=None,
                            tag=block.tag,
                        )
                    )
        else:
            blocks.append(block)

    title_text = _normalize_title(parser.title_text)
    heading_text = _normalize_title(parser.first_heading)
    if _is_placeholder_title(title_text):
        title_text = None
    if _is_placeholder_title(heading_text):
        heading_text = None
    chapter_title = title_text or heading_text or chapter_fallback
    for block in blocks:
        block.chapter = chapter_title

    return chapter_title, blocks, parser.image_refs
