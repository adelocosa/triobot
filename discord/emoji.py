from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .guild import Guild


class Emoji:
    def __init__(self, guild: Guild, data: dict[str, Any]):
        self.guild: Guild = guild
        self.name: str = data["name"]
        self.id: int = int(data["id"])
        self.animated: bool = data.get("animated", False)

    def __str__(self) -> str:
        if self.animated:
            return f"<a:{self.name}:{self.id}>"
        return f"<:{self.name}:{self.id}>"
