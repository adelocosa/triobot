from __future__ import annotations
import sqlite3
import logging
from typing import TYPE_CHECKING

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


def get_streams_by_userid(con: sqlite3.Connection, userid: str) -> list[Stream]:
    streams: list[Stream] = [
        s[1]
        for s in list(
            con.execute(
                """
        SELECT UserStreams.StreamID, UserStreams.Stream
        FROM UserStreams
        JOIN Users ON UserStreams.UserID = Users.UserID
        WHERE Users.UserID = ?
        """,
                (userid,),
            )
        )
    ]
    log.debug("Executed get_streams query.")
    return streams


def insert_user(con: sqlite3.Connection, userid: str):
    con.execute(
        "INSERT OR IGNORE INTO Users (UserID) VALUES (?)",
        (userid,),
    )
    con.commit()
    log.debug("Executed insert user query.")


def insert_stream(con: sqlite3.Connection, userid: str, stream: Stream):
    con.execute(
        "INSERT INTO UserStreams (UserID, Stream) VALUES (?, ?)",
        (
            userid,
            stream,
        ),
    )
    con.commit()
    log.debug("Executed insert stream query.")


def delete_stream(con: sqlite3.Connection, stream: Stream):
    con.execute("DELETE FROM UserStreams WHERE Stream = ?", (stream,))
    con.commit()
    log.debug("Executed delete stream query.")
