from __future__ import annotations

from dataclasses import dataclass
import posixpath
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ManifestItem:
    id: str
    href: str
    media_type: Optional[str]


@dataclass(frozen=True)
class OpfPackage:
    title: Optional[str]
    creator: Optional[str]
    manifest: Dict[str, ManifestItem]
    spine: List[str]
    opf_dir: str


def _first_text(node: Optional[ET.Element]) -> Optional[str]:
    if node is None:
        return None
    text = node.text or ""
    text = " ".join(text.split())
    return text or None


def read_container(container_xml: bytes) -> str:
    root = ET.fromstring(container_xml)
    rootfile = root.find(".//{*}rootfile")
    if rootfile is None:
        raise ValueError("container.xml missing rootfile")
    full_path = rootfile.get("full-path")
    if not full_path:
        raise ValueError("container.xml rootfile missing full-path")
    return full_path


def parse_opf(opf_xml: bytes, opf_path: str) -> OpfPackage:
    root = ET.fromstring(opf_xml)
    metadata = root.find(".//{*}metadata")
    title = _first_text(metadata.find(".//{*}title") if metadata is not None else None)
    creator = _first_text(metadata.find(".//{*}creator") if metadata is not None else None)

    manifest: Dict[str, ManifestItem] = {}
    manifest_root = root.find(".//{*}manifest")
    if manifest_root is not None:
        for item in manifest_root.findall(".//{*}item"):
            item_id = item.get("id")
            href = item.get("href")
            if not item_id or not href:
                continue
            manifest[item_id] = ManifestItem(
                id=item_id,
                href=href,
                media_type=item.get("media-type"),
            )

    spine: List[str] = []
    spine_root = root.find(".//{*}spine")
    if spine_root is not None:
        for itemref in spine_root.findall(".//{*}itemref"):
            idref = itemref.get("idref")
            if idref:
                spine.append(idref)

    opf_dir = posixpath.dirname(opf_path)
    return OpfPackage(
        title=title,
        creator=creator,
        manifest=manifest,
        spine=spine,
        opf_dir=opf_dir,
    )


def resolve_href(base_dir: str, href: str) -> str:
    clean_href = href.split("#", 1)[0].split("?", 1)[0]
    if base_dir:
        joined = posixpath.join(base_dir, clean_href)
    else:
        joined = clean_href
    return posixpath.normpath(joined)
