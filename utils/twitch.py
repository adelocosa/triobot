from __future__ import annotations
import httpx
import os
import logging
import json
import time
from typing import Optional

log = logging.getLogger(__name__)


def get_twitch_bearer_token() -> Optional[str]:
    CLIENT_ID = os.environ.get("CLIENT_ID")
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
    get_token_url = f"https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&grant_type=client_credentials"
    try:
        log.info("Sending twitch oauth token request.")
        response = httpx.post(get_token_url)
        log.debug(json.dumps(response.json(), indent=4))
        oauth_token = response.json()["access_token"]
        log.info(f"Got oauth token: {oauth_token}")
    except:
        log.info("Couldn't get oauth token!")
        oauth_token = None
    return oauth_token


async def get_userid_from_username(username: str) -> str:
    CLIENT_ID = os.environ.get("CLIENT_ID")
    TWITCH_TOKEN = os.environ.get("TWITCH_TOKEN")
    headers = {
        "Authorization": f"Bearer {TWITCH_TOKEN}",
        "Client-Id": f"{CLIENT_ID}",
    }
    url = f"https://api.twitch.tv/helix/users?login={username}"
    try:
        log.info("Sending twitch Get Users request.")
        response = httpx.get(url, headers=headers)
        log.debug(json.dumps(response.json(), indent=4))
        userid = response.json()["data"][0]["id"]
        log.info(f"Got userid {userid}")
    except:
        userid = ""
        log.info(f"Couldn't get userid for {username}.")
    return userid


async def get_live_streams_by_usernames(usernames: list[str]) -> list[Optional[str]]:
    live = []
    CLIENT_ID = os.environ.get("CLIENT_ID")
    TWITCH_TOKEN = os.environ.get("TWITCH_TOKEN")
    headers = {
        "Authorization": f"Bearer {TWITCH_TOKEN}",
        "Client-Id": f"{CLIENT_ID}",
    }
    url = f"https://api.twitch.tv/helix/streams?"
    for username in usernames:
        url += f"user_login={username}&"
    url += "type=live&first=100"
    try:
        log.info("Sending twitch Get Streams request.")
        response = httpx.get(url, headers=headers)
        log.debug(json.dumps(response.json(), indent=4))
        log.debug(json.dumps(dict(response.headers), indent=4))
    except:
        log.info(f"Couldn't get streams.")
        return live
    for stream in response.json()["data"]:
        live.append(stream["user_login"])
    return live