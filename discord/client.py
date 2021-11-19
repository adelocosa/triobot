from __future__ import annotations

import logging
import random
import time
from typing import TYPE_CHECKING

import trio

from .event import Event
from .gateway import GatewayConnection
from .http_request import HTTPRequest

if TYPE_CHECKING:
    from .guild import Guild
    from .interaction import SlashCommand
    from .user import User

log = logging.getLogger(__name__)


class Client:

    START_DELAY = 1.1
    MAX_DELAY = 32

    def __init__(self, TOKEN: str):
        self.TOKEN = TOKEN
        self.user: None | User = None
        self.sequence: None | int = None
        self.session_id: None | str = None
        self.delay = self.START_DELAY
        self.guilds: dict[str, Guild] = {}
        self.users: dict[str, User] = {}

    def connect(self):
        while True:
            self.connection = GatewayConnection(self, self.TOKEN)
            log.info("Attempting to connect...")
            trio.run(self.connection.connect)
            log.warning(f"Disconnected! Reconnecting in {self.delay:.1f} seconds...")
            time.sleep(self.delay)
            self.increase_delay()

    def increase_delay(self):
        new_delay = int(self.delay) * 2
        if new_delay != self.MAX_DELAY:
            new_delay += random.random()
        self.delay = new_delay

    def reset_delay(self):
        self.delay = self.START_DELAY

    def clear_state(self):
        self.user = None
        self.sequence = None
        self.session_id = None
        self.guilds = {}
        self.users = {}

    def watch_interaction(self, func):
        Event.interaction_listeners[func.__name__] = func
        return func

    async def interaction_response(self, interaction: SlashCommand, message: str):
        payload = {"type": 4, "data": {"content": message}}
        r = HTTPRequest()
        await r.interaction_response(interaction.id, interaction.token, payload)
