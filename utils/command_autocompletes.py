#! command_autocompletes.py
# Utility class for managing autocomplete functionality

import discord
from discord import app_commands, Member, Guild, User
from typing import List, Optional, Literal, Dict
import dom.data_model as gdm
from dom.data_model import Game, Player, Round, Vote, Party, Dilemma
from dom.conf_vars import ConfVars as Conf


async def player_list_autocomplete(interaction: discord.Interaction,
                                   current: str) -> List[app_commands.Choice[str]]:
    game = await gdm.get_game(file_path=Conf.GAME_PATH)
    players = await get_valid_players(current, game.players)
    return [
        app_commands.Choice(name=player.player_discord_name, value=str(player.player_id))
        for player in players
    ]

async def get_valid_players(substr: str, players: List[Player]) -> List[Player]:
    player_list = []
    for player in sorted(players, key=lambda e: e.player_discord_name.lower()):
        if substr and substr.lower() not in player.player_discord_name.lower():
            continue
        if not player.is_dead:
            player_list.append(player)
    return player_list[:25]

async def party_list_autocomplete(interaction: discord.Interaction,
                                  current: str) -> List[app_commands.Choice[str]]:
    game = await gdm.get_game(file_path=Conf.GAME_PATH)
    parties = await get_valid_parties(current, game.parties)
    return [
        app_commands.Choice(name=f'{party.party_name} ({len(party.player_ids)}/{party.max_size})',
                            value=str(party.channel_id))
        for party in parties
    ]

async def get_valid_parties(substr: str, parties: List[Party]) -> List[Party]:
    party_list = []
    for party in sorted(parties, key=lambda e: e.party_name.lower()):
        if substr and substr.lower() not in party.party_name.lower():
            continue
        party_list.append(party)
    return party_list[:25]

async def dilemma_name_autocomplete(interaction: discord.Interaction,
                                    current: str) -> List[app_commands.Choice[str]]:
    game = await gdm.get_game(file_path=Conf.GAME_PATH)
    guild_member = await interaction.guild.fetch_member(interaction.user.id)
    dilemma_names = await get_valid_dilemma_names(current, game, guild_member)
    return [
        app_commands.Choice(name=dilemma_name, value=dilemma_name)
        for dilemma_name in dilemma_names
    ]

async def get_valid_dilemma_names(substr: str, game: Game, member: Member) -> List[str]:
    name_list = []
    dilemma_list = []
    game_round = game.get_latest_round()
    if game_round is not None:
        if member.guild_permissions.manage_guild:
            dilemma_list.append(game_round.round_dilemmas)
        else:
            for round_dilemma in game_round.round_dilemmas:
                if member.id in round_dilemma.dilemma_player_ids:
                    dilemma_list.append(round_dilemma)
        round_dilemmas = game_round.round_dilemmas
        for round_dilemma in round_dilemmas:
            if substr and substr.lower() not in round_dilemma.dilemma_name.lower():
                continue
            name_list.append(round_dilemma.dilemma_name)
    return name_list[:25]

async def dilemma_choice_autocomplete(interaction: discord.Interaction,
                                      current: str) -> List[app_commands.Choice[str]]:
    game = await gdm.get_game(file_path=Conf.GAME_PATH)
    dilemma_name = interaction.namespace.dilemma_name
    dilemma_choices = await get_valid_dilemma_choices(current, game, dilemma_name)
    return [
        app_commands.Choice(name=choice, value=choice)
        for choice in dilemma_choices
    ]


async def get_valid_dilemma_choices(substr: str, game: Game, dilemma_name: str) -> List[str]:
    choice_list = []
    game_round = game.get_latest_round()
    if game_round is not None:
        dilemma = game_round.get_dilemma(dilemma_name)
        for dilemma_choice in dilemma.dilemma_choices:
            if substr and substr.lower() not in dilemma_choice.lower():
                continue
            choice_list.append(dilemma_choice)
    return choice_list[:25]
