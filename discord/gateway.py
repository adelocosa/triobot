from __future__ import annotations

import json
import random
import zlib
from enum import IntEnum
from pprint import pprint
from typing import TYPE_CHECKING, Any

import trio
from trio_websocket import (
    WebSocketConnection,
    open_websocket_url,
    ConnectionClosed,
    HandshakeError,
)

if TYPE_CHECKING:
    from .client import Client


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


class GatewayConnection:
    def __init__(self, client: Client, bot_token: str):
        self.client = client
        self.token = bot_token
        self.zlib = zlib.decompressobj()
        self.buffer = bytearray()

    def build_heartbeat(self) -> dict[str, Any]:
        message = {"op": 1, "d": self.client.sequence}
        return message

    async def connect(self) -> bool:
        try:
            async with open_websocket_url(
                "wss://gateway.discord.gg/?v=9&encoding=json&compress=zlib-stream",
                connect_timeout=5,
                disconnect_timeout=5,
            ) as ws:
                self.ws: WebSocketConnection = ws
                try:
                    async with trio.open_nursery() as nursery:
                        # memory channel to initialize heartbeat function with correct interval
                        (
                            send_hb_interval,
                            receive_hb_interval,
                        ) = trio.open_memory_channel(0)

                        # memory channel to communicate messages to be sent to the gateway
                        send_gateway_message, send_queue = trio.open_memory_channel(5)
                        nursery.start_soon(
                            self.receiver,
                            send_hb_interval,
                            send_gateway_message.clone(),
                        )
                        nursery.start_soon(self.sender, send_queue)
                        nursery.start_soon(
                            self.heartbeat, receive_hb_interval, send_gateway_message
                        )
                except ConnectionClosed as cc:
                    reason = (
                        "<no reason>"
                        if cc.reason.reason is None
                        else f'"{cc.reason.reason}"'
                    )
                    pprint(f"Closed: {cc.reason.code}/{cc.reason.name} {reason}")
                    return False

        except HandshakeError as e:
            pprint(f"Connection attempt failed: {e}")
            return False

        return False

    async def receiver(
        self,
        send_hb_interval: trio.MemorySendChannel,
        send_gateway_message: trio.MemorySendChannel,
    ):
        def build_identify() -> dict[str, Any]:
            message = {
                "op": 2,
                "d": {
                    "token": self.client.TOKEN,
                    "intents": 32767,
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
            decompressed = decompress(raw)
            data: dict[str, Any] = json.loads(decompressed)
            pprint(data)
            opcode: int = data["op"]
            sequence: None | int = data.get("s", None)
            event: None | str = data.get("t", None)
            data: dict[str, Any] = data.get("d", {})
            if sequence:
                self.client.sequence = sequence

            if opcode == Opcode.INVALID_SESSION:
                # if d = True, resume | if d = False, identify
                if not data["d"]:
                    self.client.sequence = None
                    self.client.session_id = None
                await self.ws.aclose(reason="Received opcode 9: INVALID_SESSION")

            elif opcode == Opcode.RECONNECT:
                await self.ws.aclose(reason="Received opcode 7: RECONNECT")

            elif opcode == Opcode.HEARTBEAT:
                await send_gateway_message.send(self.build_heartbeat())

            elif opcode == Opcode.HELLO:
                interval = data["heartbeat_interval"]
                async with send_hb_interval:
                    await send_hb_interval.send(interval)
                if self.client.session_id and self.client.sequence:
                    await send_gateway_message.send(build_resume())
                else:
                    await send_gateway_message.send(build_identify())

            elif opcode == Opcode.HEARTBEAT_ACK:
                pass

            elif opcode == Opcode.DISPATCH:
                if event == "READY":
                    self.client.session_id = data["session_id"]

    async def sender(self, send_queue: trio.MemoryReceiveChannel):
        # handles sending all messages to the gateway
        # messages should be dicts, json encoding happens here
        while True:
            async with send_queue:
                async for message in send_queue:
                    pprint(message)
                    payload = json.dumps(message)
                    await self.ws.send_message(payload)

    async def heartbeat(
        self,
        receive_hb_interval: trio.MemoryReceiveChannel,
        send_gateway_message: trio.MemorySendChannel,
    ):
        # sends regular heartbeats according to heartbeat interval received in HELLO
        # todo: close connection if heartbeat_ack isn't received
        async with receive_hb_interval:
            interval = await receive_hb_interval.receive() / 1000
        await trio.sleep(interval * random.random())
        await send_gateway_message.send(self.build_heartbeat())
        while True:
            await trio.sleep(interval)
            await send_gateway_message.send(self.build_heartbeat())
