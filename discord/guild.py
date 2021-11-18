from typing import Any
from .emoji import Emoji
from .http_request import HTTPRequest


class Guild:
    def __init__(self, data: dict[str, Any]):
        self.id: int = data["id"]
        self.emojis: dict[str | int, Emoji] = self._parse_emojis(data["emojis"])

    def _parse_emojis(self, emoji_list: list[dict]) -> dict[str | int, Emoji]:
        # emoji objects are indexed by both name and id because both seem useful
        emojis = {}
        for emoji_data in emoji_list:
            emoji = Emoji(self, emoji_data)
            emojis[emoji.name] = emoji
            emojis[emoji.id] = emoji
        return emojis

    async def request_emojis(self) -> dict[str | int, Emoji]:
        request = HTTPRequest()
        response = await request.list_guild_emojis(self.id)
        if response.status_code != 200:
            return self.emojis
        self.emojis = self._parse_emojis(response.json())
        return self.emojis
