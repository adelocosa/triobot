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
        self, url: str = "", service: str = "", username: str = "", userid: str = ""
    ):
        self.url = url
        self.service = service
        self.username = username
        self.userid = userid
        if not (self.service and self.username):
            self.url, self.service, self.username = self.parse_url(self.url)
        if not self.userid:
            self.valid: bool = self.validate()
            log.info(f"{self.url} validated: {self.valid}")

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
        log.info(f"Parsed stream url (service = {service}, username = {username}).")
        return (url, service, username)

    def validate(self) -> bool:
        if self.service == "twitch.tv":
            oauth_token = get_twitch_bearer_token()
            if not oauth_token:
                return False
            self.userid = get_userid_from_username(oauth_token, self.username)
            return False if not self.userid else True
        else:
            return False


def adapt_stream(stream: Stream):
    return f"{stream.url};{stream.service};{stream.username};{stream.userid}"


def convert_stream(query: bytes) -> Stream:
    url, service, username, userid = [s.decode("utf-8") for s in query.split(b";")]
    return Stream(url, service, username, userid)
