#! conf_vars.py
# Loads and stores environment variables

import os
from dotenv import load_dotenv

load_dotenv()

class ConfVars:
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD_ID = int(os.getenv('GUILD_ID'))
    VOTE_CHANNEL = int(os.getenv('VOTE_CHANNEL'))
    PRIVATE_CHAT_CATEGORY = int(os.getenv('PRIVATE_CHAT_CATEGORY'))
    MOD_CATEGORY = int(os.getenv('MOD_CATEGORY'))
    BASE_PATH = os.getenv('BASE_PATH')
    EMOJI_FILE = os.getenv('EMOJI_FILE')
    EMOJI_PATH = f'{BASE_PATH}/{EMOJI_FILE}'
    GAME_CONF_FILE = os.getenv('GAME_CONF_FILE')
    GAME_CONF_PATH = f'{BASE_PATH}/{GAME_CONF_FILE}'
    CHARACTER_FILE = os.getenv('CHARACTER_FILE')
    CHAR_FILE_PATH = f'{BASE_PATH}/{CHARACTER_FILE}'
    PLAYER_CHARACTER_FILE = os.getenv('PLAYER_CHARACTER_FILE')
    PLAYER_CHAR_PATH = f'{BASE_PATH}/{PLAYER_CHARACTER_FILE}'
    GAME_FILE = os.getenv('GAME_FILE')
    GAME_PATH = f'{BASE_PATH}/{GAME_FILE}'
