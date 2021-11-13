from dataclasses import dataclass, field
from .http_request import HTTPRequest
from .emoji import Emoji


@dataclass
class Guild:
    id: int
    emojis: dict[str | int, Emoji] = field(default_factory=dict)

    async def request_emojis(self) -> dict[str | int, Emoji]:
        request = HTTPRequest()
        response = await request.list_guild_emojis(self.id)
        if response.status_code != 200:
            return self.emojis
        emojis = {}
        for emoji_data in response.json():
            emoji = Emoji(self, emoji_data)
            emojis[emoji.name] = emoji
            emojis[emoji.id] = emoji
        self.emojis = emojis
        return self.emojis
