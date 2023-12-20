from __future__ import annotations
import sqlite3
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .stream import Stream

log = logging.getLogger(__name__)


def create_users_table(con: sqlite3.Connection):
    con.execute(
        """
    CREATE TABLE IF NOT EXISTS Users (
        UserID TEXT PRIMARY KEY
    )
    """
    )
    con.commit()
    log.debug("Created Users table.")


def create_userstreams_table(con: sqlite3.Connection):
    con.execute(
        """
    CREATE TABLE IF NOT EXISTS UserStreams (
        StreamID INTEGER PRIMARY KEY,
        UserID TEXT,
        Stream STREAM,
        FOREIGN KEY(UserID) REFERENCES Users(UserID)
    )
    """
    )
    con.commit()
    log.debug("Created UserStreams table.")


def create_guilds_table(con: sqlite3.Connection):
    con.execute(
        """
    CREATE TABLE IF NOT EXISTS Guilds (
        GuildID TEXT PRIMARY KEY,
        AnnounceChannel TEXT
        RainbowRole TEXT
    )
    """
    )
    con.commit()
    log.debug("Created Guilds table.")


def get_streams_by_userid(con: sqlite3.Connection, user_id: str) -> list[Stream]:
    query = "SELECT Stream FROM UserStreams WHERE UserID = ?"
    streams: list[Stream] = [s[0] for s in list(con.execute(query, (user_id,)))]
    log.debug("Executed get streams by userid query.")
    return streams


def get_streams_by_userids(
    con: sqlite3.Connection, user_ids: list[str]
) -> list[Stream]:
    query = "SELECT Stream FROM UserStreams WHERE UserID IN ({})".format(
        ",".join("?" for _ in user_ids)
    )
    result: list[Stream] = [s[0] for s in con.execute(query, user_ids)]
    log.debug("Executed get streams by userids query.")
    return result


def get_all_streams(con: sqlite3.Connection) -> list[tuple[str, Stream]]:
    query = "SELECT UserID, Stream FROM UserStreams"
    result: list[tuple[str, Stream]] = list(con.execute(query))
    log.debug("Executed get all streams query.")
    return result


def get_announce_channel(con: sqlite3.Connection, guild_id: str) -> Optional[str]:
    channel_id = con.execute(
        "SELECT AnnounceChannel FROM Guilds WHERE GuildID = ?", (guild_id,)
    ).fetchone()
    log.debug("Executed get announce channel query.")
    if channel_id:
        return channel_id[0]
    return None


def get_rainbow_role(con: sqlite3.Connection, guild_id: str) -> Optional[str]:
    role_id = con.execute(
        "SELECT RainbowRole FROM Guilds WHERE GuildID = ?", (guild_id,)
    ).fetchone()
    log.debug("Executed get rainbow role query.")
    if role_id:
        return role_id[0]
    return None


def insert_user(con: sqlite3.Connection, user_id: str):
    con.execute(
        "INSERT OR IGNORE INTO Users (UserID) VALUES (?)",
        (user_id,),
    )
    con.commit()
    log.debug("Executed insert user query.")


def insert_announce_channel(con: sqlite3.Connection, guild_id: str, channel_id: str):
    exists = con.execute(
        "SELECT 1 FROM Guilds WHERE GuildID = ? LIMIT 1", (guild_id,)
    ).fetchone()
    if exists:
        con.execute(
            "UPDATE Guilds SET AnnounceChannel = ? WHERE GuildID = ?",
            (
                channel_id,
                guild_id,
            ),
        )
    else:
        con.execute(
            "INSERT INTO Guilds (GuildID, AnnounceChannel) VALUES (?, ?)",
            (
                guild_id,
                channel_id,
            ),
        )
    con.commit()
    log.debug("Executed insert announce channel query.")


def insert_rainbow_role(con: sqlite3.Connection, guild_id: str, role_id: str):
    exists = con.execute(
        "SELECT 1 FROM Guilds WHERE GuildID = ? LIMIT 1", (guild_id,)
    ).fetchone()
    if exists:
        con.execute(
            "UPDATE Guilds SET RainbowRole = ? WHERE GuildID = ?",
            (
                role_id,
                guild_id,
            ),
        )
    else:
        con.execute(
            "INSERT INTO Guilds (GuildID, RainbowRole) VALUES (?, ?)",
            (
                guild_id,
                role_id,
            ),
        )
    con.commit()
    log.debug("Executed insert announce channel query.")


def insert_stream(con: sqlite3.Connection, user_id: str, stream: Stream):
    con.execute(
        "INSERT INTO UserStreams (UserID, Stream) VALUES (?, ?)",
        (
            user_id,
            stream,
        ),
    )
    con.commit()
    log.debug("Executed insert stream query.")


def delete_stream(con: sqlite3.Connection, stream: Stream):
    con.execute("DELETE FROM UserStreams WHERE Stream = ?", (stream,))
    con.commit()
    log.debug("Executed delete stream query.")
