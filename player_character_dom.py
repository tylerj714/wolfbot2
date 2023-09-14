#! player_character_dom.py
# a class for managing game state details
import json
from typing import Optional, List, Dict
from enum import Enum


class ActionTiming(Enum):
    NIGHT = "night"
    DAY = "day"
    ANY = "any"
    NIGHT_BONUS = "night_bonus"
    DAY_BONUS = "day_bonus"
    ANY_BONUS = "any_bonus"
    OTHER = "other"
    OTHER_BONUS = "other_bonus"
    PASSIVE = "passive"


class CharResource:
    def __init__(self, resource_name: str, resource_amt: int = None, resource_min: int = None, resource_max: int = None):
        self.resource_name = resource_name
        self.resource_amt = resource_amt if resource_amt is not None else 0
        self.resource_min = resource_min if resource_min is not None else 0
        self.resource_max = resource_max


class CharAttribute:
    def __init__(self, attr_name: str, attr_amount: int = None, attr_min: int = None, attr_max: int = None):
        self.attr_name = attr_name
        self.attr_amount = attr_amount if attr_amount is not None else 0
        self.attr_min = attr_min if attr_min is not None else 0
        self.attr_max = attr_max


class VoteAttributes:
    def __init__(self, can_vote: bool = None, can_be_voted: bool = None, vote_strength: int = None):
        self.can_vote = can_vote if can_vote is not None else True
        self.can_be_voted = can_be_voted if can_be_voted is not None else True
        self.vote_strength = vote_strength if vote_strength is not None else 1


class CharAction:
    def __init__(self, action_name: str, action_timing: List[ActionTiming], action_text: str, action_uses: int = None):
        self.action_name = action_name
        self.action_timing = action_timing
        self.action_uses = action_uses if action_uses is not None else -1
        self.action_text = action_text


class ItemProperties:
    def __init__(self, is_transferrable: bool = None, is_destructible: bool = None):
        self.is_transferrable = is_transferrable if is_transferrable is not None else False
        self.is_destructible = is_destructible if is_destructible is not None else False


class GameItem:
    def __init__(self, item_name: str, item_action_name: str, item_action_timing: List[ActionTiming], item_action_text: str, item_action_uses = None):
        self.item_name = item_name
        self.item_action_name = item_action_name
        self.item_action_timing = item_action_timing
        self.item_action_uses = item_action_uses if item_action_uses is not None else -1
        self.item_action_text = item_action_text


class PlayerCharacter:
    def __init__(self, character_name: str, character_factions: List[str], character_objectives: List[str], character_vote_attributes: VoteAttributes,
                 character_tags: List[str] = None, character_resources: List[CharResource] = None, character_attrs: List[CharAttribute] = None,
                 character_actions: List[CharAction] = None, character_item_capacity: int = None, character_items: List[GameItem] = None):
        self.character_name = character_name
        self.character_factions = character_factions
        self.character_tags = character_tags if character_tags is not None else []
        self.character_objectives = character_objectives
        self.character_vote_attributes = character_vote_attributes
        self.character_resources = character_resources if character_resources is not None else []
        self.character_attrs = character_attrs if character_attrs is not None else []
        self.character_actions = character_actions if character_actions is not None else []
        self.character_item_capacity = character_item_capacity if character_item_capacity is not None else -1
        self.character_items = character_items if character_items is not None else []

