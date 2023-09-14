#! game_configurations.py
# a class for managing game state details
import json
from typing import Optional, List, Dict
from datetime import datetime
from logging_manager import logger
from enum import Enum


class VotingStyle(Enum):
    PLAYER = "player"
    OPTION = "option"


class GameResource:
    def __init__(self, resource_name: str, is_commodity: bool = None, resource_faction_limited: List[str] = None,
                 resource_tag_limited: List[str] = None, resource_def_amt: int = None, resource_min: int = None, resource_max: int = None):
        self.resource_name = resource_name
        self.is_commodity = is_commodity if is_commodity is not None else False
        self.resource_faction_limited = resource_faction_limited if resource_faction_limited is not None else []
        self.resource_tag_limited = resource_tag_limited if resource_tag_limited is not None else []
        self.resource_def_amt = resource_def_amt if resource_def_amt is not None else 0
        self.resource_min = resource_min if resource_min is not None else 0
        self.resource_max = resource_max


class GameAttribute:
    def __init__(self, attr_name: str, is_adjustable: bool = None, attr_def_amt: int = None, attr_min: int = None, attr_max: int = None):
        self.attr_name = attr_name
        self.is_adjustable = is_adjustable if is_adjustable is not None else False
        self.attr_def_amt = attr_def_amt if attr_def_amt is not None else 0
        self.attr_min = attr_min if attr_min is not None else 0
        self.attr_max = attr_max


class VotingParameters:
    def __init__(self, voting_style: VotingStyle = None, voting_enabled: bool = None):
        self.voting_style = voting_style if voting_style is not None else VotingStyle.PLAYER
        self.voting_enabled = voting_enabled if voting_enabled is not None else True


class GameConfiguration:
    def __init__(self, voting_params: VotingParameters, game_resources: List[GameResource] = None, game_attrs: List[GameAttribute] = None):
        self.voting_params = voting_params
        self.game_resources = game_resources if game_resources is not None else []
        self.game_attrs = game_attrs if game_attrs is not None else []


def read_json_to_dom(filepath: str) -> GameConfiguration:
    with open(filepath, 'r', encoding="utf8") as openfile:
        json_object = json.load(openfile)

        game_resources = []
        game_attrs = []
        if json_object.get("game_configuration") is not None:
            game_conf_jsobject = json_object.get("game_configuration")
            if game_conf_jsobject.get("voting_configuration") is not None:
                voting_conf_jsobject = game_conf_jsobject.get("voting_configuration")
                voting_style = voting_conf_jsobject.get("voting_style")
                voting_enabled = voting_conf_jsobject.get("voting_enabled")
            voting_params = VotingParameters(voting_style=VotingStyle(voting_style), voting_enabled=voting_enabled)
            if game_conf_jsobject.get("game_resources") is not None:
                for resource_entry in game_conf_jsobject.get("game_resources"):
                    resource_name = resource_entry.get("resource_name")
                    is_commodity = resource_entry.get("is_commodity")
                    resource_faction_limited = []
                    resource_tag_limited = []
                    if resource_entry.get("resource_faction_limited") is not None:
                        for resource_faction in resource_entry.get("resource_faction_limited"):
                            resource_faction_limited.append(resource_faction)
                    if resource_entry.get("resource_tag_limited") is not None:
                        for resource_tag in resource_entry.get("resource_tag_limited"):
                            resource_tag_limited.append(resource_tag)
                    resource_def_amt = resource_entry.get("resource_def_amt")
                    resource_min = resource_entry.get("resource_min")
                    resource_max = resource_entry.get("resource_max")
                    game_resources.append(GameResource(resource_name=resource_name,
                                                       is_commodity=is_commodity,
                                                       resource_faction_limited=resource_faction_limited,
                                                       resource_tag_limited=resource_tag_limited,
                                                       resource_def_amt=resource_def_amt,
                                                       resource_min=resource_min,
                                                       resource_max=resource_max
                                                       ))
            if game_conf_jsobject.get("game_attributes") is not None:
                for attr_entry in game_conf_jsobject.get("game_attributes"):
                    attr_name = attr_entry.get("attr_name")
                    is_adjustable = attr_entry.get("is_adjustable")
                    attr_def_amt = attr_entry.get("attr_def_amt")
                    attr_min = attr_entry.get("attr_min")
                    attr_max = attr_entry.get("attr_max")
                    game_attrs.append(GameAttribute(attr_name=attr_name,
                                                    is_adjustable=is_adjustable,
                                                    attr_def_amt=attr_def_amt,
                                                    attr_min=attr_min,
                                                    attr_max=attr_max
                                                    ))

        return GameConfiguration(voting_params=voting_params, game_resources=game_resources, game_attrs=game_attrs)


def write_dom_to_json(game_conf: GameConfiguration, filepath: str):
    with open(filepath, 'w', encoding="utf8") as outfile:

        #convert GameConfiguration to dictionary here
        voting_conf_dict = {
            "voting_style": game_conf.voting_params.voting_style.value,
            "voting_enabled": game_conf.voting_params.voting_enabled
        }
        game_resources_dicts = []
        for game_resource in game_conf.game_resources:
            resource_faction_limited = []
            for faction in game_resource.resource_faction_limited:
                resource_faction_limited.append(faction)
            resource_tag_limited = []
            for tag in game_resource.resource_tag_limited:
                resource_tag_limited.append(tag)
            game_resources_dicts.append({
                "resource_name": game_resource.resource_name,
                "is_commodity": game_resource.is_commodity,
                "resource_faction_limited": resource_faction_limited,
                "resource_tag_limited": resource_tag_limited,
                "resource_def_amt": game_resource.resource_def_amt,
                "resource_min": game_resource.resource_min,
                "resource_max": game_resource.resource_max
            })
        game_attr_dicts = []
        for game_attr in game_conf.game_attrs:
            game_attr_dicts.append({
                "attr_name": game_attr.attr_name,
                "is_adjustable": game_attr.is_adjustable,
                "attr_def_amt": game_attr.attr_def_amt,
                "attr_min": game_attr.attr_min,
                "attr_max": game_attr.attr_max
            })
        game_conf_dict = {"voting_configuration": voting_conf_dict,
                          "game_resources": game_resources_dicts,
                          "game_attributes": game_attr_dicts
                          }
        game_conf_parent_dict = {"game_configuration": game_conf_dict}

        json.dump(game_conf_parent_dict, outfile, indent=2, ensure_ascii=False)


async def get_game_conf(file_path: str) -> GameConfiguration:
    logger.info(f'Grabbing game info from {file_path}')
    return read_json_to_dom(filepath=file_path)


async def write_game_conf(game_conf: GameConfiguration, file_path: str):
    logger.info(f'Wrote game configuration data to {file_path}')
    write_dom_to_json(game_conf=game_conf, filepath=file_path)
