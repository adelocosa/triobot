from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .guild import Guild

if TYPE_CHECKING:
    from .client import Client


class Event:
    def __init__(self, client: Client, name: str, data: dict[str, Any]):
        self.client = client
        self.name = name
        self.data = data

    def process(self):
        handler = f"handle_{self.name.lower()}"
        try:
            getattr(self, handler)()
        except AttributeError:
            pass

    def handle_ready(self):
        self.client.session_id = self.data["session_id"]

    def handle_guild_create(self):
        guild = Guild(self.data)
        self.client.guilds[guild.id] = guild
