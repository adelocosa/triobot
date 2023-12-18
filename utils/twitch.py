from __future__ import annotations
import httpx
import os
import logging
import json
from typing import Optional

log = logging.getLogger(__name__)


def get_twitch_bearer_token() -> Optional[str]:
    CLIENT_ID = os.environ.get("CLIENT_ID")
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
    get_token_url = f"https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&grant_type=client_credentials"
    try:
        log.info("Sending twitch oauth token request.")
        response = httpx.post(get_token_url)
        oauth_token = response.json()["access_token"]
        log.info(f"Got oauth token: {oauth_token}")
    except:
        log.info("Couldn't get oauth token!")
        oauth_token = None
    return oauth_token


def get_userid_from_username(oauth_token: str, username: str) -> str:
    CLIENT_ID = os.environ.get("CLIENT_ID")
    headers = {
        "Authorization": f"Bearer {oauth_token}",
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
        log.info("Couldn't get twitch user. Invalid username?")
    return userid
