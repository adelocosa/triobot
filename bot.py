import logging
import logging.handlers
import os

from dotenv import load_dotenv

load_dotenv()

import discord

log_format = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")

console_log = logging.StreamHandler()
console_log.setLevel(logging.INFO)
console_log.setFormatter(log_format)

file_log = logging.handlers.RotatingFileHandler(
    "debug.log", maxBytes=10000000, backupCount=5, encoding="utf8"
)
file_log.setLevel(logging.DEBUG)
file_log.setFormatter(log_format)

log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(console_log)
log.addHandler(file_log)


def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    assert isinstance(TOKEN, str)
    log.info("Token found. Initializing bot...")
    bot = discord.Client(TOKEN)
    bot.connect()


try:
    main()
except KeyboardInterrupt:
    log.info("Program halted due to keyboard interrupt.")
except Exception as e:
    log.exception("Program halted due to unhandled exception:")
