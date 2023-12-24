from __future__ import annotations

import json
import logging
import random
import zlib
from enum import IntEnum, StrEnum
from typing import TYPE_CHECKING, Any

import trio
from trio_websocket import (
    ConnectionClosed,
    HandshakeError,
    WebSocketConnection,
    open_websocket_url,
)

from .event import Event

if TYPE_CHECKING:
    from .client import Client

log = logging.getLogger(__name__)


class Opcode(IntEnum):
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


class DotColor(StrEnum):
    RED = "dnd"
    GREEN = "online"
    ORANGE = "idle"
    GRAY = "invisible"


class ActivityType(IntEnum):
    PLAYING = 0
    STREAMING = 1
    LISTENING = 2
    WATCHING = 3
    CUSTOM = 4
    COMPETING = 5


class GatewayConnection:
    def __init__(self, client: Client, bot_token: str, url: str):
        self.client = client
        self.url = url
        self.token = bot_token
        self.zlib = zlib.decompressobj()
        self.buffer = bytearray()

    def build_heartbeat(self) -> dict[str, Any]:
        message = {"op": 1, "d": self.client.sequence}
        return message

    async def connect(self) -> None:
        try:
            async with open_websocket_url(
                f"{self.url}/?v=10&encoding=json&compress=zlib-stream",
                connect_timeout=5,
                disconnect_timeout=5,
            ) as ws:
                self.ws: WebSocketConnection = ws
                await self.client.on_connected()
                try:
                    async with trio.open_nursery() as nursery:
                        # memory channel to initialize heartbeat function with correct interval
                        send_hb_info, receive_hb_info = trio.open_memory_channel(0)

                        # memory channel to communicate messages to be sent to the gateway
                        send_gateway_message, send_queue = trio.open_memory_channel(5)
                        nursery.start_soon(
                            self.receiver,
                            send_hb_info,
                            send_gateway_message.clone(),
                        )
                        nursery.start_soon(self.sender, send_queue)
                        nursery.start_soon(
                            self.heartbeat, receive_hb_info, send_gateway_message
                        )
                        nursery.start_soon(self.client.background_tasks)
                        self.client.gateway_channel = send_gateway_message.clone()

                except ConnectionClosed as cc:
                    reason = (
                        "No reason."
                        if cc.reason.reason is None
                        else f'"{cc.reason.reason}"'
                    )
                    log.warning(
                        f"Connection closed: {cc.reason.code}/{cc.reason.name} - {reason}"
                    )
                    return

        except HandshakeError as e:
            log.warning(f"Connection attempt failed.")
            return

        return

    async def receiver(
        self,
        send_hb_info: trio.MemorySendChannel,
        send_gateway_message: trio.MemorySendChannel,
    ):
        def build_identify() -> dict[str, Any]:
            message = {
                "op": 2,
                "d": {
                    "token": self.client.TOKEN,
                    "intents": 131071,
                    "properties": {
                        "$os": "windows",
                        "$browser": "mumbotv2",
                        "$device": "mumbotv2",
                    },
                },
            }
            return message

        def build_resume() -> dict[str, Any]:
            message = {
                "op": 6,
                "d": {
                    "token": self.client.TOKEN,
                    "session_id": self.client.session_id,
                    "seq": self.client.sequence,
                },
            }
            return message

        def decompress(raw) -> str:
            # detects and decompresses zlib-compressed data
            self.buffer.extend(raw)
            if len(raw) < 4 or raw[-4:] != b"\x00\x00\xff\xff":
                return raw
            raw = self.zlib.decompress(self.buffer)
            self.buffer = bytearray()
            return raw.decode("utf-8")

        # main receiving loop
        while True:
            raw = await self.ws.get_message()
            decompressed = json.loads(decompress(raw))
            opcode: int = decompressed["op"]
            sequence: None | int = decompressed["s"]
            event_name: None | str = decompressed["t"]
            data: dict[str, Any] = decompressed.get("d", {})
            if opcode != Opcode.DISPATCH:
                log.info(f"Received opcode {opcode} ({Opcode(opcode).name}).")
                log.debug(json.dumps(decompressed, indent=4))
            if sequence:
                self.client.sequence = sequence

            if opcode == Opcode.INVALID_SESSION:
                # if d = True, resume | if d = False, identify
                if not data:
                    self.client.clear_state()
                await self.ws.aclose(reason="Received opcode 9 (INVALID_SESSION).")

            elif opcode == Opcode.RECONNECT:
                await self.ws.aclose(code=2000, reason="Received opcode 7 (RECONNECT).")

            elif opcode == Opcode.HEARTBEAT:
                await send_gateway_message.send(self.build_heartbeat())

            elif opcode == Opcode.HELLO:
                interval = data["heartbeat_interval"]
                async with send_hb_info:
                    await send_hb_info.send(interval)
                if self.client.session_id and self.client.sequence:
                    await send_gateway_message.send(build_resume())
                else:
                    await send_gateway_message.send(build_identify())

            elif opcode == Opcode.HEARTBEAT_ACK:
                pass

            elif opcode == Opcode.DISPATCH:
                assert isinstance(event_name, str)
                event = Event(self.client, event_name, data)
                await event.process()

    async def sender(self, send_queue: trio.MemoryReceiveChannel):
        # handles sending all messages to the gateway
        # messages should be dicts, json encoding happens here
        while True:
            async with send_queue:
                async for message in send_queue:
                    log.info(
                        f"Sending opcode {message['op']} ({Opcode(message['op']).name})."
                    )
                    log.debug(json.dumps(message, indent=4))
                    payload = json.dumps(message)
                    await self.ws.send_message(payload)

    async def heartbeat(
        self,
        receive_hb_info: trio.MemoryReceiveChannel,
        send_gateway_message: trio.MemorySendChannel,
    ):
        # sends regular heartbeats according to heartbeat interval received in HELLO
        # todo: close connection if heartbeat_ack isn't received
        async with receive_hb_info:
            interval = await receive_hb_info.receive() / 1000
        await trio.sleep(interval * random.random())
        await send_gateway_message.send(self.build_heartbeat())
        while True:
            await trio.sleep(interval)
            await send_gateway_message.send(self.build_heartbeat())
