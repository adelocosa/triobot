import logging
from typing import Any

from enum import IntEnum

log = logging.getLogger(__name__)


class Activity:
    def __init__(self, type: int, name: str, url: None | str):
        self.type = type
        self.name = name
        self.url = url

    def __str__(self):
        return f"<{ActivityType(self.type).name} - {self.name}>"


class ActivityType(IntEnum):
    PLAYING = 0
    STREAMING = 1
    LISTENING = 2
    WATCHING = 3
    CUSTOM = 4
    COMPETING = 5


class User:
    def __init__(self, data: dict[str, Any]):
        self.id: int = int(data["id"])
        self.username: str = data["username"]
        self.number: int = int(data["discriminator"])
        self.activities: list[Activity] = []
        log.debug(f"Created user {self.id} ({self.username}).")

    def update_activities(self, data: list[dict[str, Any]]) -> None:
        activities = []
        for activity in data:
            type = activity["type"]
            name = activity["name"]
            url = activity.get("url", None)
            activities.append(Activity(type, name, url))
        log.debug(
            f"User {self.id} ({self.username}) activities set to {[str(activity) for activity in activities]}]"
        )
        self.activites = activities
        return
