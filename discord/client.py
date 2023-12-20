from __future__ import annotations

import logging
import random
import time
import json
from typing import TYPE_CHECKING, Callable, Optional, Any

import trio

from .gateway import GatewayConnection, Opcode, DotColor
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
            self.gateway_channel: None | trio.MemorySendChannel = None
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

    def event(self, func: Callable):
        # decorator for responding to events
        # function name must correspond to event name
        self.event_listeners[func.__name__] = func
        return func

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
                log.info(f"Started task {task.__name__}.")

    async def interaction_response(
        self, interaction: SlashCommand, message: str, ephemeral: bool = False
    ):
        flags = 64 if ephemeral else 0
        payload = {"type": 4, "data": {"content": message, "flags": flags}}
        r = HTTPRequest()
        await r.interaction_response(interaction.id, interaction.token, payload)

    async def edit_interaction_response(self, interaction: SlashCommand, message: str):
        payload = {"content": message}
        r = HTTPRequest()
        await r.edit_interaction_response(interaction.token, payload)

    async def edit_interaction_response_with_file(
        self, interaction: SlashCommand, filename: str, message: str
    ):
        pj = {"content": message}
        pj2 = {"payload_json": json.dumps(pj)}
        file = {"file": (filename, open(filename, "rb"))}
        r = HTTPRequest()
        await r.edit_interaction_response_with_file(interaction.token, pj2, file)

    async def send_message(self, channel: Optional[str], message: str):
        if not channel:
            log.debug("Tried to send a message, but had no channel.")
            return
        payload = {"content": message}
        r = HTTPRequest()
        await r.create_message(channel, payload)

    async def send_file(
        self, channel: Optional[str], filename: str, message: None | str = None
    ):
        if not channel:
            log.debug("Tried to send a message, but had no channel.")
            return
        pj = {"content": message}
        pj2 = {"payload_json": json.dumps(pj)}
        file = {"file": (filename, open(filename, "rb"))}
        r = HTTPRequest()
        await r.create_message_with_file(channel, pj2, file)

    async def update_role(self, guild_id, role_id: str, color: int):
        payload = {"color": color}
        r = HTTPRequest()
        await r.modify_guild_role(guild_id, role_id, payload)

    async def send_gateway_message(self, message: dict[str, Any]):
        if not self.gateway_channel:
            return
        await self.gateway_channel.send(message)

    async def update_presence(
        self, color: str, activity: None | int = None, message: None | str = None
    ):
        payload = {}
        payload["op"] = Opcode.PRESENCE_UPDATE
        payload["d"] = {}
        payload["d"]["since"] = None
        payload["d"]["status"] = color
        payload["d"]["afk"] = True if color == DotColor.ORANGE else False
        if activity:
            payload["d"]["activities"] = [{}]
            payload["d"]["activities"][0]["name"] = message
            payload["d"]["activities"][0]["type"] = activity

        if self.gateway_channel:
            await self.gateway_channel.send(payload)
