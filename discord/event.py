from __future__ import annotations

import json
import logging
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any

from .channel import Channel
from .guild import Guild
from .interaction import Interaction
from .member import GuildMember
from .user import User

if TYPE_CHECKING:
    from .client import Client

log = logging.getLogger(__name__)


class Event:
    # todo: possibly make queue of events to process if they arrive prior to GUILD_CREATE

    def __init__(self, client: Client, name: str, data: dict[str, Any]):
        self.client = client
        self.name = name
        self.data = data
        log.info(f"Received {self.name} dispatch.")
        log.debug(json.dumps(data, indent=4))

    async def process(self):
        try:
            handler = getattr(self, f"handle_{self.name.lower()}")
        except AttributeError:
            log.debug(f"Ignored {self.name} dispatch.")
        else:
            if iscoroutinefunction(handler):
                await handler()
            else:
                handler()
            if self.name.lower() in self.client.event_listeners.keys():
                await self.client.event_listeners[self.name.lower()](self.data)
                log.debug(f"Triggered {self.name} event.")
            log.debug(f"Finished processing {self.name} dispatch.")

    def handle_ready(self):
        self.client.session_id = self.data["session_id"]
        self.client.user = User(self.data["user"])
        self.client.users[self.client.user.id] = self.client.user

    def handle_channel_create(self):
        guild = self.client.guilds[self.data["guild_id"]]
        channel = Channel(guild, self.data)
        guild.channels[channel.id] = channel

    def handle_channel_update(self):
        guild = self.client.guilds[self.data["guild_id"]]
        channel = guild.channels[self.data["id"]]
        channel.update(self.data)

    def handle_channel_delete(self):
        guild = self.client.guilds[self.data["guild_id"]]
        channel = guild.channels[self.data["id"]]
        del guild.channels[channel.id]
        log.debug(
            f"Removed channel {channel.id} ({channel.name} from guild {guild.id} ({guild.name})."
        )

    def handle_guild_create(self):
        guild = Guild(self.client, self.data)
        self.client.guilds[guild.id] = guild

    def handle_guild_update(self):
        guild = self.client.guilds[self.data["id"]]
        guild.update(self.data)

    def handle_guild_delete(self):
        guild = self.client.guilds[self.data["id"]]
        del self.client.guilds[guild.id]
        log.debug(f"Removed guild {guild.id} ({guild.name}).")

    def handle_guild_emojis_update(self):
        guild = self.client.guilds[self.data["guild_id"]]
        guild.emojis = guild.parse_emojis(self.data["emojis"])

    def handle_guild_member_add(self):
        guild = self.client.guilds[self.data["guild_id"]]
        member = GuildMember(guild, self.data)
        guild.members[member.user.id] = member

    def handle_guild_member_remove(self):
        guild = self.client.guilds[self.data["guild_id"]]
        member = guild.members[self.data["user"]["id"]]
        del guild.members[self.data["user"]["id"]]
        log.debug(
            f"Removed member {member.user.id} ({str(member)}) from guild {guild.id} ({guild.name})."
        )

    def handle_guild_member_update(self):
        # sometimes comes before GUILD_CREATE on connect
        try:
            guild = self.client.guilds[self.data["guild_id"]]
        except KeyError:
            log.debug(f"Ignored {self.name} dispatch.")
        else:
            member = guild.members[self.data["user"]["id"]]
            member.update(self.data)

    def handle_guild_role_update(self):
        guild = self.client.guilds[self.data["guild_id"]]
        role = guild.roles[self.data["role"]["id"]]
        role.update(self.data["role"])

    def handle_presence_update(self):
        user = self.client.users[self.data["user"]["id"]]
        user.update_activities(self.data["activities"])

    def handle_user_update(self):
        user = self.client.users[self.data["user"]["id"]]
        user.update(self.data)

    def handle_voice_state_update(self):
        guild = self.client.guilds[self.data["guild_id"]]
        guild.parse_voice_states([self.data])

    async def handle_interaction_create(self):
        guild = self.client.guilds[self.data["guild_id"]]
        interaction = Interaction(guild, self.data)
        try:
            await self.client.interaction_listeners[interaction.name](interaction)
        except KeyError:
            log.debug(f"Received unknown slash command '{interaction.name}'")
