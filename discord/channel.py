from __future__ import annotations

from typing import TYPE_CHECKING, Any
from enum import IntEnum

if TYPE_CHECKING:
    from .guild import Guild


class ChannelType(IntEnum):
    TEXT = 0
    DM = 1
    VOICE = 2


class Channel:
    def __init__(self, guild: Guild, data: dict[str, Any]):
        self.guild = guild
        self.id: int = int(data["id"])
        self.type: int = data["type"]
        self.position: None | int = data.get("position", None)
        self.name: None | str = data.get("name", None)
        self.topic: None | str = data.get("topic", None)
        self.bitrate: None | int = data.get("bitrate", None)  # in b/s
