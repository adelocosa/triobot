from __future__ import annotations

import logging
from enum import IntEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .guild import Guild

log = logging.getLogger(__name__)


class ChannelType(IntEnum):
    TEXT = 0
    DM = 1
    VOICE = 2


class Channel:
    def __init__(self, guild: Guild, data: dict[str, Any]):
        self.guild = guild
        self.id: str = data["id"]
        self.type: int = data["type"]
        self.position: None | int = data.get("position", None)
        self.name: None | str = data.get("name", None)
        self.topic: None | str = data.get("topic", None)
        self.bitrate: None | int = data.get("bitrate", None)  # in b/s
        log.debug(
            f"Added channel {self.id} ({self.name}) to guild {self.guild.id} ({self.guild.name})."
        )

    def update(self, data: dict[str, Any]):
        self.position = data.get("position", self.position)
        self.name = data.get("name", self.name)
        self.topic = data.get("topic", self.topic)
        self.bitrate = data.get("bitrate", self.bitrate)
        log.debug(
            f"Updated channel {self.id} ({self.name}) in guild {self.guild.id} ({self.guild.name})."
        )
