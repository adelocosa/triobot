from __future__ import annotations
import httpx
import os
import logging
import json
from typing import Optional
from dotenv import load_dotenv

log = logging.getLogger(__name__)


def get_twitch_bearer_token() -> Optional[str]:
    load_dotenv("./appdata/.env", override=True)
    TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
    TWITCH_CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
    get_token_url = f"https://id.twitch.tv/oauth2/token?client_id={TWITCH_CLIENT_ID}&client_secret={TWITCH_CLIENT_SECRET}&grant_type=client_credentials"
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
    load_dotenv("./appdata/.env", override=True)
    TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
    TWITCH_TOKEN = os.environ.get("TWITCH_TOKEN")
    headers = {
        "Authorization": f"Bearer {TWITCH_TOKEN}",
        "Client-Id": f"{TWITCH_CLIENT_ID}",
    }
    url = f"https://api.twitch.tv/helix/users?login={username}"
    try:
        response = httpx.get(url, headers=headers)
        log.debug(json.dumps(response.json(), indent=4))
        userid = response.json()["data"][0]["id"]
        log.info(f"Got userid {userid}")
    except:
        userid = ""
        log.info(f"Couldn't get userid for {username}.")
    return userid


async def get_live_streams_by_usernames(
    usernames: list[str],
) -> tuple[list[Optional[str]], bool]:
    live = []
    if not usernames:
        log.info(f"Couldn't get streams.")
        return live, False
    load_dotenv("./appdata/.env", override=True)
    TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
    TWITCH_TOKEN = os.environ.get("TWITCH_TOKEN")
    headers = {
        "Authorization": f"Bearer {TWITCH_TOKEN}",
        "Client-Id": f"{TWITCH_CLIENT_ID}",
    }
    url = f"https://api.twitch.tv/helix/streams?"
    for username in usernames:
        url += f"user_login={username}&"
    url += "type=live&first=100"
    try:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        response = httpx.get(url, headers=headers)
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        log.debug(json.dumps(response.json(), indent=4))
        log.debug(json.dumps(dict(response.headers), indent=4))
        for stream in response.json()["data"]:
            live.append(stream["user_login"])
        return live, True
    except:
        log.info(f"Couldn't get streams.")
        return live, False
