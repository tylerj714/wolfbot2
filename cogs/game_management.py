#! game_management.py
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

class GameManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="toggle-activity",
                          description="Enables/Disables bot commands for players")
    @app_commands.default_permissions(manage_guild=True)
    async def toggle_activity(self,
                              interaction: discord.Interaction,
                              active: Literal['True', 'False']):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        game.is_active = True if active == 'True' else False

        await gdm.write_game(game=game, file_path=Conf.GAME_PATH)
        await interaction.response.send_message(f'Game state has been set to {active}!', ephemeral=True)

    @app_commands.command(name="clear-messages",
                          description="Clears up to 100 messages out of a discord channel")
    @app_commands.default_permissions(manage_guild=True)
    async def clear_messages(self,
                             interaction: discord.Interaction,
                             channel: discord.TextChannel,
                             channel_again: discord.TextChannel):
        log_interaction_call(interaction)

        if channel != channel_again:
            await interaction.response.send_message(
                f"Both channel arguments must be the same! This is a safety feature!")

        await interaction.response.send_message(f"Clearing messages from channel {channel.name}")
        await channel.purge(limit=100)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GameManager(bot), guilds=[discord.Object(id=Conf.GUILD_ID)])