#! moderator_request_management.py
# Class with slash commands managing game state

import discord
from discord import app_commands
from discord.ext import commands
from dom.conf_vars import ConfVars as Conf
from typing import Literal
import dom.data_model as gdm
from bot_logging.logging_manager import log_interaction_call
import random
import string


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
            await interaction.response.send_message(f'Submitted request {request} to the moderator!', ephemeral=True)
            await mod_request_channel.send(
                f'<@&{Conf.MOD_ROLE_ID}>\nPlayer **{requesting_player.player_discord_name}** has submitted an action request of **{request}**')


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModRequestManager(bot), guilds=[discord.Object(id=Conf.GUILD_ID)])
