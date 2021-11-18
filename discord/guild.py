from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .channel import Channel
from .emoji import Emoji
from .http_request import HTTPRequest
from .member import GuildMember

if TYPE_CHECKING:
    from .client import Client

log = logging.getLogger(__name__)


class Guild:
    def __init__(self, client: Client, data: dict[str, Any]):
        self.client = client
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.emojis: dict[str, Emoji] = self.parse_emojis(data["emojis"])
        self.members: dict[str, GuildMember] = self.parse_members(data["members"])
        self.channels: dict[str, Channel] = self.parse_channels(data["channels"])
        if data.get("presences", None):
            self.update_activities(data["presences"])

    def update(self, data: dict[str, Any]):
        self.name: str = data["name"]
        log.debug(f"Updated guild {self.id} ({self.name}).")

    def parse_emojis(self, emoji_list: list[dict]) -> dict[str, Emoji]:
        # emoji objects are indexed by both name and id because both seem useful
        emojis = {}
        for emoji_data in emoji_list:
            emoji = Emoji(self, emoji_data)
            emojis[emoji.name] = emoji
            emojis[emoji.id] = emoji
        return emojis

    def parse_members(self, member_list: list[dict]) -> dict[str, GuildMember]:
        members = {}
        for member_data in member_list:
            member = GuildMember(self, member_data)
            members[member.user.id] = member
        return members

    def parse_channels(self, channel_list: list[dict]) -> dict[str, Channel]:
        channels = {}
        for channel_data in channel_list:
            channel = Channel(self, channel_data)
            channels[channel.id] = channel
        return channels

    def update_activities(self, presence_list: list[dict]) -> None:
        for presence_data in presence_list:
            if presence_data["activities"]:
                user = self.client.users[presence_data["user"]["id"]]
                user.update_activities(presence_data["activities"])
        return

    async def request_emojis(self) -> dict[str, Emoji]:
        request = HTTPRequest()
        response = await request.list_guild_emojis(self.id)
        if response.status_code != 200:
            return self.emojis
        self.emojis = self.parse_emojis(response.json())
        return self.emojis
