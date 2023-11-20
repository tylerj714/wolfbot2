#! game_manager.py
# a class for managing game state details
import json
from typing import Optional, List, Dict, Set
from archive.logging_manager import logger
import csv
import time
import os
from dom.conf_vars import ConfVars as Conf

class Attribute:
    def __init__(self, name: str, level: int, max_level: int):
        self.name = name
        self.level = level
        self.max_level = max_level


class Resource:
    def __init__(self, resource_type: str, resource_amt: int):
        self.resource_type = resource_type
        self.resource_amt = resource_amt


class Action:
    def __init__(self, name: str, timing: str, desc: str, uses: int):
        self.name = name
        self.timing = timing
        self.desc = desc
        self.uses = uses


class Item:
    def __init__(self, item_name: str, item_action: Optional[Action], item_desc: str):
        self.item_name = item_name
        self.item_action = item_action
        self.item_descr = item_desc


class Player:
    def __init__(self, player_id: int, player_discord_name: str, player_mod_channel: int,
                 player_attributes: List[Attribute], player_actions: List[Action], player_items: List[Item],
                 is_dead: bool = False):
        self.player_id = player_id
        self.player_discord_name = player_discord_name
        self.player_mod_channel = player_mod_channel
        self.player_attributes = player_attributes
        self.player_actions = player_actions
        self.player_items = player_items
        self.is_dead = is_dead

    def get_action(self, action_name: str) -> Optional[Action]:
        specific_action: Optional[Action] = None
        for action in self.player_actions:
            if action.name == action_name:
                specific_action = action
        return specific_action

    def add_action(self, action: Action):
        self.player_actions.append(action)

    def remove_action(self, action: Action):
        self.player_actions.remove(action)

    def get_item(self, item_name: str) -> Optional[Item]:
        specific_item: Optional[Item] = None
        for item in self.player_items:
            if item.item_name == item_name:
                specific_item = item
        return specific_item

    def add_item(self, item: Item):
        self.player_items.append(item)

    def remove_item(self, item: Item):
        self.player_items.remove(item)

class Vote:
    def __init__(self, player_id: int, choice: str, timestamp: int):
        self.player_id = player_id
        self.choice = choice
        self.timestamp = timestamp


class Dilemma:
    def __init__(self, dilemma_votes: List[Vote], dilemma_name: str, dilemma_channel_id: int, dilemma_message_id: int,
                 dilemma_player_ids: Set[int], dilemma_choices: Set[str], is_active_dilemma: bool):
        self.dilemma_votes = dilemma_votes
        self.dilemma_name = dilemma_name
        self.dilemma_channel_id = dilemma_channel_id
        self.dilemma_message_id = dilemma_message_id
        self.dilemma_player_ids = dilemma_player_ids
        self.dilemma_choices = dilemma_choices
        self.is_active_dilemma = is_active_dilemma

    def get_player_vote(self, player_id: int) -> Optional[Vote]:
        player_vote = None
        for vote in self.dilemma_votes:
            if vote.player_id == player_id:
                player_vote = vote
        return player_vote

    def add_vote(self, vote: Vote):
        self.dilemma_votes.append(vote)

    def remove_vote(self, vote: Vote):
        self.dilemma_votes.remove(vote)

    def add_player(self, player: Player):
        self.dilemma_player_ids.add(player.player_id)

    def remove_player(self, player: Player):
        self.dilemma_player_ids.remove(player.player_id)

    def add_choice(self, choice: str):
        self.dilemma_choices.add(choice)

    def remove_choice(self, choice: str):
        self.dilemma_choices.remove(choice)


class Party:
    def __init__(self, player_ids: Set[int], party_name: str, max_size: int, channel_id: int):
        self.player_ids = player_ids
        self.channel_id = channel_id
        self.party_name = party_name
        self.max_size = max_size

    def add_player(self, player: Player):
        self.player_ids.add(player.player_id)

    def remove_player(self, player: Player):
        self.player_ids.remove(player.player_id)


class Round:
    def __init__(self, votes: List[Vote], round_channel_id: int, round_message_id: int, round_number: int,
                 round_dilemmas: List[Dilemma], is_active_round: bool):
        self.votes = votes
        self.round_channel_id = round_channel_id
        self.round_message_id = round_message_id
        self.round_dilemmas = round_dilemmas
        self.round_number = round_number
        self.is_active_round = is_active_round

    def add_dilemma(self, dilemma: Dilemma):
        self.round_dilemmas.append(dilemma)

    def close_dilemmas(self):
        for dilemma in self.round_dilemmas:
            dilemma.is_active_dilemma = False

    def get_dilemmas(self):
        return self.round_dilemmas

    def get_dilemma(self, dilemma_name) -> Optional[Dilemma]:
        player_dilemma = None
        for a_dilemma in self.round_dilemmas:
            if dilemma_name == a_dilemma.dilemma_name:
                player_dilemma = a_dilemma
        return player_dilemma

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
    def __init__(self, is_active: bool, parties_locked: bool, voting_locked: bool, items_locked: bool, players: List[Player],
                 parties: List[Party], rounds: List[Round], actions: List[Action], items: List[Item]):
        self.is_active = is_active
        self.parties_locked = parties_locked
        self.voting_locked = voting_locked
        self.items_locked = items_locked
        self.players = players
        self.rounds = rounds
        self.parties = parties
        self.actions = actions
        self.items = items

    def get_player(self, player_id: int | str) -> Optional[Player]:
        player_int_id = player_id if isinstance(player_id, int) else int(player_id)
        for player in self.players:
            if player.player_id == player_int_id:
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

    def add_party(self, a_party: Party):
        self.parties.append(a_party)

    def get_party(self, channel_id: int):
        for a_party in self.parties:
            if a_party.channel_id == channel_id:
                return a_party
        return None

    def get_player_party(self, player: Player):
        for a_party in self.parties:
            if player.player_id in a_party.player_ids:
                return a_party
        return None

    def get_action(self, action_name: str) -> Optional[Action]:
        for action in self.actions:
            if action.name == action_name:
                return action
        return None

    def get_action_map(self) -> Dict[str, Action]:
        action_dict: Dict[str, Action] = {}
        for action in self.actions:
            action_dict[action.name] = action
        return action_dict

    def get_item(self, item_name: str) -> Optional[Item]:
        for item in self.items:
            if item.item_name == item_name:
                return item
        return None

    def get_item_map(self) -> Dict[str, Item]:
        item_dict: Dict[str, Item] = {}
        for item in self.items:
            item_dict[item.item_name] = item
        return item_dict


def map_player_list(players: List[Player]) -> Dict[int, Player]:
    player_dict: Dict[int, Player] = {}
    for player in players:
        player_dict[player.player_id] = player
    return player_dict

def map_action_list(actions: List[Action]) -> Dict[str, Action]:
    action_dict: Dict[str, Action] = {}
    for action in actions:
        action_dict[action.name] = action
    return action_dict

def map_item_list(items: List[Item]) -> Dict[str, Item]:
    item_dict: Dict[str, Item] = {}
    for item in items:
        item_dict[item.item_name] = item
    return item_dict

def read_json_to_dom(filepath: str) -> Game:
    with open(filepath, 'r', encoding="utf8") as openfile:
        json_object = json.load(openfile)

        is_active = json_object.get("is_active")
        parties_locked = json_object.get("parties_locked")
        voting_locked = json_object.get("voting_locked")
        items_locked = json_object.get("items_locked")
        players = []
        rounds = []
        parties = []
        actions = []
        items = []
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
                player_actions = []
                if player_entry.get("player_actions") is not None:
                    for action_entry in player_entry.get("player_actions"):
                        action_name = action_entry.get("name")
                        action_desc = action_entry.get("desc")
                        action_uses = action_entry.get("uses")
                        action_timing = action_entry.get("timing")
                        player_actions.append(Action(name=action_name,
                                                     desc=action_desc,
                                                     uses=action_uses,
                                                     timing=action_timing))
                player_items = []
                if player_entry.get("player_items") is not None:
                    for item_entry in player_entry.get("player_items"):
                        item_name = item_entry.get("item_name")
                        item_desc = item_entry.get("item_desc")
                        item_action: Optional[Action] = None
                        if item_entry.get("item_action") is not None:
                            item_action_entry = item_entry.get("item_action")
                            item_action_name = item_action_entry.get("name")
                            item_action_desc = item_action_entry.get("desc")
                            item_action_timing = item_action_entry.get("timing")
                            item_action_uses = item_action_entry.get("uses")
                            item_action = Action(name=item_action_name,
                                                 desc=item_action_desc,
                                                 uses=item_action_uses,
                                                 timing=item_action_timing)
                        player_items.append(Item(item_name=item_name,
                                                 item_desc=item_desc,
                                                 item_action=item_action))
                players.append(Player(player_id=player_id,
                                      player_discord_name=player_discord_name,
                                      player_mod_channel=player_mod_channel,
                                      player_attributes=attributes,
                                      player_actions=player_actions,
                                      player_items=player_items,
                                      is_dead=is_dead))
        if json_object.get("rounds") is not None:
            for round_entry in json_object.get("rounds"):
                round_channel_id = round_entry.get("round_channel_id")
                round_message_id = round_entry.get("round_message_id")
                round_num = round_entry.get("round_number")
                is_active_round = round_entry.get("is_active_round")
                votes = []
                round_dilemmas = []
                if round_entry.get("votes") is not None:
                    for vote_entry in round_entry.get("votes"):
                        player_id = vote_entry.get("player_id")
                        choice = vote_entry.get("choice")
                        timestamp = vote_entry.get("timestamp")
                        votes.append(Vote(player_id=player_id,
                                          choice=choice,
                                          timestamp=timestamp))
                if round_entry.get("round_dilemmas") is not None:
                    for dilemma_entry in round_entry.get("round_dilemmas"):
                        dilemma_name = dilemma_entry.get("dilemma_name")
                        dilemma_channel_id = dilemma_entry.get("dilemma_channel_id")
                        dilemma_message_id = dilemma_entry.get("dilemma_message_id")
                        is_active_dilemma = dilemma_entry.get("is_active_dilemma")
                        dilemma_choices = set(dilemma_entry.get("dilemma_choices"))
                        dilemma_player_ids = set(dilemma_entry.get("dilemma_player_ids"))
                        dilemma_votes = []
                        if dilemma_entry.get("dilemma_votes") is not None:
                            for dilemma_vote_entry in dilemma_entry.get("dilemma_votes"):
                                player_id = dilemma_vote_entry.get("player_id")
                                choice = dilemma_vote_entry.get("choice")
                                timestamp = dilemma_vote_entry.get("timestamp")
                                dilemma_votes.append(Vote(player_id=player_id,
                                                          choice=choice,
                                                          timestamp=timestamp))
                        round_dilemmas.append(Dilemma(dilemma_name=dilemma_name,
                                                      dilemma_channel_id=dilemma_channel_id,
                                                      dilemma_message_id=dilemma_message_id,
                                                      dilemma_player_ids=dilemma_player_ids,
                                                      dilemma_choices=dilemma_choices,
                                                      dilemma_votes=dilemma_votes,
                                                      is_active_dilemma=is_active_dilemma))
                rounds.append(Round(round_number=round_num,
                                    round_channel_id=round_channel_id,
                                    round_message_id=round_message_id,
                                    round_dilemmas=round_dilemmas,
                                    is_active_round=is_active_round,
                                    votes=votes))
        if json_object.get("parties") is not None:
            for party_entry in json_object.get("parties"):
                channel_id = party_entry.get("channel_id")
                max_size = party_entry.get("max_size")
                party_name = party_entry.get("party_name")
                player_ids = set(party_entry.get("player_ids"))
                parties.append(Party(player_ids=player_ids,
                                     party_name=party_name,
                                     channel_id=channel_id,
                                     max_size=max_size))
        if json_object.get("actions") is not None:
            for action_entry in json_object.get("actions"):
                action_name = action_entry.get("name")
                action_desc = action_entry.get("desc")
                action_uses = action_entry.get("uses")
                action_timing = action_entry.get("timing")
                actions.append(Action(name=action_name,
                                      desc=action_desc,
                                      uses=action_uses,
                                      timing=action_timing))
        if json_object.get("items") is not None:
            for item_entry in json_object.get("items"):
                item_name = item_entry.get("item_name")
                item_desc = item_entry.get("item_desc")
                item_action: Optional[Action] = None
                if item_entry.get("item_action") is not None:
                    item_action_entry = item_entry.get("item_action")
                    item_action_name = item_action_entry.get("name")
                    item_action_desc = item_action_entry.get("desc")
                    item_action_timing = item_action_entry.get("timing")
                    item_action_uses = item_action_entry.get("uses")
                    item_action = Action(name=item_action_name,
                                         desc=item_action_desc,
                                         uses=item_action_uses,
                                         timing=item_action_timing)
                items.append(Item(item_name=item_name,
                                  item_desc=item_desc,
                                  item_action=item_action))
        return Game(is_active=is_active,
                    parties_locked=parties_locked,
                    voting_locked=voting_locked,
                    items_locked=items_locked,
                    players=players,
                    rounds=rounds,
                    parties=parties,
                    actions=actions,
                    items=items)


def write_dom_to_json(game: Game):
    millis_prefix = round(time.time() * 1000)
    filepath_final = f'{Conf.BASE_PATH}/{Conf.GAME_FILE}'
    filepath_temp = f'{Conf.BASE_PATH}/{millis_prefix}_{Conf.GAME_FILE}'

    with open(filepath_temp, 'w', encoding="utf8") as outfile:

        # convert Game to dictionary here
        game_dict = {"is_active": game.is_active,
                     "parties_locked": game.parties_locked,
                     "voting_locked": game.voting_locked,
                     "items_locked": game.items_locked}
        player_dicts = []
        for player in game.players:
            attribute_dicts = []
            for attribute in player.player_attributes:
                attribute_dicts.append({"name": attribute.name,
                                        "level": attribute.level,
                                        "max_level": attribute.max_level})
            player_action_dicts = []
            for action in player.player_actions:
                player_action_dicts.append({"name": action.name,
                                            "desc": action.desc,
                                            "uses": action.uses,
                                            "timing": action.timing})
            player_item_dicts = []
            for item in player.player_items:
                item_action_dict = {}
                if item.item_action is not None:
                    item_action: Action = item.item_action
                    item_action_dict = {"name": item_action.name,
                                        "desc": item_action.desc,
                                        "uses": item_action.uses,
                                        "timing": item_action.timing}
                player_item_dicts.append({"item_name": item.item_name,
                                          "item_desc": item.item_descr,
                                          "item_action": item_action_dict})
            player_dicts.append({"player_id": player.player_id,
                                 "player_discord_name": player.player_discord_name,
                                 "player_mod_channel": player.player_mod_channel,
                                 "player_attributes": attribute_dicts,
                                 "player_actions": player_action_dicts,
                                 "player_items": player_item_dicts,
                                 "is_dead": player.is_dead
                                 })
        game_dict["players"] = player_dicts
        round_dicts = []
        for a_round in game.rounds:
            vote_dicts = []
            dilemma_dicts = []
            for vote in a_round.votes:
                vote_dicts.append({"player_id": vote.player_id,
                                   "choice": vote.choice,
                                   "timestamp": vote.timestamp})
            for a_dilemma in a_round.round_dilemmas:
                dilemma_vote_dicts = []
                for dilemma_vote in a_dilemma.dilemma_votes:
                    dilemma_vote_dicts.append({"player_id": dilemma_vote.player_id,
                                               "choice": dilemma_vote.choice,
                                               "timestamp": dilemma_vote.timestamp})
                dilemma_dicts.append({"dilemma_name": a_dilemma.dilemma_name,
                                      "dilemma_channel_id": a_dilemma.dilemma_channel_id,
                                      "dilemma_message_id": a_dilemma.dilemma_message_id,
                                      "dilemma_player_ids": list(a_dilemma.dilemma_player_ids),
                                      "dilemma_choices": list(a_dilemma.dilemma_choices),
                                      "dilemma_votes": dilemma_vote_dicts,
                                      "is_active_dilemma": a_dilemma.is_active_dilemma})
            round_dicts.append({"round_number": a_round.round_number,
                                "round_channel_id": a_round.round_channel_id,
                                "round_message_id": a_round.round_message_id,
                                "is_active_round": a_round.is_active_round,
                                "votes": vote_dicts,
                                "round_dilemmas": dilemma_dicts})
        game_dict["rounds"] = round_dicts
        party_dicts = []
        for a_party in game.parties:
            party_dicts.append({"player_ids": list(a_party.player_ids),
                                "party_name": a_party.party_name,
                                "channel_id": a_party.channel_id,
                                "max_size": a_party.max_size})
        game_dict["parties"] = party_dicts
        action_dicts = []
        for action in game.actions:
            action_dicts.append({"name": action.name,
                                 "desc": action.desc,
                                 "uses": action.uses,
                                 "timing": action.timing})
        game_dict["actions"] = action_dicts
        item_dicts = []
        for item in game.items:
            item_action_dict = {}
            if item.item_action is not None:
                item_action: Action = item.item_action
                item_action_dict = {"name": item_action.name,
                                    "desc": item_action.desc,
                                    "uses": item_action.uses,
                                    "timing": item_action.timing}
            item_dicts.append({"item_name": item.item_name,
                               "item_desc": item.item_descr,
                               "item_action": item_action_dict})
        game_dict["items"] = item_dicts
        json.dump(game_dict, outfile, indent=2, ensure_ascii=False)
        outfile.close()

        if os.path.isfile(filepath_final):
            os.remove(filepath_final)
        os.rename(filepath_temp, filepath_final)

        logger.info(f'Wrote game data to {filepath_final}')


async def get_game(file_path: str) -> Game:
    logger.info(f'Grabbing game info from {file_path}')
    return read_json_to_dom(filepath=file_path)


async def write_game(game: Game):
    write_dom_to_json(game=game)


async def read_players_file(file_path: str, game_actions: Dict[str, Action] = None, game_items: Dict[str, Item] = None) -> List[Player]:
    if game_actions is None:
        game_actions = {}
    if game_items is None:
        game_items = {}

    players = []

    rows: List[Dict] = await read_csv_file(file_path=file_path)

    for row in rows:
        player_id = int(row['player_id'])
        player_discord_name = row['name']
        player_mod_channel = int(row['mod_channel']) if 'mod_channel' in row and row['mod_channel'] else None
        player_attributes_str = row['attributes'] if 'attributes' in row else None
        player_resources_str = row['resources'] if 'resources' in row else None
        player_actions_str = row['actions'] if 'actions' in row else None
        player_items_str = row['items'] if 'items' in row else None

        player_attributes: List[Attribute] = []
        player_resources: List[Resource] = []
        player_actions: List[Action] = []
        player_items: List[Item] = []

        if player_resources_str is not None:
            player_resources_list = list(filter(None, player_resources_str.split(';')))
            for player_resource in player_resources_list:
                player_resource_split = player_resource.split(':')
                # TODO: this when attributes are defined

        if player_attributes_str is not None:
            player_attributes_list = list(filter(None, player_attributes_str.split(';')))
            for player_attribute in player_attributes_list:
                player_attribute_split = player_attribute.split(':')
                # TODO: this when attributes are defined

        if player_actions_str is not None:
            player_action_name_list = list(filter(None, player_actions_str.split(';')))
            for player_action_name in player_action_name_list:
                if player_action_name in game_actions:
                    player_actions.append(game_actions[player_action_name])

        if player_items_str is not None:
            player_item_name_list = list(filter(None, player_items_str.split(';')))
            for player_item_name in player_item_name_list:
                if player_item_name in game_items:
                    player_items.append(game_items[player_item_name])

        players.append(Player(player_id=player_id,
                              player_discord_name=player_discord_name,
                              player_mod_channel=player_mod_channel,
                              player_attributes=player_attributes,
                              player_actions=player_actions,
                              player_items=player_items,
                              is_dead=False))

    return players


async def read_parties_file(file_path: str) -> List[Party]:
    parties = []

    rows: List[Dict] = await read_csv_file(file_path=file_path)

    for row in rows:
        player_ids = set(map(int, list(filter(None, row['player_ids'].split(';'))))) if row['player_ids'] else []
        party_name = row['name']
        max_size = int(row['max_size']) if 'max_size' in row and row['max_size'] else None
        channel_id = int(row['channel_id']) if 'channel_id' in row and row['channel_id'] else None
        parties.append(Party(player_ids=player_ids,
                             party_name=party_name,
                             max_size=max_size,
                             channel_id=channel_id))
    return parties


async def read_actions_file(file_path: str) -> List[Action]:
    actions = []

    rows: List[Dict] = await read_csv_file(file_path=file_path)

    for row in rows:
        action_name = row['name']
        action_timing = row['timing'] if 'timing' in row else None
        action_uses = row['uses'] if 'uses' in row else None
        action_desc = row['desc']
        actions.append(Action(name=action_name,
                              timing=action_timing,
                              desc=action_desc,
                              uses=action_uses))

    return actions


async def read_items_file(file_path: str, game_actions: Dict[str, Action] = None) -> List[Item]:
    if game_actions is None:
        game_actions = {}
    items = []

    rows: List[Dict] = await read_csv_file(file_path=file_path)

    for row in rows:
        item_name = row['name']
        item_desc = row['desc']
        item_action_name = row['action_name'] if 'action_name' in row else None

        item_action: Optional[Action] = None
        if item_action_name is not None and item_action_name in game_actions:
            item_action = game_actions[item_action_name]

        items.append(Item(item_name=item_name,
                          item_desc=item_desc,
                          item_action=item_action))

    return items


async def read_csv_file(file_path: str) -> List[Dict]:
    rows: List[Dict] = []
    with open(file_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)

        for row in map(dict, reader):
            rows.append(row)

    return rows
