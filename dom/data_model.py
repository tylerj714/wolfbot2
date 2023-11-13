#! game_manager.py
# a class for managing game state details
import json
from typing import Optional, List, Dict
from archive.logging_manager import logger


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


class Item:
    def __init__(self, item_name: str, item_action: Action, item_desc: str, item_uses: int, item_image: str):
        self.item_name = item_name,
        self.item_action = item_action,
        self.item_descr = item_desc,
        self.item_uses = item_uses,
        self.item_image = item_image


class Player:
    def __init__(self, player_id: int, player_discord_name: str, player_mod_channel: int,
                 player_attributes: List[Attribute],
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


class Dilemma:
    def __init__(self, dilemma_votes: List[Vote], dilemma_id: str, dilemma_player_ids: [int], dilemma_choices: [str], is_active_dilemma: bool):
        self.dilemma_votes = dilemma_votes
        self.dilemma_id = dilemma_id
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


class Party:
    def __init__(self, player_ids: List[int], party_name: str, max_size: int, channel_id: int):
        self.player_ids = player_ids
        self.channel_id = channel_id
        self.party_name = party_name
        self.max_size = max_size

    def add_player(self, player: Player):
        self.player_ids.append(player.player_id)

    def remove_player(self, player: Player):
        self.player_ids.remove(player.player_id)


class Round:
    def __init__(self, votes: List[Vote], round_number: int, round_dilemmas: [Dilemma], is_active_round: bool):
        self.votes = votes
        self.round_dilemmas = round_dilemmas
        self.round_number = round_number
        self.is_active_round = is_active_round

    def get_player_dilemma(self, player_id: int) -> Optional[Dilemma]:
        player_dilemma = None
        for dilemma in self.round_dilemmas:
            if player_id in dilemma.dilemma_player_ids:
                player_dilemma = dilemma
        return player_dilemma

    def add_dilemma(self, dilemma: Dilemma):
        self.round_dilemmas.append(dilemma)

    def close_dilemmas(self):
        for dilemma in self.round_dilemmas:
            dilemma.is_active_dilemma = False

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
    def __init__(self, is_active: bool, players: List[Player], parties: List[Party], rounds: List[Round]):
        self.is_active = is_active
        self.players = players
        self.rounds = rounds
        self.parties = parties

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


def read_json_to_dom(filepath: str) -> Game:
    with open(filepath, 'r', encoding="utf8") as openfile:
        json_object = json.load(openfile)

        is_active = json_object.get("is_active")
        players = []
        rounds = []
        parties = []
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
                for dilemma_entry in json_object.get("dilemmas"):
                    dilemma_id = dilemma_entry.get("dilemma_id")
                    is_active_dilemma = dilemma_entry.get("is_active_dilemma")
                    dilemma_choices = dilemma_entry.get("dilemma_choices")
                    dilemma_votes = []
                    dilemma_player_ids = []
                    if dilemma_entry.get("dilemma_player_ids") is not None:
                        for player_id in dilemma_entry.get("dilemma_player_ids"):
                            dilemma_player_ids.append(player_id)
                    if dilemma_entry.get("votes") is not None:
                        for dilemma_vote_entry in dilemma_entry.get("votes"):
                            player_id = dilemma_vote_entry.get("player_id")
                            choice = dilemma_vote_entry.get("choice")
                            timestamp = dilemma_vote_entry.get("timestamp")
                            dilemma_votes.append(Vote(player_id=player_id,
                                                      choice=choice,
                                                      timestamp=timestamp))
                    round_dilemmas.append(Dilemma(dilemma_id=dilemma_id,
                                                  dilemma_player_ids=dilemma_player_ids,
                                                  dilemma_choices=dilemma_choices,
                                                  dilemma_votes=dilemma_votes,
                                                  is_active_dilemma=is_active_dilemma))
                rounds.append(Round(round_number=round_num,
                                    round_dilemmas=round_dilemmas,
                                    is_active_round=is_active_round,
                                    votes=votes))
        if json_object.get("parties") is not None:
            for party_entry in json_object.get("parties"):
                channel_id = party_entry.get("channel_id")
                max_size = party_entry.get("max_size")
                party_name = party_entry.get("party_name")
                player_ids = []
                if party_entry.get("player_ids") is not None:
                    for player_id in party_entry.get("player_ids"):
                        player_ids.append(player_id)
                parties.append(Party(player_ids=player_ids,
                                     party_name=party_name,
                                     channel_id=channel_id,
                                     max_size=max_size))

        return Game(is_active=is_active,
                    players=players,
                    rounds=rounds,
                    parties=parties)


def write_dom_to_json(game: Game, filepath: str):
    with open(filepath, 'w', encoding="utf8") as outfile:

        # convert Game to dictionary here
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
            dilemma_dicts = []
            for vote in a_round.votes:
                vote_dicts.append({"player_id": vote.player_id,
                                   "choice": vote.choice,
                                   "timestamp": vote.timestamp})
            for a_dilemma in a_round.round_dilemmas:
                dilemma_id = a_dilemma.dilemma_id
                dilemma_choices = a_dilemma.dilemma_choices
                dilemma_player_ids = a_dilemma.dilemma_player_ids
                is_active_dilemma = a_dilemma.is_active_dilemma
                dilemma_vote_dicts = []
                for dilemma_vote in a_dilemma.dilemma_votes:
                    dilemma_vote_dicts.append({"player_id": dilemma_vote.player_id,
                                               "choice": dilemma_vote.choice,
                                               "timestamp": dilemma_vote.timestamp})
                dilemma_dicts.append({"dilemma_id": dilemma_id,
                                      "dilemma_player_ids": dilemma_player_ids,
                                      "dilemma_choices": dilemma_choices,
                                      "dilemma_votes": dilemma_vote_dicts,
                                      "is_active_dilemma": is_active_dilemma})
            round_dicts.append({"round_number": a_round.round_number,
                                "is_active_round": a_round.is_active_round,
                                "votes": vote_dicts,
                                "round_dilemmas": dilemma_dicts})
        game_dict["rounds"] = round_dicts
        party_dicts = []
        for a_party in game.parties:
            party_dicts.append({"player_ids": a_party.player_ids,
                                "party_name": a_party.party_name,
                                "channel_id": a_party.channel_id,
                                "max_size": a_party.max_size})
        game_dict["parties"] = party_dicts
        json.dump(game_dict, outfile, indent=2, ensure_ascii=False)


async def get_game(file_path: str) -> Game:
    logger.info(f'Grabbing game info from {file_path}')
    return read_json_to_dom(filepath=file_path)


async def write_game(game: Game, file_path: str):
    logger.info(f'Wrote game data to {file_path}')
    write_dom_to_json(game=game, filepath=file_path)
