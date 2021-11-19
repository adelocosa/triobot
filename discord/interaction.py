from __future__ import annotations


from enum import IntEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .guild import Guild


class InteractionType(IntEnum):

    SLASH_COMMAND = 2
    MESSAGE_COMPONENT = 3
    AUTOCOMPLETE = 4


class SlashCommand:
    def __init__(self, guild: Guild, data: dict[str, Any]):
        self.id = data["id"]
        self.token = data["token"]
        self.guild = guild
        self.channel = self.guild.channels[data["channel_id"]]
        self.member = self.guild.members[data["member"]["user"]["id"]]
        self.data = data["data"]
        self.name = self.data["name"]
