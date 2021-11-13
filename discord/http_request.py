import httpx
import pprint
import os
from typing import Any, TypeAlias, ClassVar
from dotenv import load_dotenv

Payload: TypeAlias = None | dict[str, Any]


class HTTPRequest:

    API_URL: ClassVar[str] = "https://discordapp.com/api/v9"

    def __init__(self):
        self.response: None | httpx.Response = None

    async def send(self, method: str, route: str, payload: Payload = None) -> httpx.Response:
        payload_format = {
            "GET": {"params": payload},
            "POST": {"json": payload},
            "PATCH": {"json": payload},
            "PUT": {"json": payload},
            "DELETE": {},
        }
        url = self.API_URL + route
        load_dotenv()
        bot_token = os.environ.get("BOT_TOKEN")
        headers = {
            "Authorization": f"Bot {bot_token}",
            "User-Agent": "mumbot (http://mumblecrew.com, 1.0)",
        }

        async with httpx.AsyncClient() as http_client:
            self.response = await http_client.request(method, url, **payload_format[method])
        return self.response

    def print_response(self) -> None:
        if self.response:
            print(f"status code: {self.response.status_code}")
            print("response:")
            pprint.pprint(self.response.json())

    def print_headers(self) -> None:
        if self.response:
            print(f"status code: {self.response.status_code}")
            pprint.pprint(dict(self.response.headers))

    # channel requests

    async def create_reaction(
        self, channel_id: int, message_id: int, emoji: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
        method = "PUT"
        return await self.send(method, route, payload)

    async def get_channel(self, channel_id: int, payload: Payload = None) -> httpx.Response:
        route = f"/channels/{channel_id}"
        method = "GET"
        return await self.send(method, route, payload)

    async def create_message(
        self, channel_id: int, payload: dict[str, Any]
    ) -> httpx.Response:
        route = f"/channels/{channel_id}/messages"
        method = "POST"
        return await self.send(method, route, payload)

    async def edit_message(
        self, channel_id: int, message_id: int, payload: Payload = None
    ) -> httpx.Response:
        route = f"/channels/{channel_id}/messages/{message_id}"
        method = "PATCH"
        return await self.send(method, route, payload)

    async def delete_message(
        self, channel_id: int, message_id: int, payload: Payload = None
    ) -> httpx.Response:
        route = f"/channels/{channel_id}/messages/{message_id}"
        method = "DELETE"
        return await self.send(method, route, payload)

    async def delete_channel(
        self, channel_id: int, payload: Payload = None
    ) -> httpx.Response:
        route = f"/channels/{channel_id}"
        method = "DELETE"
        return await self.send(method, route, payload)

    # emoji requests

    async def list_guild_emojis(
        self, guild_id: int, payload: Payload = None
    ) -> httpx.Response:
        route = f"/guilds/{guild_id}/emojis"
        method = "GET"
        response = await self.send(method, route, payload)
        return response

    # guild requests

    async def get_guild(self, guild_id: int, payload: Payload = None) -> httpx.Response:
        route = f"/guilds/{guild_id}"
        method = "GET"
        return await self.send(method, route, payload)

    async def list_guild_members(
        self, guild_id: int, payload: Payload = None
    ) -> httpx.Response:
        route = f"/guilds/{guild_id}/members"
        method = "GET"
        return await self.send(method, route, payload)

    async def add_guild_member_role(
        self, guild_id: int, user_id: int, role_id: int, payload: Payload = None
    ) -> httpx.Response:
        route = f"/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
        method = "PUT"
        return await self.send(method, route, payload)

    async def get_guild_roles(self, guild_id: int, payload: Payload = None) -> httpx.Response:
        route = f"/guilds/{guild_id}/roles"
        method = "GET"
        return await self.send(method, route, payload)

    async def get_guild_audit_log(
        self, guild_id: int, payload: Payload = None
    ) -> httpx.Response:
        route = f"/guilds/{guild_id}/audit-logs"
        method = "GET"
        return await self.send(method, route, payload)

    async def modify_guild_member(
        self, guild_id: int, user_id: int, payload: Payload = None
    ) -> httpx.Response:
        """params: nick (str), roles (list), mute (bool), deaf (bool), channel_id (int)"""
        route = f"/guilds/{guild_id}/members/{user_id}"
        method = "PATCH"
        return await self.send(method, route, payload)

    async def modify_guild_role(
        self, guild_id: int, role_id: int, payload: Payload = None
    ) -> httpx.Response:
        """params: name (str), permissions (int), color (int), hoist (bool), mentionable (bool)"""
        route = f"/guilds/{guild_id}/roles/{role_id}"
        method = "PATCH"
        return await self.send(method, route, payload)

    # user requests

    async def get_user(self, user_id: int, payload: Payload = None) -> httpx.Response:
        route = f"/users/{user_id}"
        method = "GET"
        return await self.send(method, route, payload)
