from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .channel import Channel
    from .guild import Guild
    from .member import GuildMember

class InteractionType(IntEnum):

    SLASH_COMMAND = 2
    MESSAGE_COMPONENT = 3
    AUTOCOMPLETE = 4


class SlashCommand:
    def __init__(self, guild: Guild, data: dict[str, Any]):
        self.guild = guild
        self.id: str = data["id"]
        self.token: str = data["token"]
        self.channel: Channel = self.guild.channels[data["channel_id"]]
        self.member: GuildMember = self.guild.members[data["member"]["user"]["id"]]
        self.data: dict[str, Any] = data["data"]
        self.name: str = self.data["name"]
