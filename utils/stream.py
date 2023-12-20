from __future__ import annotations
from urllib.parse import urlparse
from .twitch import *
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)


class Stream:
    def __init__(
        self,
        url: str = "",
        service: str = "",
        username: str = "",
        userid: str = "",
    ):
        self.url = url
        self.service = service
        self.username = username
        self.userid = userid
        self.is_live: bool = False
        self.was_live: bool = False
        self.valid: bool = False
        if not (self.service and self.username):
            self.url, self.service, self.username = self.parse_url(self.url)

    def __repr__(self):
        return (
            f"Stream('{self.url}','{self.service}','{self.username}','{self.userid}')"
        )

    def __str__(self):
        return f"<{self.url}>"

    def __eq__(self, other: Stream):
        return (self.service, self.username) == (other.service, other.username)

    def parse_url(self, url: str) -> tuple[str, str, str]:
        if not url.startswith("http"):
            url = f"https://{url}"
        url = url.replace("www.", "")
        parsed = urlparse(url)
        service = parsed.netloc.lower()
        username = parsed.path.strip("/").lower()
        url = f"https://{service}/{username}"
        log.debug(f"Parsed stream url (service = {service}, username = {username}).")
        return (url, service, username)

    async def validate(self) -> bool:
        if not self.service == "twitch.tv":
            return False
        self.userid = await get_userid_from_username(self.username)
        if self.userid:
            self.valid = True
            log.debug(f"{self.url} validated: {self.valid}")
            return True
        return False


def adapt_stream(stream: Stream):
    return f"{stream.url};{stream.service};{stream.username};{stream.userid}"


def convert_stream(query: bytes) -> Stream:
    url, service, username, userid = [s.decode("utf-8") for s in query.split(b";")]
    return Stream(url, service, username, userid)
