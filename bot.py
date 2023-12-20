import logging
import logging.handlers
import os
import trio
import sqlite3
from collections import defaultdict
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()

import discord
import utils

log_format = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
console_log = logging.StreamHandler()
console_log.setLevel(logging.INFO)
console_log.setFormatter(log_format)
file_log = logging.handlers.RotatingFileHandler(
    "debug.log", maxBytes=10000000, backupCount=5, encoding="utf8"
)
file_log.setLevel(logging.DEBUG)
file_log.setFormatter(log_format)
log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(console_log)
log.addHandler(file_log)


class Mumbot(discord.Client):
    def __init__(self):
        BOT_TOKEN = os.environ.get("BOT_TOKEN")
        assert isinstance(BOT_TOKEN, str)
        TWITCH_TOKEN = utils.get_twitch_bearer_token()
        assert isinstance(TWITCH_TOKEN, str)
        os.environ["TWITCH_TOKEN"] = TWITCH_TOKEN
        log.info("Token found. Initializing bot...")
        super().__init__(BOT_TOKEN)

        self.con = self.initialize_database()
        self.user_streams: dict[str, list[utils.Stream]] = defaultdict(list)
        streams = utils.get_all_streams(self.con)
        for stream in streams:
            self.user_streams[stream[0]].append(stream[1])

    def initialize_database(self) -> sqlite3.Connection:
        sqlite3.register_adapter(utils.Stream, utils.adapt_stream)
        sqlite3.register_converter("STREAM", utils.convert_stream)
        con = sqlite3.connect("mumbot.db", detect_types=sqlite3.PARSE_DECLTYPES)
        log.info("Connected to sqlite database.")
        utils.create_users_table(con)
        utils.create_userstreams_table(con)
        utils.create_guilds_table(con)
        return con

    def get_guild_streams(self, guild_id: str) -> list[utils.Stream]:
        streams = []
        for user in self.user_streams.keys():
            if user in self.guilds[guild_id].members.keys():
                streams.extend(bot.user_streams[user])
        return streams

    def get_user_from_stream(self, stream: utils.Stream) -> None | discord.User:
        for user_id, streams in self.user_streams.items():
            if stream in streams:
                return bot.users[user_id]

    def get_playing_game(self, user: discord.User) -> str:
        for activity in user.activities:
            if activity.type == discord.ActivityType.PLAYING:
                return activity.name
        return ""

    def generate_presence_args(self) -> tuple[str, int, str]:
        live = 0
        for guild in bot.guilds.values():
            for member in guild.members.values():
                if member.is_live:
                    live += 1
        for streams in bot.user_streams.values():
            for stream in streams:
                if stream.is_live:
                    live += 1
        color = discord.gateway.DotColor.GREEN
        if live == 0:
            color = discord.gateway.DotColor.RED
            message = "nothing :("
        elif live == 1:
            message = "1 live stream"
        else:
            message = f"{live} live streams!"
        return color, discord.gateway.ActivityType.WATCHING, message


bot = Mumbot()

# to implement for feature parity: (* critical)
# * gradient role
# - mumbot status updating
# - ding
# - streampic
# - streamgif
# - /color random, role, specific


@bot.event
async def voice_state_update(data: dict[str, Any]):
    guild_id = data["guild_id"]
    member = bot.guilds[guild_id].members[data["user_id"]]
    if member.is_live and not member.was_live:
        assert member.voice_state
        assert member.voice_state.channel
        game = bot.get_playing_game(member.user)
        add = f", playing **{game}**" if game else ""
        message = f"**{member}** just went live{add}! \
                \n`🔊 {member.voice_state.channel.name}`"
        await bot.update_presence(*bot.generate_presence_args())
        await bot.send_message(utils.get_announce_channel(bot.con, guild_id), message)
    elif member.was_live and not member.is_live:
        await bot.update_presence(*bot.generate_presence_args())
        member.was_live = False
    return


@bot.slash_command
async def setchannel(interaction: discord.SlashCommand):
    guild_id = interaction.guild.id
    channel_id = interaction.data["options"][0]["value"]
    utils.insert_guild(bot.con, guild_id, channel_id)
    return


@bot.slash_command
async def live(interaction: discord.SlashCommand):
    message = "Currently live:"
    zero = True
    for member in interaction.guild.members.values():
        if member.is_live:
            zero = False
            assert member.voice_state
            assert member.voice_state.channel
            game = bot.get_playing_game(member.user)
            add = f" - playing **{game}**" if game else ""
            message += f"\n**{member}** - `🔊 {member.voice_state.channel.name}`{add}"
    streams = bot.get_guild_streams(interaction.guild.id)
    for stream in streams:
        if stream.is_live:
            zero = False
            user = bot.get_user_from_stream(stream)
            if not user:
                continue
            game = bot.get_playing_game(user)
            add = f" - playing **{game}**" if game else ""
            message += f"\n**{interaction.guild.members[user.id]}** - {stream}{add}"
    if zero:
        message = "No streams live."
    await bot.interaction_response(interaction, message)
    return


@bot.slash_command
async def stream(interaction: discord.SlashCommand):
    ephemeral = True
    userid = interaction.member.user.id
    subcommand = interaction.data["options"][0]["name"]

    if subcommand == "list":
        x = 1
        message = "linked streams:"
        for entry in bot.user_streams[userid]:
            message += f"\n{x}. {entry}"
            x += 1
        await bot.interaction_response(interaction, message, ephemeral)
        return

    url = interaction.data["options"][0]["options"][0]["value"]

    if subcommand == "link":
        new_stream = utils.Stream(url=url)
        if not await new_stream.validate():
            message = "couldn't validate stream"
            await bot.interaction_response(interaction, message, ephemeral)
            return
        utils.insert_user(bot.con, userid)
        if new_stream in bot.user_streams[userid]:
            message = "stream already exists!"
            await bot.interaction_response(interaction, message, ephemeral)
            return
        utils.insert_stream(bot.con, userid, new_stream)
        bot.user_streams[userid].append(new_stream)
        await bot.interaction_response(interaction, f"linked {new_stream}", ephemeral)
        return

    if subcommand == "unlink":
        new_stream = utils.Stream(url=url)
        for linked_stream in bot.user_streams[userid]:
            if linked_stream == new_stream:
                utils.delete_stream(bot.con, linked_stream)
                bot.user_streams[userid].remove(new_stream)
                message = f"unlinked {new_stream}"
                await bot.interaction_response(interaction, message, ephemeral)
                return
        message = "stream not found"
        await bot.interaction_response(interaction, message, ephemeral)
        return


@bot.task
async def twitch_polling():
    while True:
        await trio.sleep(5)
        for guild in bot.guilds.values():
            streams = bot.get_guild_streams(guild.id)
            usernames = [stream.username for stream in streams]
            live = await utils.get_live_streams_by_usernames(usernames)
            for stream in streams:
                if stream.username not in live:
                    stream.is_live = False
                    if stream.was_live:
                        await bot.update_presence(*bot.generate_presence_args())
                        stream.was_live = False
                    continue
                stream.is_live = True
                if not stream.was_live:
                    user = bot.get_user_from_stream(stream)
                    if not user:
                        continue
                    member = guild.members[user.id]
                    game = bot.get_playing_game(member.user)
                    add = f", playing **{game}**" if game else ""
                    message = f"**{member}** just went live{add}!\n{stream}"
                    await bot.update_presence(*bot.generate_presence_args())
                    await bot.send_message(
                        utils.get_announce_channel(bot.con, guild.id), message
                    )
                stream.was_live = True


if __name__ == "__main__":
    try:
        bot.connect()
    except KeyboardInterrupt:
        log.info("Program halted due to keyboard interrupt.")
    except Exception as e:
        log.exception("Program halted due to unhandled exception:")
