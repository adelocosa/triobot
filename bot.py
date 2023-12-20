import logging
import logging.handlers
import os
import trio
import sqlite3
import random
import numpy
import cv2
from PIL import Image
from streamlink.session import Streamlink
from streamlink.options import Options
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor
from collections import defaultdict
from typing import Any
from dotenv import load_dotenv

import discord
import utils


def patch_asscalar(a):
    return a.item()


setattr(numpy, "asscalar", patch_asscalar)
if not os.path.exists("./appdata"):
    os.mkdir("./appdata")
log_format = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
console_log = logging.StreamHandler()
console_log.setLevel(logging.INFO)
console_log.setFormatter(log_format)
file_log = logging.handlers.RotatingFileHandler(
    "./appdata/debug.log", maxBytes=10000000, backupCount=5, encoding="utf8"
)
file_log.setLevel(logging.DEBUG)
file_log.setFormatter(log_format)
log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(console_log)
log.addHandler(file_log)


class Mumbot(discord.Client):
    def __init__(self):
        load_dotenv("./appdata/.env", override=True)
        BOT_TOKEN = os.environ.get("BOT_TOKEN")
        print(BOT_TOKEN)
        TWITCH_TOKEN = utils.get_twitch_bearer_token()
        assert isinstance(BOT_TOKEN, str)
        assert isinstance(TWITCH_TOKEN, str)
        os.environ["TWITCH_TOKEN"] = TWITCH_TOKEN
        log.info("Token found. Initializing bot...")
        super().__init__(BOT_TOKEN)

        self.con = self.initialize_database()
        self.user_streams: dict[str, list[utils.Stream]] = defaultdict(list)
        streams = utils.get_all_streams(self.con)
        for stream in streams:
            self.user_streams[stream[0]].append(stream[1])
        self.color_list: list[sRGBColor] = []

    def initialize_database(self) -> sqlite3.Connection:
        sqlite3.register_adapter(utils.Stream, utils.adapt_stream)
        sqlite3.register_converter("STREAM", utils.convert_stream)
        con = sqlite3.connect("appdata/mumbot.db", detect_types=sqlite3.PARSE_DECLTYPES)
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
        discord_streams: list[discord.GuildMember] = []
        linked_streams: list[utils.Stream] = []
        for guild in bot.guilds.values():
            for member in guild.members.values():
                if member.is_live:
                    discord_streams.append(member)
        for streams in bot.user_streams.values():
            for stream in streams:
                if stream.is_live:
                    linked_streams.append(stream)
        color = discord.gateway.DotColor.GREEN
        if len(linked_streams + discord_streams) == 0:
            color = discord.gateway.DotColor.RED
            message = "nothing :("
        elif len(linked_streams + discord_streams) == 1:
            if discord_streams:
                name = str(discord_streams[0])
            else:
                name = linked_streams[0].username
            message = f"{name} :)"
        else:
            message = f"{len(linked_streams + discord_streams)} live streams!"
        return color, discord.gateway.ActivityType.WATCHING, message


bot = Mumbot()

# to implement for feature parity: (* critical)
# - ding
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
    utils.insert_announce_channel(bot.con, guild_id, channel_id)
    await bot.interaction_response(interaction, "updated!", True)
    return


@bot.slash_command
async def rainbow(interaction: discord.SlashCommand):
    guild_id = interaction.guild.id
    role_id = interaction.data["options"][0]["value"]
    utils.insert_rainbow_role(bot.con, guild_id, role_id)
    await bot.interaction_response(interaction, "updated!", True)
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
async def link(interaction: discord.SlashCommand):
    ephemeral = True
    userid = interaction.member.user.id
    url = interaction.data["options"][0]["value"]
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


@bot.slash_command
async def unlink(interaction: discord.SlashCommand):
    ephemeral = True
    userid = interaction.member.user.id
    url = interaction.data["options"][0]["value"]
    new_stream = utils.Stream(url=url)
    for linked_stream in bot.user_streams[userid]:
        if linked_stream == new_stream:
            utils.delete_stream(bot.con, linked_stream)
            bot.user_streams[userid].remove(new_stream)
            message = f"unlinked {new_stream}"
            await bot.update_presence(*bot.generate_presence_args())
            await bot.interaction_response(interaction, message, ephemeral)
            return
    message = "stream not found"
    await bot.interaction_response(interaction, message, ephemeral)
    return


@bot.slash_command
async def mystreams(interaction: discord.SlashCommand):
    ephemeral = True
    userid = interaction.member.user.id
    x = 1
    message = "Linked streams:"
    for entry in bot.user_streams[userid]:
        message += f"\n{x}. {entry}"
        x += 1
    await bot.interaction_response(interaction, message, ephemeral)
    return


@bot.slash_command
async def streampic(interaction: discord.SlashCommand):
    streamname = interaction.data["options"][0]["value"]
    session = Streamlink()
    options = Options()
    load_dotenv("./appdata/.env", override=True)
    TURBO_OAUTH = os.environ.get("TURBO_OAUTH")
    options.set("api-header", [("Authorization", f"OAuth {TURBO_OAUTH}")])
    options.set("low-latency", True)
    message = f"Generating a streampic from *{streamname}*..."
    await bot.interaction_response(interaction, message)
    try:
        streams = session.streams(f"https://twitch.tv/{streamname}", options)
    except:
        await bot.edit_interaction_response(interaction, "Couldn't find stream.")
        return
    try:
        stream = streams["best"]
    except:
        await bot.edit_interaction_response(interaction, f"{streamname} is offline!")
        return
    try:
        with stream.open() as fd:
            await trio.sleep(1)
            data = fd.read(1000000)
    except:
        await bot.edit_interaction_response(interaction, "couldn't download stream")
        return

    fname = "./appdata/stream.bin"
    open(fname, "wb").write(data)
    try:
        capture = cv2.VideoCapture(fname)
        imgdata = capture.read()[1]
        imgdata = imgdata[..., ::-1]  # BGR -> RGB
        img = Image.fromarray(imgdata)
        img.save("./appdata/frame.jpg")
        message = (
            f"Please enjoy this {utils.get_adjective()} streampic from *{streamname}*."
        )
        await bot.edit_interaction_response_with_file(
            interaction, "./appdata/frame.jpg", message
        )
    except:
        await bot.edit_interaction_response(interaction, "couldn't generate image")


@bot.slash_command
async def sp(interaction: discord.SlashCommand):
    await streampic(interaction)


@bot.task
async def set_initial_presence():
    await trio.sleep(2)
    await bot.update_presence(*bot.generate_presence_args())


@bot.task
async def twitch_polling():
    first = True
    while True:
        await trio.sleep(5)
        for guild in bot.guilds.values():
            streams = bot.get_guild_streams(guild.id)
            usernames = [stream.username for stream in streams]
            live, success = await utils.get_live_streams_by_usernames(usernames)
            if not success:
                continue
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
                    if not first:
                        await bot.send_message(
                            utils.get_announce_channel(bot.con, guild.id), message
                        )
                stream.was_live = True
        first = False


@bot.task
async def rainbow_role():
    def generate_lab_gradient(
        color1: sRGBColor, color2: sRGBColor, steps
    ) -> list[sRGBColor]:
        c1: LabColor = convert_color(color1, LabColor)
        c2: LabColor = convert_color(color2, LabColor)
        dl = (c1.lab_l - c2.lab_l) / steps
        da = (c1.lab_a - c2.lab_a) / steps
        db = (c1.lab_b - c2.lab_b) / steps
        gradient: list[sRGBColor] = []
        for _ in range(steps):
            c1.lab_l -= dl
            c1.lab_a -= da
            c1.lab_b -= db
            newcolor: sRGBColor = convert_color(c1, sRGBColor)
            gradient.append(newcolor)
        return gradient

    await trio.sleep(2)
    while True:
        for guild in bot.guilds.values():
            rainbow_role = utils.get_rainbow_role(bot.con, guild.id)
            if not rainbow_role:
                continue
            log.debug(f"Got rainbow role {rainbow_role} for guild {guild.id}")
            if not bot.color_list:
                current_color = guild.roles[rainbow_role].srgb_color
                c1lab: sRGBColor = convert_color(current_color, LabColor)
                if random.choice(range(200)) == 69:
                    next_color: sRGBColor = sRGBColor.new_from_rgb_hex("#36393F")
                    c2lab: LabColor = convert_color(next_color, LabColor)
                    delta_e = delta_e_cie2000(c1lab, c2lab)
                else:
                    while True:
                        next_color: sRGBColor = sRGBColor(
                            random.random(), random.random(), random.random()
                        )
                        c2lab: LabColor = convert_color(next_color, LabColor)
                        if c2lab.lab_l > 40:
                            break
                    delta_e = delta_e_cie2000(c1lab, c2lab)
                bot.color_list = generate_lab_gradient(
                    current_color, next_color, int(delta_e)
                )

            log.debug(f"gradient: {[i.get_rgb_hex() for i in bot.color_list]}")
            nextcolor = bot.color_list.pop(0)
            rgb = nextcolor.get_upscaled_value_tuple()
            log.debug(f"next color: {rgb}")
            finalcolor = 65536 * rgb[0] + 256 * rgb[1] + rgb[2]
            await bot.update_role(guild.id, rainbow_role, finalcolor)
        await trio.sleep(120)


if __name__ == "__main__":
    try:
        bot.connect()
    except KeyboardInterrupt:
        log.info("Program halted due to keyboard interrupt.")
    except Exception as e:
        log.exception("Program halted due to unhandled exception:")
