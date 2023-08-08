#! wolfbot_dom.py
# a class for managing game state details
import json
from typing import Optional, List
from datetime import datetime


class Player:
    def __init__(self, player_id: int, player_discord_name: str, is_dead: bool = False):
        self.player_id = player_id
        self.player_discord_name = player_discord_name
        self.is_dead = is_dead

    def set_assets(self, assets: int):
        self.assets = assets

class Vote:
    def __init__(self, player_id: int, choice: str, timestamp: int):
        self.player_id = player_id
        self.choice = choice
        self.timestamp = timestamp

class Round:
    def __init__(self, votes: [Vote], round_number: int, is_active_round: bool):
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
    def __init__(self, is_active: bool, players: [Player], rounds: [Round]):
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
                player_discord_name = player_entry.get("player_discord_name")
                is_dead = player_entry.get("is_dead")
                players.append(Player(player_id=player_id,
                                      player_discord_name=player_discord_name,
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
            player_dicts.append({"player_id": player.player_id,
                                 "player_discord_name": player.player_discord_name,
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
