#! voting.py
# Class with slash commands managing round and dilemma voting

import discord
from discord import app_commands
from discord.ext import commands
from dom.conf_vars import ConfVars as Conf
import dom.data_model as gdm
from typing import Optional, Literal
from dom.data_model import Round, Dilemma, Player, Vote
from bot_logging.logging_manager import log_interaction_call
from utils.command_autocompletes import player_list_autocomplete, dilemma_choice_autocomplete
import time


class VotingManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="start-round",
                          description="Creates and enables the current round, if possible")
    @app_commands.default_permissions(manage_guild=True)
    async def start_round(self,
                          interaction: discord.Interaction):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        latest_round = game.get_latest_round()

        if latest_round is None:
            new_round = Round(votes=[], round_number=1, is_active_round=True)
            game.add_round(new_round)
        elif latest_round.is_active_round:
            await interaction.response.send_message(
                f'There is already an active round; you must end the existing round first before creating another',
                ephemeral=True)
            return
        else:
            new_round = Round(votes=[], round_number=latest_round.round_number + 1, is_active_round=True)
            game.add_round(new_round)

        await gdm.write_game(game=game, file_path=Conf.GAME_PATH)
        await interaction.response.send_message(f'Created round {new_round.round_number}!', ephemeral=True)

    @app_commands.command(name="end-round",
                          description="Ends the current round, if possible")
    @app_commands.default_permissions(manage_guild=True)
    async def end_round(self,
                        interaction: discord.Interaction):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        latest_round = game.get_latest_round()

        if latest_round is None:
            await interaction.response.send_message(f'There is not currently an active round to end!', ephemeral=True)
            return
        else:
            latest_round.is_active_round = False

        await gdm.write_game(game=game, file_path=Conf.GAME_PATH)
        await interaction.response.send_message(f'Ended round {latest_round.round_number}!', ephemeral=True)

    @app_commands.command(name="create-dilemma",
                          description="Creates and enables a dilemma for the current round, if possible")
    @app_commands.default_permissions(manage_guild=True)
    async def create_dilemma(self, interaction: discord.Interaction,
                             dilemma_name: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        latest_round = game.get_latest_round()

        if latest_round is None:
            await interaction.response.send_message(
                f'There is currently no active round; you must create an active round first', ephemeral=True)
        elif not latest_round.is_active_round:
            await interaction.response.send_message(
                f'The most recent round is not currently active; the current round must be active to create a dilemma!',
                ephemeral=True)
            return
        else:
            new_dilemma = Dilemma(dilemma_votes=[], dilemma_id=dilemma_name, dilemma_player_ids=[], dilemma_choices=[],
                                  is_active_dilemma=False)
            latest_round.add_dilemma(new_dilemma)

        await gdm.write_game(game=game, file_path=Conf.GAME_PATH)
        await interaction.response.send_message(
            f'Created dilemma {new_dilemma.dilemma_id} for round {latest_round.round_number}!', ephemeral=True)

    @app_commands.command(name="update-dilemma-player",
                          description="Adds or removes a player from a selected dilemma")
    @app_commands.default_permissions(manage_guild=True)
    async def update_dilemma_player(self, interaction: discord.Interaction,
                                    dilemma_name: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        latest_round = game.get_latest_round()

        if latest_round is None:
            await interaction.response.send_message(
                f'There is currently no active round; you must create an active round first', ephemeral=True)
        elif not latest_round.is_active_round:
            await interaction.response.send_message(
                f'The most recent round is not currently active; the current round must be active to create a dilemma!',
                ephemeral=True)
            return
        else:
            new_dilemma = Dilemma(dilemma_votes=[], dilemma_id=dilemma_name, dilemma_player_ids=[], dilemma_choices=[],
                                  is_active_dilemma=False)
            latest_round.add_dilemma(new_dilemma)

        await gdm.write_game(game=game, file_path=Conf.GAME_PATH)
        await interaction.response.send_message(
            f'Created dilemma {new_dilemma.dilemma_id} for round {latest_round.round_number}!', ephemeral=True)

    @app_commands.command(name="update-dilemma-choices",
                          description="Adds or Removes a choice to a selected dilemma")
    @app_commands.default_permissions(manage_guild=True)
    async def update_dilemma_choices(self,
                                     interaction: discord.Interaction,
                                     dilemma_name: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        latest_round = game.get_latest_round()

        if latest_round is None:
            await interaction.response.send_message(
                f'There is currently no active round; you must create an active round first', ephemeral=True)
        elif not latest_round.is_active_round:
            await interaction.response.send_message(
                f'The most recent round is not currently active; the current round must be active to create a dilemma!',
                ephemeral=True)
            return
        else:
            new_dilemma = Dilemma(dilemma_votes=[], dilemma_id=dilemma_name, dilemma_player_ids=[], dilemma_choices=[],
                                  is_active_dilemma=False)
            latest_round.add_dilemma(new_dilemma)

        await gdm.write_game(game=game, file_path=Conf.GAME_PATH)
        await interaction.response.send_message(
            f'Created dilemma {new_dilemma.dilemma_id} for round {latest_round.round_number}!', ephemeral=True)

    @app_commands.command(name="update-dilemma-status",
                          description="Adds or Removes a choice to a selected dilemma")
    @app_commands.default_permissions(manage_guild=True)
    async def update_dilemma_choices(self, interaction: discord.Interaction,
                                     dilemma_name: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        latest_round = game.get_latest_round()

        if latest_round is None:
            await interaction.response.send_message(
                f'There is currently no active round; you must create an active round first', ephemeral=True)
        elif not latest_round.is_active_round:
            await interaction.response.send_message(
                f'The most recent round is not currently active; the current round must be active to create a dilemma!',
                ephemeral=True)
            return
        else:
            new_dilemma = Dilemma(dilemma_votes=[], dilemma_id=dilemma_name, dilemma_player_ids=[], dilemma_choices=[],
                                  is_active_dilemma=False)
            latest_round.add_dilemma(new_dilemma)

        await gdm.write_game(game=game, file_path=Conf.GAME_PATH)
        await interaction.response.send_message(
            f'Created dilemma {new_dilemma.dilemma_id} for round {latest_round.round_number}!', ephemeral=True)

    @app_commands.command(name="vote-player",
                          description="Votes for a particular player")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    @app_commands.autocomplete(player=player_list_autocomplete)
    async def vote_player(self, interaction: discord.Interaction,
                          player: Optional[str] = None,
                          other: Optional[Literal['No Vote', 'Unvote']] = None):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        if not game.is_active:
            await interaction.response.send_message(
                f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
            return

        if player is not None and other is not None:
            await interaction.response.send_message(
                f'You may select only one of the arguments player or other, you cannot select both. Please resubmit your vote.',
                ephemeral=True)
            return

        latest_round = game.get_latest_round()
        if latest_round is None or not latest_round.is_active_round:
            await interaction.response.send_message(f'No currently active round found for this game!', ephemeral=True)
            return

        requesting_player = game.get_player(interaction.user.id)
        if requesting_player is None or requesting_player.is_dead:
            await interaction.response.send_message(f'Player {interaction.user.name} was not found in this game!',
                                                    ephemeral=True)
            return

        if player is not None and player not in game.get_living_player_ids():
            await interaction.response.send_message(f'Invalid player selection! Please resubmit your vote.',
                                                    ephemeral=True)
            return

        voted_player = None if player is None else game.get_player(int(player))

        if voted_player is not None and voted_player.is_dead:
            await interaction.response.send_message(
                f'Player {voted_player.player_discord_name} is dead and cannot be voted!', ephemeral=True)
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
                    latest_round.add_vote(
                        Vote(requesting_player.player_id, str(voted_player.player_id), round(time.time())))
                else:
                    round_current_player_vote.choice = str(voted_player.player_id)
                    round_current_player_vote.timestamp = round(time.time())

            await gdm.write_game(game=game, file_path=Conf.GAME_PATH)

            if voted_player is not None:
                success_vote_target = voted_player.player_discord_name
            else:
                success_vote_target = other
            await interaction.response.send_message(f'Registered vote for {success_vote_target}!', ephemeral=True)

            vote_channel = interaction.guild.get_channel(Conf.VOTE_CHANNEL)

            response_value = voted_player.player_discord_name if voted_player is not None else other

            if vote_channel is not None:
                await interaction.followup.send(f'Sending public vote announcement in channel #{vote_channel}',
                                                ephemeral=True)
                await vote_channel.send(
                    f'Player **{requesting_player.player_discord_name}** has submitted a vote for **{response_value}**')
            else:
                await interaction.followup.send(f'Sending public vote results now...', ephemeral=True)
                await interaction.followup.send(
                    f'Player **{requesting_player.player_discord_name}** has submitted a vote for **{response_value}**',
                    ephemeral=False)

    @app_commands.command(name="vote-report",
                          description="Generates a report of current voting totals")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    async def vote_report(self,
                          interaction: discord.Interaction,
                          for_round: Optional[app_commands.Range[int, 0, 20]] = None,
                          with_history: Optional[Literal['Yes', 'No']] = 'No'):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        if not game.is_active:
            await interaction.response.send_message(
                f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
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

        vote_channel = interaction.guild.get_channel(Conf.VOTE_CHANNEL)

        if vote_channel is not None:
            await interaction.response.send_message(f'Sending query response in channel ', ephemeral=True)
            await vote_channel.send(formatted_votes)
        else:
            await interaction.response.send_message(f'Sending vote results now...', ephemeral=True)
            await interaction.followup.send(formatted_votes, ephemeral=False)

        # With History to-be-implemented


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VotingManager(bot), guilds=[discord.Object(id=Conf.GUILD_ID)])
