#! wolfbot_dom.py
# a class for managing game state details
import json
from typing import Optional, List, Dict
from datetime import datetime


class Embed:
    def __init__(self, title: str, descr: str, color: str, fields: Dict[str, str]):
        self.title = title
        self.descr = descr
        self.color = color
        self.fields = fields


class CharacterEmbed:
    def __init__(self, message_id: int, embeds: List[Embed]):
        self.message_id = message_id
        self.embeds = embeds


class PlayerCharacter:
    def __init__(self, role_id: int, character_embeds: List[CharacterEmbed]):
        self.role_id = role_id
        self.character_embeds = character_embeds


class Attribute:
    def __init__(self, name: str, level: int, max_level: int):
        self.name = name
        self.level = level
        self.max_level = max_level


class Action:
    def __init__(self, name: str, desc: str, uses: int, image: str, timing: str):
        self.name = name
        self.desc = desc
        self.uses = uses
        self.image = image
        self.timing = timing


class Player:
    def __init__(self, player_id: int, player_discord_name: str, player_mod_channel: str, player_attributes: List[Attribute],
                 player_actions: List[Action], is_dead: bool = False):
        self.player_id = player_id
        self.player_discord_name = player_discord_name
        self.player_mod_channel = player_mod_channel
        self.player_attributes = player_attributes
        self.player_actions = player_actions
        self.is_dead = is_dead


class Vote:
    def __init__(self, player_id: int, choice: str, timestamp: int):
        self.player_id = player_id
        self.choice = choice
        self.timestamp = timestamp


class Round:
    def __init__(self, votes: List[Vote], round_number: int, is_active_round: bool):
        self.votes = votes
        self.round_number = round_number
        self.is_active_round = is_active_round

    def get_player_vote(self, player_id: int) -> Optional[Vote]:
        player_vote = None
        for vote in self.votes:
            if vote.player_id == player_id:
                player_vote = vote
        return player_vote

    def add_vote(self, vote: Vote):
        self.votes.append(vote)

    def remove_vote(self, vote: Vote):
        self.votes.remove(vote)


class Game:
    def __init__(self, is_active: bool, players: List[Player], rounds: List[Round]):
        self.is_active = is_active
        self.players = players
        self.rounds = rounds

    def get_player(self, player_id: int) -> Optional[Player]:
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None

    def add_player(self, player: Player):
        self.players.append(player)

    def get_living_player_ids(self) -> List[str]:
        game_player_ids = []
        for player in self.players:
            game_player_ids.append(str(player.player_id))
        return game_player_ids

    def add_round(self, a_round: Round):
        self.rounds.append(a_round)

    def get_round(self, round_num: int) -> Optional[Round]:
        for a_round in self.rounds:
            if a_round.round_number == round_num:
                return a_round
        return None

    def get_latest_round(self) -> Optional[Round]:
        latest_round = None
        previous_round_num = 0
        for a_round in self.rounds:
            if a_round.round_number > previous_round_num:
                previous_round_num = a_round.round_number
                latest_round = a_round
        return latest_round


def read_json_to_dom(filepath: str) -> Game:
    with open(filepath, 'r', encoding="utf8") as openfile:
        json_object = json.load(openfile)

        is_active = json_object.get("is_active")
        players = []
        rounds = []
        if json_object.get("players") is not None:
            for player_entry in json_object.get("players"):
                player_id = player_entry.get("player_id")
                player_mod_channel = player_entry.get("player_mod_channel")
                player_discord_name = player_entry.get("player_discord_name")
                is_dead = player_entry.get("is_dead")
                attributes = []
                if player_entry.get("player_attributes") is not None:
                    for attribute_entry in player_entry.get("player_attributes"):
                        attribute_name = attribute_entry.get("name")
                        attribute_level = attribute_entry.get("level")
                        attribute_max_level = attribute_entry.get("max_level")
                        attributes.append(Attribute(name=attribute_name,
                                                    level=attribute_level,
                                                    max_level=attribute_max_level))
                actions = []
                if player_entry.get("player_actions") is not None:
                    for action_entry in player_entry.get("player_actions"):
                        action_name = action_entry.get("name")
                        action_desc = action_entry.get("desc")
                        action_uses = action_entry.get("uses")
                        action_timing = action_entry.get("timing")
                        action_image = action_entry.get("image")
                        actions.append(Action(name=action_name,
                                              desc=action_desc,
                                              uses=action_uses,
                                              timing=action_timing,
                                              image=action_image))
                players.append(Player(player_id=player_id,
                                      player_discord_name=player_discord_name,
                                      player_mod_channel=player_mod_channel,
                                      player_attributes=attributes,
                                      player_actions=actions,
                                      is_dead=is_dead))

        if json_object.get("rounds") is not None:
            for round_entry in json_object.get("rounds"):
                round_num = round_entry.get("round_number")
                round_is_active = round_entry.get("is_active_round")
                votes = []
                if round_entry.get("votes") is not None:
                    for vote_entry in round_entry.get("votes"):
                        player_id = vote_entry.get("player_id")
                        choice = vote_entry.get("choice")
                        timestamp = vote_entry.get("timestamp")
                        votes.append(Vote(player_id=player_id,
                                          choice=choice,
                                          timestamp=timestamp))
                rounds.append(Round(round_number=round_num,
                                    is_active_round=round_is_active,
                                    votes=votes))

        return Game(is_active, players, rounds)


def write_dom_to_json(game: Game, filepath: str):
    with open(filepath, 'w', encoding="utf8") as outfile:

        #convert Game to dictionary here
        game_dict = {"is_active": game.is_active}
        player_dicts = []
        for player in game.players:
            attribute_dicts = []
            for attribute in player.player_attributes:
                attribute_dicts.append({"name": attribute.name,
                                        "level": attribute.level,
                                        "max_level": attribute.max_level})
            action_dicts = []
            for action in player.player_actions:
                action_dicts.append({"name": action.name,
                                     "desc": action.desc,
                                     "uses": action.uses,
                                     "timing": action.timing,
                                     "image": action.image})
            player_dicts.append({"player_id": player.player_id,
                                 "player_discord_name": player.player_discord_name,
                                 "player_mod_channel": player.player_mod_channel,
                                 "player_attributes": attribute_dicts,
                                 "player_actions": action_dicts,
                                 "is_dead": player.is_dead
                                 })
        game_dict["players"] = player_dicts
        round_dicts = []
        for a_round in game.rounds:
            vote_dicts = []
            for vote in a_round.votes:
                vote_dicts.append({"player_id": vote.player_id,
                                   "choice": vote.choice,
                                   "timestamp": vote.timestamp})
            round_dicts.append({"round_number": a_round.round_number,
                                "is_active_round": a_round.is_active_round,
                                "votes": vote_dicts})
        game_dict["rounds"] = round_dicts
        json.dump(game_dict, outfile, indent=2, ensure_ascii=False)
