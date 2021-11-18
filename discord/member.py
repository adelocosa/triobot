from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .user import User

if TYPE_CHECKING:
    from .client import Client


class GuildMember:
    def __init__(self, client: Client, data: dict[str, Any]):
        self.client = client
        self.muted: bool = data["mute"]
        self.deafened: bool = data["deaf"]
        self.nick: None | str = data.get("nick", None)
        if data["user"]["id"] not in self.client.users:
            user = User(data["user"])
            self.client.users[user.id] = user
        else:
            user = self.client.users[data["user"]["id"]]
        self.user: User = user

    def __str__(self) -> str:
        if self.nick:
            return self.nick
        else:
            return self.user.username
