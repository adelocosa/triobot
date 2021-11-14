import logging
import time

import trio

from .gateway import GatewayConnection

log = logging.getLogger(__name__)


class Client:
    def __init__(self, TOKEN: str):
        self.TOKEN = TOKEN
        self.sequence: None | int = None
        self.session_id: None | str = None
        self.delay = 5  # temporary

    def connect(self):
        while True:
            self.connection = GatewayConnection(self, self.TOKEN)
            trio.run(self.connection.connect)
            log.warning(f"disconnected! reconnecting in {self.delay} seconds")
            time.sleep(self.delay)
