from __future__ import annotations

import logging
import random
import time
from typing import TYPE_CHECKING, Callable

import trio

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
        self.event_listeners: dict[str, Callable] = {}
        self.interaction_listeners: dict[str, Callable] = {}
        self.tasks: list[Callable] = []

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

    def slash_command(self, func: Callable):
        # decorator for responding to slash commands
        # function name must correspond to command name
        self.interaction_listeners[func.__name__] = func
        return func

    def task(self, func: Callable):
        # decorator to create looping background tasks
        # tasks will restart on disconnect/reconnect
        self.tasks.append(func)
        return func

    async def on_connected(self):
        log.info("Connected!")
        self.reset_delay()

    async def background_tasks(self):
        async with trio.open_nursery() as nursery:
            for task in self.tasks:
                nursery.start_soon(task)

    async def interaction_response(self, interaction: SlashCommand, message: str):
        payload = {"type": 4, "data": {"content": message}}
        r = HTTPRequest()
        await r.interaction_response(interaction.id, interaction.token, payload)

    async def send_message(self, channel: str, message: str):
        payload = {"content": message}
        r = HTTPRequest()
        await r.create_message(channel, payload)
