from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from .guild import Guild
from .user import User

if TYPE_CHECKING:
    from .client import Client

log = logging.getLogger(__name__)


class Event:
    def __init__(self, client: Client, name: str, data: dict[str, Any]):
        self.client = client
        self.name = name
        self.data = data
        log.info(f"Received {self.name} dispatch.")
        log.debug(json.dumps(data, indent=4))

    def process(self):
        handler = f"handle_{self.name.lower()}"
        try:
            getattr(self, handler)()
        except AttributeError:
            log.debug(f"Ignored {self.name} dispatch.")
        else:
            log.debug(f"Finished processing {self.name} dispatch.")

    def handle_ready(self):
        self.client.session_id = self.data["session_id"]
        self.client.user = User(self.data["user"])
        self.client.users[self.client.user.id] = self.client.user

    def handle_guild_create(self):
        guild = Guild(self.client, self.data)
        self.client.guilds[guild.id] = guild
