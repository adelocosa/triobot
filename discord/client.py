import logging
import random
import time

import trio

from .gateway import GatewayConnection
from .guild import Guild
from .user import User

log = logging.getLogger(__name__)


class Client:

    START_DELAY = 1.1
    MAX_DELAY = 32

    def __init__(self, TOKEN: str):
        self.TOKEN = TOKEN
        self.sequence: None | int = None
        self.session_id: None | str = None
        self.delay = self.START_DELAY
        self.guilds: dict[int, Guild] = {}
        self.users: dict[int, User] = {}

    def connect(self):
        while True:
            self.connection = GatewayConnection(self, self.TOKEN)
            log.info("Attempting to connect...")
            trio.run(self.connection.connect)
            log.warning(f"Disconnected! Reconnecting in {self.delay:.1f} seconds...")
            time.sleep(self.delay)
            self.increase_delay()

    def increase_delay(self):
        new_delay = int(self.delay) * 2
        if new_delay != self.MAX_DELAY:
            new_delay += random.random()
        self.delay = new_delay

    def reset_delay(self):
        self.delay = self.START_DELAY
