import logging
import logging.handlers
import os
import trio
import sqlite3

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

TOKEN = os.environ.get("BOT_TOKEN")
assert isinstance(TOKEN, str)
log.info("Token found. Initializing bot...")
bot = discord.Client(TOKEN)


# to implement for feature parity: (* critical)
# * twitch api polling
# * gradient role
# - /live
# - mumbot status updating
# - discord stream status/notifications
# - ding
# - streampic
# - streamgif
# - /color random, role, specific


@bot.slash_command
async def echo(interaction: discord.SlashCommand):
    message = interaction.data["options"][0]["value"]
    await bot.interaction_response(interaction, message)
    return


@bot.slash_command
async def slap(interaction: discord.SlashCommand):
    slapper = str(interaction.member)
    target = str(
        interaction.guild.members[list(interaction.data["resolved"]["users"])[0]]
    )
    message = f"*{slapper} slaps {target} around a bit with a large trout*"
    await bot.interaction_response(interaction, message)
    return


@bot.slash_command
async def stream(interaction: discord.SlashCommand):
    ephemeral = True
    userid = interaction.member.user.id
    subcommand = interaction.data["options"][0]["name"]
    user_streams = utils.get_streams_by_userid(con, userid)
    if subcommand == "list":
        x = 1
        message = "linked streams:"
        for entry in user_streams:
            message += f"\n{x}. {entry}"
            x += 1
        await bot.interaction_response(interaction, message, ephemeral)
        return

    url = interaction.data["options"][0]["options"][0]["value"]
    new_stream = utils.Stream(url)

    if subcommand == "link":
        utils.insert_user(con, userid)
        if not new_stream.valid:
            message = "couldn't validate stream"
            await bot.interaction_response(interaction, message, ephemeral)
            return
        if new_stream in user_streams:
            message = "stream already exists!"
            await bot.interaction_response(interaction, message, ephemeral)
            return
        utils.insert_stream(con, userid, new_stream)
        await bot.interaction_response(interaction, f"linked {new_stream}", ephemeral)
        return

    if subcommand == "unlink":
        if new_stream not in user_streams:
            message = "stream not found"
            await bot.interaction_response(interaction, message, ephemeral)
            return
        utils.delete_stream(con, new_stream)
        await bot.interaction_response(interaction, f"unlinked {new_stream}", ephemeral)
        return


@bot.task
async def test_task():
    while True:
        await bot.send_message("723649270296739882", "hello!")
        await trio.sleep(3600)


# @bot.task
# async def test_task2():
#     while True:
#         await bot.send_message("723649270296739882", "hi!")
#         await trio.sleep(5)


def initialize_database() -> sqlite3.Connection:
    create_users_table_query = """
    CREATE TABLE IF NOT EXISTS Users (
        UserID TEXT PRIMARY KEY
    )
    """
    create_userstreams_table_query = """
    CREATE TABLE IF NOT EXISTS UserStreams (
    StreamID INTEGER PRIMARY KEY,
    UserID TEXT,
    Stream STREAM,
    FOREIGN KEY(UserID) REFERENCES Users(UserID)
    )
    """
    sqlite3.register_adapter(utils.Stream, utils.adapt_stream)
    sqlite3.register_converter("STREAM", utils.convert_stream)
    con = sqlite3.connect("mumbot.db", detect_types=sqlite3.PARSE_DECLTYPES)
    con.execute(create_users_table_query)
    con.execute(create_userstreams_table_query)
    return con


try:
    con = initialize_database()
    bot.connect()
except KeyboardInterrupt:
    log.info("Program halted due to keyboard interrupt.")
except Exception as e:
    log.exception("Program halted due to unhandled exception:")
