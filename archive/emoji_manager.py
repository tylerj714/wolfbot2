#! emoji_manager.py
# a class for managing game emoji assets
import json
from typing import Optional, List, Dict
from logging_manager import logger


def read_json_to_dom(filepath: str) -> Dict[str, str]:
    with open(filepath, 'r', encoding="utf8") as openfile:
        json_object = json.load(openfile)

        emoji_dict = {}
        if json_object.get("emojis") is not None:
            for emoji_entry in json_object.get("emojis"):
                emoji_name = emoji_entry.get("name")
                emoji_identifier = emoji_entry.get("identifier")
                emoji_dict[emoji_name] = emoji_identifier

        return emoji_dict


async def get_emojis(file_path: str) -> Dict[str, str]:
    logger.info(f'Grabbing emoji in from {file_path}')
    return read_json_to_dom(filepath=file_path)
