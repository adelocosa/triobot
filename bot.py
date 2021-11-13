import discord
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    TOKEN = os.environ.get('BOT_TOKEN')
    assert isinstance(TOKEN, str)
    bot = discord.Client(TOKEN)
    bot.connect()

main()