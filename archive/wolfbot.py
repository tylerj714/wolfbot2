# wolfbot.py
import os
import discord
from dotenv import load_dotenv
from discord import app_commands, User
from typing import List, Optional, Literal
import game_manager
from game_manager import Game, Player, Round, Vote, Party, Dilemma
from logging_manager import logger
import time
import random
import string
import game_configurations

load_dotenv()
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


class WolfBotClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=GUILD_ID))
            self.synced = True
        print(f"We have logged in as {self.user}.")


client = WolfBotClient()
tree = app_commands.CommandTree(client)

async def player_list_autocomplete(interaction: discord.Interaction,
                                   current: str) -> List[app_commands.Choice[str]]:
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')
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
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')
    parties = await get_valid_parties(current, game.parties)
    return [
        app_commands.Choice(name=f'{party.party_name} ({len(party.player_ids)}/{party.max_size})', value=str(party.channel_id))
        for party in parties
    ]


async def get_valid_parties(substr: str, parties: List[Party]) -> List[Party]:
    party_list = []
    for party in sorted(parties, key=lambda e: e.party_name.lower()):
        if substr and substr.lower() not in party.party_name.lower():
            continue
        # if not len(party.player_ids) >= party.max_size:
        party_list.append(party)
    return party_list[:25]


async def dilemma_choice_autocomplete(interaction: discord.Interaction,
                                      current: str) -> List[app_commands.Choice[str]]:
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')
    dilemma_choices = await get_valid_dilemma_choices(current, game, interaction.user)
    return [
        app_commands.Choice(name=choice, value=choice)
        for choice in dilemma_choices
    ]

async def get_valid_dilemma_choices(substr: str, game: Game, user: User) -> List[str]:
    choice_list = []
    game_round = game.get_latest_round
    if game_round is not None:
        round_dilemma = game_round.get_player_dilemma(user.id)
        if round_dilemma is not None:
            for dilemma_choice in round_dilemma.dilemma_choices:
                choice_list.append(dilemma_choice)
    return choice_list[:25]

@tree.command(name="toggle-activity",
              description="Enables/Disables bot commands for players",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def toggle_activity(interaction: discord.Interaction,
                          active: Literal['True', 'False']):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    game.is_active = True if active == 'True' else False

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'Game state has been set to {active}!', ephemeral=True)

@tree.command(name="clear-messages",
              description="Clears up to 100 messages out of a discord channel",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def clear_messages(interaction: discord.Interaction,
                         channel: discord.TextChannel,
                         channel_again: discord.TextChannel):
    log_interaction_call(interaction)

    if channel != channel_again:
        await interaction.response.send_message(f"Both channel arguments must be the same! This is a safety feature!")

    await interaction.response.send_message(f"Clearing messages from channel {channel.name}")
    await channel.purge(limit=100)


@tree.command(name="add-player",
              description="Adds a player to the game, creating a private moderator channel for them in the process.",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def add_player(interaction: discord.Interaction,
                     player: discord.Member,
                     channel_name: str):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    if game.get_player(player.id) is None:

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            player: discord.PermissionOverwrite(read_messages=True)
        }

        category_channel = await interaction.guild.fetch_channel(MOD_CATEGORY)
        mod_channel = await interaction.guild.create_text_channel(name=channel_name, overwrites=overwrites, category=category_channel)

        new_player = Player(player_id=player.id,
                            player_discord_name=player.name,
                            player_mod_channel=mod_channel.id,
                            player_attributes=[],
                            player_actions=[])
        game.add_player(new_player)
        await game_manager.write_game(game=game, file_path=GAME_PATH)
        await interaction.response.send_message(f'Added player {player.name} to game!', ephemeral=True)
    else:
        await interaction.response.send_message(f'Failed to add {player.name} to game!', ephemeral=True)


@tree.command(name="start-round",
              description="Creates and enables the current round, if possible",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def start_round(interaction: discord.Interaction):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    latest_round = game.get_latest_round()

    if latest_round is None:
        new_round = Round(votes=[], round_number=1, is_active_round=True)
        game.add_round(new_round)
    elif latest_round.is_active_round:
        await interaction.response.send_message(f'There is already an active round; you must end the existing round first before creating another', ephemeral=True)
        return
    else:
        new_round = Round(votes=[], round_number=latest_round.round_number + 1, is_active_round=True)
        game.add_round(new_round)

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'Created round {new_round.round_number}!', ephemeral=True)


@tree.command(name="end-round",
              description="Ends the current round, if possible",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def end_round(interaction: discord.Interaction):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    latest_round = game.get_latest_round()

    if latest_round is None:
        await interaction.response.send_message(f'There is not currently an active round to end!', ephemeral=True)
        return
    else:
        latest_round.is_active_round = False

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'Ended round {latest_round.round_number}!', ephemeral=True)


@tree.command(name="create-dilemma",
              description="Creates and enables a dilemma for the current round, if possible",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def create_dilemma(interaction: discord.Interaction,
                         dilemma_name: str):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    latest_round = game.get_latest_round()

    if latest_round is None:
        await interaction.response.send_message(f'There is currently no active round; you must create an active round first', ephemeral=True)
    elif not latest_round.is_active_round:
        await interaction.response.send_message(f'The most recent round is not currently active; the current round must be active to create a dilemma!', ephemeral=True)
        return
    else:
        new_dilemma = Dilemma(dilemma_votes=[], dilemma_id = dilemma_name, dilemma_player_ids=[], dilemma_choices=[], is_active_dilemma=False)
        latest_round.add_dilemma(new_dilemma)

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'Created dilemma {new_dilemma.dilemma_id} for round {latest_round.round_number}!', ephemeral=True)


@tree.command(name="update-dilemma-player",
              description="Adds or removes a player from a selected dilemma",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def update_dilemma_player(interaction: discord.Interaction,
                         dilemma_name: str):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    latest_round = game.get_latest_round()

    if latest_round is None:
        await interaction.response.send_message(f'There is currently no active round; you must create an active round first', ephemeral=True)
    elif not latest_round.is_active_round:
        await interaction.response.send_message(f'The most recent round is not currently active; the current round must be active to create a dilemma!', ephemeral=True)
        return
    else:
        new_dilemma = Dilemma(dilemma_votes=[], dilemma_id = dilemma_name, dilemma_player_ids=[], dilemma_choices=[], is_active_dilemma=False)
        latest_round.add_dilemma(new_dilemma)

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'Created dilemma {new_dilemma.dilemma_id} for round {latest_round.round_number}!', ephemeral=True)


@tree.command(name="update-dilemma-choices",
              description="Adds or Removes a choice to a selected dilemma",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def update_dilemma_choices(interaction: discord.Interaction,
                         dilemma_name: str):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    latest_round = game.get_latest_round()

    if latest_round is None:
        await interaction.response.send_message(f'There is currently no active round; you must create an active round first', ephemeral=True)
    elif not latest_round.is_active_round:
        await interaction.response.send_message(f'The most recent round is not currently active; the current round must be active to create a dilemma!', ephemeral=True)
        return
    else:
        new_dilemma = Dilemma(dilemma_votes=[], dilemma_id = dilemma_name, dilemma_player_ids=[], dilemma_choices=[], is_active_dilemma=False)
        latest_round.add_dilemma(new_dilemma)

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'Created dilemma {new_dilemma.dilemma_id} for round {latest_round.round_number}!', ephemeral=True)


@tree.command(name="update-dilemma-status",
              description="Adds or Removes a choice to a selected dilemma",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def update_dilemma_choices(interaction: discord.Interaction,
                         dilemma_name: str):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    latest_round = game.get_latest_round()

    if latest_round is None:
        await interaction.response.send_message(f'There is currently no active round; you must create an active round first', ephemeral=True)
    elif not latest_round.is_active_round:
        await interaction.response.send_message(f'The most recent round is not currently active; the current round must be active to create a dilemma!', ephemeral=True)
        return
    else:
        new_dilemma = Dilemma(dilemma_votes=[], dilemma_id = dilemma_name, dilemma_player_ids=[], dilemma_choices=[], is_active_dilemma=False)
        latest_round.add_dilemma(new_dilemma)

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'Created dilemma {new_dilemma.dilemma_id} for round {latest_round.round_number}!', ephemeral=True)


@tree.command(name="kill-player",
              description="Toggles a player status of being dead or not.",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
@app_commands.autocomplete(player=player_list_autocomplete)
async def kill_player(interaction: discord.Interaction,
                      player: str,
                      dead: Literal['True', 'False']):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    this_player = game.get_player(int(player))
    if this_player is None:
        await interaction.response.send_message(f'The selected player is not currently defined in this game!', ephemeral=True)
    else:
        this_player.is_dead = True if dead == 'True' else False

        await game_manager.write_game(game=game, file_path=GAME_PATH)
        await interaction.response.send_message(f'Set alive status of {this_player.player_discord_name} to {dead}!', ephemeral=True)


@tree.command(name="vote-player",
              description="Votes for a particular player",
              guild=discord.Object(id=GUILD_ID))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
@app_commands.autocomplete(player=player_list_autocomplete)
async def vote_player(interaction: discord.Interaction,
                      player: Optional[str] = None,
                      other: Optional[Literal['No Vote', 'Unvote']] = None):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    if not game.is_active:
        await interaction.response.send_message(f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
        return

    if player is not None and other is not None:
        await interaction.response.send_message(f'You may select only one of the arguments player or other, you cannot select both. Please resubmit your vote.', ephemeral=True)
        return

    latest_round = game.get_latest_round()
    if latest_round is None or not latest_round.is_active_round:
        await interaction.response.send_message(f'No currently active round found for this game!', ephemeral=True)
        return

    requesting_player = game.get_player(interaction.user.id)
    if requesting_player is None or requesting_player.is_dead:
        await interaction.response.send_message(f'Player {interaction.user.name} was not found in this game!', ephemeral=True)
        return

    if player is not None and player not in game.get_living_player_ids():
        await interaction.response.send_message(f'Invalid player selection! Please resubmit your vote.', ephemeral=True)
        return

    voted_player = None if player is None else game.get_player(int(player))

    if voted_player is not None and voted_player.is_dead:
        await interaction.response.send_message(f'Player {voted_player.player_discord_name} is dead and cannot be voted!', ephemeral=True)
        return

    if voted_player is None and other is None:
        await interaction.response.send_message(f'Player {player.name} was not found in this game!', ephemeral=True)
        return
    else:
        round_current_player_vote = latest_round.get_player_vote(requesting_player.player_id)

        if voted_player is None and other is not None:
            if round_current_player_vote is None and other != 'Unvote':
                latest_round.add_vote(Vote(requesting_player.player_id, other, round(time.time())))
            else:
                if other == 'Unvote':
                    latest_round.remove_vote(round_current_player_vote)
                else:
                    round_current_player_vote.choice = other
                    round_current_player_vote.timestamp = round(time.time())
        else:
            if round_current_player_vote is None:
                latest_round.add_vote(Vote(requesting_player.player_id, str(voted_player.player_id), round(time.time())))
            else:
                round_current_player_vote.choice = str(voted_player.player_id)
                round_current_player_vote.timestamp = round(time.time())

        await game_manager.write_game(game=game, file_path=GAME_PATH)

        if voted_player is not None:
            success_vote_target = voted_player.player_discord_name
        else:
            success_vote_target = other
        await interaction.response.send_message(f'Registered vote for {success_vote_target}!', ephemeral=True)

        vote_channel = interaction.guild.get_channel(VOTE_CHANNEL)

        response_value = voted_player.player_discord_name if voted_player is not None else other

        if vote_channel is not None:
            await interaction.followup.send(f'Sending public vote announcement in channel #{vote_channel}', ephemeral=True)
            await vote_channel.send(f'Player **{requesting_player.player_discord_name}** has submitted a vote for **{response_value}**')
        else:
            await interaction.followup.send(f'Sending public vote results now...', ephemeral=True)
            await interaction.followup.send(f'Player **{requesting_player.player_discord_name}** has submitted a vote for **{response_value}**', ephemeral=False)

@tree.command(name="vote-report",
              description="Generates a report of current voting totals",
              guild=discord.Object(id=GUILD_ID))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
async def vote_report(interaction: discord.Interaction,
                      for_round: Optional[app_commands.Range[int, 0, 20]] = None,
                      with_history: Optional[Literal['Yes', 'No']] = 'No'):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    if not game.is_active:
        await interaction.response.send_message(f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
        return

    if for_round is None:
        report_round = game.get_latest_round()
    else:
        report_round = game.get_round(for_round)

    if report_round is None:
        await interaction.response.send_message(f'No active or matching round found for this game!', ephemeral=True)
        return

    vote_dict = {}

    for vote in report_round.votes:
        if vote.choice in vote_dict.keys():
            vote_dict.get(vote.choice).append(vote.player_id)
        else:
            vote_dict[vote.choice] = [vote.player_id]

    formatted_votes = f"**Vote Totals for round {report_round.round_number} as of <t:{int(time.time())}>**\n"
    formatted_votes += "```\n"
    for key, value in sorted(vote_dict.items(), key=lambda e: len(e[1]), reverse=True):
        if key == 'No Vote':
            formatted_votee = key
        else:
            formatted_votee = game.get_player(int(key)).player_discord_name
        formatted_votes += f"{formatted_votee}: {len(value)} vote(s)\n"
        formatted_votes += f"    Voted By: "
        for player_id in value:
            formatted_voter = game.get_player(int(player_id)).player_discord_name
            formatted_votes += f"{formatted_voter}, "
        formatted_votes = formatted_votes.rstrip(', ')
        formatted_votes += "\n"
    formatted_votes += "```\n"

    vote_channel = interaction.guild.get_channel(VOTE_CHANNEL)

    if vote_channel is not None:
        await interaction.response.send_message(f'Sending query response in channel ', ephemeral=True)
        await vote_channel.send(formatted_votes)
    else:
        await interaction.response.send_message(f'Sending vote results now...', ephemeral=True)
        await interaction.followup.send(formatted_votes, ephemeral=False)

    #With History to-be-implemented

@tree.command(name="open-private-chat",
              description="Opens a private chat with the chosen player",
              guild=discord.Object(id=GUILD_ID))
@app_commands.autocomplete(player=player_list_autocomplete)
async def open_private_chat(interaction: discord.Interaction,
                    player: Optional[str] = None):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    guild = interaction.guild
    discord_user1 = interaction.user
    player2 = game.get_player(int(player))
    discord_user2 = await guild.fetch_member(player2.player_id)
    channel_identifier = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    category_channel = await guild.fetch_channel(PRIVATE_CHAT_CATEGORY)

    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        discord_user1: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        discord_user2: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    private_channel = await guild.create_text_channel(name=f'private-chat-{channel_identifier}', overwrites=overwrites, category=category_channel)
    await interaction.response.send_message(f'Created private channel with player {player2.player_discord_name}')
    await private_channel.send(f'Your private chat between {discord_user1.mention} and {discord_user2.mention} has begun!')


@tree.command(name="create-party",
              description="Creates a player party group",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def create_party(interaction: discord.Interaction,
                       party_name: str,
                       party_max_size: int):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    guild = interaction.guild
    category_channel = await guild.fetch_channel(PRIVATE_CHAT_CATEGORY)

    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False)
    }

    party_channel = await guild.create_text_channel(name=f'party-{party_name}', overwrites=overwrites, category=category_channel)

    party = Party(player_ids=[], max_size=party_max_size, channel_id=party_channel.id, party_name=party_name)
    game.add_party(party)

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'Created new party {party_name}!', ephemeral=True)


@tree.command(name="add-party-player",
              description="Adds a player to a party and manages text channel permissions",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
@app_commands.autocomplete(player=player_list_autocomplete)
@app_commands.autocomplete(party=party_list_autocomplete)
async def add_party_player(interaction: discord.Interaction,
                           party: str,
                           player: str):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    game_party = game.get_party(int(party))
    game_player = game.get_player(int(player))

    if game_party is None:
        await interaction.response.send_message(f'Could not find a party with that identifier!', ephemeral=True)
        return

    if game_player is None:
        await interaction.response.send_message(f'Could not find a player with that identifier!', ephemeral=True)
        return

    if len(game_party.player_ids) >= game_party.max_size:
        await interaction.response.send_message(f'Party size is already at max size of {game_party.max_size}!', ephemeral=True)
        return

    guild = interaction.guild
    party_channel = await guild.fetch_channel(game_party.channel_id)
    player_user = await guild.fetch_member(game_player.player_id)

    existing_party = game.get_player_party(game_player)

    if existing_party is not None:
        existing_party_channel = await guild.fetch_channel(existing_party.channel_id)
        await existing_party_channel.set_permissions(player_user, read_messages=False, send_messages=False, read_message_history=False)
        await existing_party_channel.send(f'**{game_player.player_discord_name}** has left the party!')
        existing_party.remove_player(game_player)

    game_party.add_player(game_player)

    await party_channel.set_permissions(player_user, read_messages=True, send_messages=True, read_message_history=True)

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'Added player {game_player.player_discord_name} to party {game_party.party_name}!', ephemeral=True)
    await party_channel.send(f'**{game_player.player_discord_name}** has joined the party!')


@tree.command(name="remove-party-player",
              description="Removes a player from a party and manages text channel permissions",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
@app_commands.autocomplete(player=player_list_autocomplete)
async def remove_party_player(interaction: discord.Interaction,
                              player: str):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    game_player = game.get_player(int(player))

    if game_player is None:
        await interaction.response.send_message(f'Could not find a player with that identifier!', ephemeral=True)
        return

    game_party = game.get_player_party(game_player)

    if game_party is None:
        await interaction.response.send_message(f'Player {game_player.player_discord_name} is not a member of any current party!', ephemeral=True)
        return

    guild = interaction.guild
    party_channel = await guild.fetch_channel(game_party.channel_id)
    player_user = await guild.fetch_member(game_player.player_id)

    game_party.remove_player(game_player)

    await party_channel.set_permissions(player_user, read_messages=False, send_messages=False, read_message_history=False)

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'Removed player {game_player.player_discord_name} from party {game_party.party_name}!', ephemeral=True)
    await party_channel.send(f'**{game_player.player_discord_name}** has left the party!')


@tree.command(name="join-party",
              description="Allows a player to join a party and manages text channel permissions",
              guild=discord.Object(id=GUILD_ID))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
@app_commands.autocomplete(party=party_list_autocomplete)
async def join_party(interaction: discord.Interaction,
                     party: str):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    game_party = game.get_party(int(party))
    game_player = game.get_player(interaction.user.id)

    if game_party is None:
        await interaction.response.send_message(f'Could not find a party with that identifier!', ephemeral=True)
        return

    if game_player is None:
        await interaction.response.send_message(f'You are not a registered player of the current game!', ephemeral=True)
        return
    if game_player.is_dead:
        await interaction.response.send_message(f'You are dead! Begone apparition!', ephemeral=True)

    if len(game_party.player_ids) >= game_party.max_size:
        await interaction.response.send_message(f'Party size is already at max size of {game_party.max_size}!', ephemeral=True)
        return

    guild = interaction.guild
    party_channel = await guild.fetch_channel(game_party.channel_id)
    player_user = await guild.fetch_member(game_player.player_id)
    existing_party = game.get_player_party(game_player)

    if existing_party is not None:
        existing_party_channel = await guild.fetch_channel(existing_party.channel_id)
        await existing_party_channel.set_permissions(player_user, read_messages=False, send_messages=False, read_message_history=False)
        await existing_party_channel.send(f'**{game_player.player_discord_name}** has left the party!')
        existing_party.remove_player(game_player)

    game_party.add_player(game_player)

    await party_channel.set_permissions(player_user, read_messages=True, send_messages=True, read_message_history=True)

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'You have joined the party {game_party.party_name}!', ephemeral=True)
    await party_channel.send(f'**{game_player.player_discord_name}** has joined the party!')


@tree.command(name="leave-party",
              description="Allows a player to leave a party and manages text channel permissions",
              guild=discord.Object(id=GUILD_ID))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
async def leave_party(interaction: discord.Interaction):
    log_interaction_call(interaction)
    game = await game_manager.get_game(file_path=f'{BASE_PATH}/{GAME_FILE}')

    game_player = game.get_player(interaction.user.id)

    if game_player is None:
        await interaction.response.send_message(f'You are not a registered player of the current game!')
        return
    if game_player.is_dead:
        await interaction.response.send_message(f'You are dead! Begone apparition!')

    game_party = game.get_player_party(game_player)

    if game_party is None:
        await interaction.response.send_message(f'You are not currently a member of any party!')
        return

    guild = interaction.guild
    party_channel = await guild.fetch_channel(game_party.channel_id)
    player_user = await guild.fetch_member(game_player.player_id)

    game_party.remove_player(game_player)

    await party_channel.set_permissions(player_user, read_messages=False, send_messages=False, read_message_history=False)

    await game_manager.write_game(game=game, file_path=GAME_PATH)
    await interaction.response.send_message(f'You have left the party {game_party.party_name}!')
    await party_channel.send(f'**{game_player.player_discord_name}** has left the party!')


@tree.command(name="roll-dice",
              description="Rolls one or more dice with a specified number of sides",
              guild=discord.Object(id=GUILD_ID))
@app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
async def roll_dice(interaction: discord.Interaction,
                      dice_to_roll: Literal[1, 2, 3, 4, 5],
                      die_faces: Literal[2, 4, 6, 8, 10, 12, 20]):
    log_interaction_call(interaction)

    roll_values = []

    for x in range(0, dice_to_roll):
        roll_values.append(random.randint(1, die_faces))

    roll_values.sort()

    roll_val_str = ', '.join(map(str, roll_values))

    roll_message = f'Rolling {dice_to_roll} d{die_faces}...'
    result_message = f'Rolled values: {roll_val_str}'

    await interaction.response.send_message(roll_message, ephemeral=False)
    await interaction.followup.send(result_message, ephemeral=False)


# @tree.command(name="action-success-roll",
#               description="Computes success and dice roll result for an action",
#               guild=discord.Object(id=GUILD_ID))
# @app_commands.default_permissions(manage_guild=True)
# async def action_success_roll(interaction: discord.Interaction,
#                           source_skill_level: app_commands.Range[int, 0, 100],
#                           target_skill_level: app_commands.Range[int, 0, 100],
#                           with_modifier: Optional[Literal[True, False]]):
#     await interaction.response.send_message("Not implemented yet!")
#
# @tree.command(name="action-result-roll",
#               description="Computes value of one or more dice rolls",
#               guild=discord.Object(id=GUILD_ID))
# @app_commands.default_permissions(manage_guild=True)
# async def action_result_roll(interaction: discord.Interaction,
#                              base_source_value: app_commands.Range[int, 0, 20],
#                              base_target_reduction: app_commands.Range[int, 0, 20],
#                              d1_faces: Literal[2,4,6,8,10,12,20],
#                              d1_to_roll: app_commands.Range[int, 1, 5],
#                              d1_target_resistance: Optional[app_commands.Range[0,10]] = 0,
#                              d2_faces: Optional[Literal[2,4,6,8,10,12,20]] = 4,
#                              d2_to_roll: Optional[app_commands.Range[int, 0, 5]] = 0,
#                              d2_target_resistance: Optional[app_commands.Range[0,10]] = 0):
#     await interaction.response.send_message("Not implemented yet!")


@tree.command(name="cycle-game-conf",
              description="Reads and then writes the game conf",
              guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_guild=True)
async def toggle_activity(interaction: discord.Interaction):
    log_interaction_call(interaction)
    game_conf = await game_configurations.get_game_conf(file_path=GAME_CONF_PATH)

    await game_configurations.write_game_conf(game_conf=game_conf, file_path=GAME_CONF_PATH)
    await interaction.response.send_message(f'Game Configuration has been updated!', ephemeral=True)


@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Cooldown is in force, please wait for {round(error.retry_after)} seconds", ephemeral=True)
    else:
        raise error


def log_interaction_call(interaction: discord.Interaction):
    logger.info(f'Received command {interaction.command.name} with parameters {interaction.data} initiated by user {interaction.user.name}')


client.run(TOKEN)
