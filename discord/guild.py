from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .channel import Channel
from .emoji import Emoji
from .member import GuildMember
from .http_request import HTTPRequest

if TYPE_CHECKING:
    from .client import Client


class Guild:
    def __init__(self, client: Client, data: dict[str, Any]):
        self.client = client
        self.id: int = data["id"]
        self.emojis: dict[str | int, Emoji] = self._parse_emojis(data["emojis"])
        self.members: dict[int, GuildMember] = self._parse_members(data["members"])
        self.channels: dict[int, Channel] = self._parse_channels(data["channels"])

    def _parse_emojis(self, emoji_list: list[dict]) -> dict[str | int, Emoji]:
        # emoji objects are indexed by both name and id because both seem useful
        emojis = {}
        for emoji_data in emoji_list:
            emoji = Emoji(self, emoji_data)
            emojis[emoji.name] = emoji
            emojis[emoji.id] = emoji
        return emojis

    def _parse_members(self, member_list: list[dict]) -> dict[int, GuildMember]:
        members = {}
        for member_data in member_list:
            member = GuildMember(self.client, member_data)
            members[member.user.id] = member
        return members

    def _parse_channels(self, channel_list: list[dict]) -> dict[int, Channel]:
        channels = {}
        for channel_data in channel_list:
            channel = Channel(self, channel_data)
            channels[channel.id] = channel
        return channels
        
    async def request_emojis(self) -> dict[str | int, Emoji]:
        request = HTTPRequest()
        response = await request.list_guild_emojis(self.id)
        if response.status_code != 200:
            return self.emojis
        self.emojis = self._parse_emojis(response.json())
        return self.emojis
