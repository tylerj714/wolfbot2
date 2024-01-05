#! moderator_request_management.py
# Class with slash commands managing game state

import discord
from discord import app_commands, Guild
from discord.ext import commands
from dom.conf_vars import ConfVars as Conf
import dom.data_model as gdm
from typing import Optional, Literal
from bot_logging.logging_manager import log_interaction_call, log_info
from utils.command_autocompletes import player_action_autocomplete, game_action_autocomplete


async def send_message_to_moderator(message: str, guild: Guild):
    mod_request_channel = await guild.fetch_channel(Conf.REQUEST_CHANNEL)

    formatted_request = f'<@&{Conf.MOD_ROLE_ID}>\n'
    formatted_request += f'{message}\n'

    await mod_request_channel.send(formatted_request)


class ModRequestManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="mod-request",
                          description="Send a request to the moderator through a private channel")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    async def moderator_request(self, interaction: discord.Interaction,
                                request: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(Conf.GAME_PATH)

        mod_request_channel = await interaction.guild.fetch_channel(Conf.REQUEST_CHANNEL)

        requesting_player = game.get_player(interaction.user.id)

        if requesting_player is None:
            await interaction.response.send_message(
                f'Player {interaction.user.name} is not currently defined in this game!', ephemeral=True)
            return
        elif requesting_player.is_dead:
            await interaction.response.send_message(f'You are dead! Begone apparition!')
            return
        else:
            await interaction.response.send_message(f'Submitted request **{request}** to the moderator!',
                                                    ephemeral=True)
            await mod_request_channel.send(
                f'<@&{Conf.MOD_ROLE_ID}>\nPlayer **{requesting_player.player_discord_name}** has submitted an action request of **{request}**\n')

    @app_commands.command(name="action-submission",
                          description="Submit an action to be performed to the moderator")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    @app_commands.autocomplete(action=player_action_autocomplete)
    async def action_submission(self, interaction: discord.Interaction,
                                action: str,
                                target1: Optional[str],
                                target2: Optional[str],
                                target3: Optional[str],
                                request_details: Optional[str]):
        log_interaction_call(interaction)
        game = await gdm.get_game(Conf.GAME_PATH)

        mod_request_channel = await interaction.guild.fetch_channel(Conf.REQUEST_CHANNEL)

        requesting_player = game.get_player(interaction.user.id)

        if requesting_player is None:
            await interaction.response.send_message(
                f'Player {interaction.user.name} is not currently defined in this game!', ephemeral=True)
            return
        elif requesting_player.is_dead:
            await interaction.response.send_message(f'You are dead! Begone apparition!', ephemeral=True)
            return
        else:
            await interaction.response.send_message(f'Submitted request for action **{action}** to the moderator!',
                                                    ephemeral=True)

            formatted_request = f'<@&{Conf.MOD_ROLE_ID}>\nPlayer **{requesting_player.player_discord_name}** has requested to use the action **{action}**\n'
            if target1:
                formatted_request += f'First Target: {target1}\n'
            if target2:
                formatted_request += f'Second Target: {target2}\n'
            if target3:
                formatted_request += f'Third Target: {target3}\n'
            if request_details:
                formatted_request += f'Additional details: {request_details}\n'

            await mod_request_channel.send(formatted_request)

    @app_commands.command(name="level-up",
                          description="Submit level up requests to the moderator here.")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    @app_commands.autocomplete(action=game_action_autocomplete)
    async def level_up(self, interaction: discord.Interaction,
                       action: str,
                       skill: str,
                       attribute1: Literal['Body', 'Mind', 'Spirit'],
                       attribute2: Literal['Body', 'Mind', 'Spirit']):
        log_interaction_call(interaction)
        game = await gdm.get_game(Conf.GAME_PATH)

        mod_request_channel = await interaction.guild.fetch_channel(Conf.REQUEST_CHANNEL)

        requesting_player = game.get_player(interaction.user.id)

        if requesting_player is None:
            await interaction.response.send_message(
                f'Player {interaction.user.name} is not currently defined in this game!', ephemeral=True)
            return
        elif requesting_player.is_dead:
            await interaction.response.send_message(f'You are dead! Begone apparition!', ephemeral=True)
            return
        else:
            await interaction.response.send_message(f'Submitted level up request to the moderator!',
                                                    ephemeral=True)

            formatted_request = f'<@&{Conf.MOD_ROLE_ID}>\nPlayer **{requesting_player.player_discord_name}** has submitted a level-up request:\n'
            formatted_request += f'New Action: {action}\n'
            formatted_request += f'New Skill: {skill}\n'
            formatted_request += f'Attribute 1: {attribute1}\n'
            formatted_request += f'Attribute 2: {attribute2}\n'

            await mod_request_channel.send(formatted_request)


async def setup(bot: commands.Bot) -> None:
    cog = ModRequestManager(bot)
    await bot.add_cog(cog, guilds=[discord.Object(id=Conf.GUILD_ID)])
    log_info(f'Cog {cog.__class__.__name__} loaded!')
