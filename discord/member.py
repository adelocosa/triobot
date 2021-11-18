from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .user import User

if TYPE_CHECKING:
    from .guild import Guild

log = logging.getLogger(__name__)


class GuildMember:
    def __init__(self, guild: Guild, data: dict[str, Any]):
        self.guild = guild
        self.nick: None | str = data.get("nick", None)
        if data["user"]["id"] not in self.guild.client.users:
            user = User(data["user"])
            self.guild.client.users[user.id] = user
        else:
            user = self.guild.client.users[data["user"]["id"]]
        self.user: User = user
        log.debug(
            f"Added member {self.user.id} ({str(self)}) to guild {self.guild.id} ({self.guild.name})."
        )

    def __str__(self) -> str:
        if self.nick:
            return self.nick
        else:
            return self.user.username
