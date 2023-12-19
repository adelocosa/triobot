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
        validate: bool,
        url: str = "",
        service: str = "",
        username: str = "",
        userid: str = "",
    ):
        self.live: bool = False
        self.url = url
        self.service = service
        self.username = username
        self.userid = userid
        if not (self.service and self.username):
            self.url, self.service, self.username = self.parse_url(self.url)
        if validate:
            self.valid: bool = self.validate()
            log.debug(f"{self.url} validated: {self.valid}")

    def __repr__(self):
        return (
            f"Stream('{self.url}','{self.service}','{self.username}','{self.userid}',)"
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
        service = parsed.netloc
        username = parsed.path.strip("/")
        url = f"https://{service}/{username}"
        log.debug(f"Parsed stream url (service = {service}, username = {username}).")
        return (url, service, username)

    def validate(self) -> bool:
        if not self.service == "twitch.tv":
            return False
        self.userid = get_userid_from_username(self.username)
        return False if not self.userid else True


def adapt_stream(stream: Stream):
    return f"{stream.url};{stream.service};{stream.username};{stream.userid}"


def convert_stream(query: bytes) -> Stream:
    url, service, username, userid = [s.decode("utf-8") for s in query.split(b";")]
    return Stream(False, url, service, username, userid)
