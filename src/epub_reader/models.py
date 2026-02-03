from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Block:
    id: str
    type: str
    chapter: Optional[str]
    order: int
    text: Optional[str] = None
    image: Optional[str] = None
    alt: Optional[str] = None
    source_href: Optional[str] = None
    level: Optional[int] = None
    tag: Optional[str] = None
    list_type: Optional[str] = None
    list_index: Optional[int] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


@dataclass(frozen=True)
class ImageRef:
    href: str
    alt: Optional[str]
    source_html: str
