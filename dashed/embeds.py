import dataclasses
from typing import List, Literal, Optional


class EmbedFooter:
    pass


class EmbedImage:
    pass


@dataclasses.dataclass
class EmbedThumbnail:
    url: Optional[str] = None
    proxy_url: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None


class EmbedVideo:
    pass


class EmbedProvider:
    pass


class EmbedAuthor:
    pass


@dataclasses.dataclass
class EmbedField:
    name: str
    value: str
    inline: Optional[bool] = False


@dataclasses.dataclass
class Embed:
    title: Optional[str] = None
    type: Optional[
        Literal["rich", "image", "video", "gifv", "article", "link"]
    ] = "rich"
    description: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[str] = None
    color: Optional[int] = None
    footer: Optional[EmbedFooter] = None
    image: Optional[EmbedImage] = None
    thumbnail: Optional[EmbedThumbnail] = None
    video: Optional[EmbedVideo] = None
    provider: Optional[EmbedProvider] = None
    author: Optional[EmbedAuthor] = None
    fields: Optional[List[EmbedField]] = None
