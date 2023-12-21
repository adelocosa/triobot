import inspect
import json
import logging
import os
from typing import Any, ClassVar, TypeAlias
from dotenv import load_dotenv
import httpx

Payload: TypeAlias = None | dict[str, Any]

log = logging.getLogger(__name__)


class HTTPRequest:
    load_dotenv("./appdata/.env", override=True)
    TOKEN = os.environ.get("BOT_TOKEN")
    APP_ID = os.environ.get("APP_ID")
    API_URL: ClassVar[str] = "https://discord.com/api/v10"

    def __init__(self, headers: None | dict[str, str] = None):
        self.response: None | httpx.Response = None
        self.headers = headers
        if not headers:
            self.headers = {
                "Authorization": f"Bot {self.TOKEN}",
                "User-Agent": "mumbot (http://mumblecrew.com, 2.0)",
            }

    async def send(
        self,
        method: str,
        route: str,
        payload: Payload = None,
        file=None,
    ) -> httpx.Response:
        # get correct args for request based on method
        payload_format = {
            "GET": {"params": payload},
            "POST": {"json": payload},
            "PATCH": {"json": payload},
            "PUT": {"json": payload},
            "DELETE": {},
        }
        url = self.API_URL + route

        async with httpx.AsyncClient(headers=self.headers) as http_client:
            log.info(f"Sending HTTP {inspect.stack()[1][3]} request.")
            log.debug(json.dumps(payload, indent=4))
            log.debug(self.headers)
            if not file:
                self.response = await http_client.request(
                    method, url, **payload_format[method]
                )
            else:
                self.response = await http_client.request(
                    method, url, data=payload, files=file
                )
            log.info(f"Request returned status {self.response.status_code}.")
            log.debug(json.dumps(dict(self.response.headers), indent=4))
            if self.response.status_code != 204:
                log.debug(json.dumps(self.response.json(), indent=4))
        return self.response

    # application commands

    async def create_guild_application_command(
        self, guild_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/applications/{self.APP_ID}/guilds/{guild_id}/commands"
        method = "POST"
        return await self.send(method, route, payload)

    async def delete_guild_application_command(
        self, guild_id: str, command_id: str
    ) -> httpx.Response:
        route = f"/applications/{self.APP_ID}/guilds/{guild_id}/commands/{command_id}"
        method = "DELETE"
        return await self.send(method, route)

    async def get_guild_application_commands(self, guild_id: str) -> httpx.Response:
        route = f"/applications/{self.APP_ID}/guilds/{guild_id}/commands"
        method = "GET"
        return await self.send(method, route)

    async def set_guild_application_command_permissions(
        self, guild_id: str, command_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/applications/{self.APP_ID}/guilds/{guild_id}/commands/{command_id}/permissions"
        method = "PUT"
        return await self.send(method, route, payload)

    async def interaction_response(
        self, interaction_id: str, interaction_token: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/interactions/{interaction_id}/{interaction_token}/callback"
        method = "POST"
        return await self.send(method, route, payload)

    async def edit_interaction_response(
        self, interaction_token: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/webhooks/{self.APP_ID}/{interaction_token}/messages/@original"
        method = "PATCH"
        return await self.send(method, route, payload)

    async def edit_interaction_response_with_file(
        self, interaction_token: str, payload: Payload, file
    ) -> httpx.Response:
        route = f"/webhooks/{self.APP_ID}/{interaction_token}/messages/@original"
        method = "PATCH"
        return await self.send(method, route, payload, file)

    # channel requests

    async def create_reaction(
        self, channel_id: str, message_id: str, emoji: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
        method = "PUT"
        return await self.send(method, route, payload)

    async def get_channel(
        self, channel_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/channels/{channel_id}"
        method = "GET"
        return await self.send(method, route, payload)

    async def create_message(
        self, channel_id: str, payload: dict[str, Any]
    ) -> httpx.Response:
        route = f"/channels/{channel_id}/messages"
        method = "POST"
        return await self.send(method, route, payload)

    async def create_message_with_file(
        self, channel_id: str, payload: dict[str, Any], file
    ) -> httpx.Response:
        route = f"/channels/{channel_id}/messages"
        method = "POST"
        return await self.send(method, route, payload, file)

    async def edit_message(
        self, channel_id: str, message_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/channels/{channel_id}/messages/{message_id}"
        method = "PATCH"
        return await self.send(method, route, payload)

    async def delete_message(
        self, channel_id: str, message_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/channels/{channel_id}/messages/{message_id}"
        method = "DELETE"
        return await self.send(method, route, payload)

    async def delete_channel(
        self, channel_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/channels/{channel_id}"
        method = "DELETE"
        return await self.send(method, route, payload)

    # emoji requests

    async def list_guild_emojis(
        self, guild_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/guilds/{guild_id}/emojis"
        method = "GET"
        response = await self.send(method, route, payload)
        return response

    # guild requests

    async def get_guild(self, guild_id: str, payload: Payload = None) -> httpx.Response:
        route = f"/guilds/{guild_id}"
        method = "GET"
        return await self.send(method, route, payload)

    async def get_guild_member(self, guild_id: str, user_id: str) -> httpx.Response:
        route = f"/guilds/{guild_id}/members/{user_id}"
        method = "GET"
        return await self.send(method, route)

    async def list_guild_members(
        self, guild_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/guilds/{guild_id}/members"
        method = "GET"
        return await self.send(method, route, payload)

    async def add_guild_member_role(
        self, guild_id: str, user_id: str, role_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
        method = "PUT"
        return await self.send(method, route, payload)

    async def get_guild_roles(
        self, guild_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/guilds/{guild_id}/roles"
        method = "GET"
        return await self.send(method, route, payload)

    async def get_guild_audit_log(
        self, guild_id: str, payload: Payload = None
    ) -> httpx.Response:
        route = f"/guilds/{guild_id}/audit-logs"
        method = "GET"
        return await self.send(method, route, payload)

    async def modify_guild_member(
        self, guild_id: str, user_id: str, payload: Payload = None
    ) -> httpx.Response:
        """params: nick (str), roles (list), mute (bool), deaf (bool), channel_id (str)"""
        route = f"/guilds/{guild_id}/members/{user_id}"
        method = "PATCH"
        return await self.send(method, route, payload)

    async def modify_guild_role(
        self, guild_id: str, role_id: str, payload: Payload = None
    ) -> httpx.Response:
        """params: name (str), permissions (int), color (int), hoist (bool), mentionable (bool)"""
        route = f"/guilds/{guild_id}/roles/{role_id}"
        method = "PATCH"
        return await self.send(method, route, payload)

    # user requests

    async def get_user(self, user_id: str, payload: Payload = None) -> httpx.Response:
        route = f"/users/{user_id}"
        method = "GET"
        return await self.send(method, route, payload)
