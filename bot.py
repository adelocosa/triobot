import logging
import os

from dotenv import load_dotenv

import discord

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_log = logging.StreamHandler()
console_log.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(console_log)

file_log = logging.FileHandler("log.txt")
file_log.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(file_log)


def main():
    load_dotenv()
    TOKEN = os.environ.get("BOT_TOKEN")
    assert isinstance(TOKEN, str)
    logger.info("Token found. Initializing bot...")
    bot = discord.Client(TOKEN)
    bot.connect()


try:
    main()
except KeyboardInterrupt:
    logger.info("Program halted due to keyboard interrupt.")
except Exception as e:
    logger.exception("Program halted due to unhandled exception:")
