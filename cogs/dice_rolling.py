#! dice_rolling.py
# Class with slash commands for rolling dice

import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from typing import Literal, Optional
from dom.conf_vars import ConfVars as Conf
from bot_logging.logging_manager import log_interaction_call
import random


class DiceManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="roll-dice",
                          description="Rolls one or more dice with a specified number of sides")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    async def roll_dice(self, interaction: discord.Interaction,
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

    # @app_commands.command(name="action-success-roll",
    #                       description="Computes success and dice roll result for an action")
    # @app_commands.default_permissions(manage_guild=True)
    # async def action_success_roll(self, interaction: discord.Interaction,
    #                               source_skill_level: app_commands.Range[int, 0, 100],
    #                               target_skill_level: app_commands.Range[int, 0, 100],
    #                               with_modifier: Optional[Literal[True, False]]):
    #     await interaction.response.send_message("Not implemented yet!")
    #
    # @app_commands.command(name="action-result-roll",
    #                       description="Computes value of one or more dice rolls")
    # @app_commands.default_permissions(manage_guild=True)
    # async def action_result_roll(self,
    #                              interaction: discord.Interaction,
    #                              base_source_value: app_commands.Range[int, 0, 20],
    #                              base_target_reduction: app_commands.Range[int, 0, 20],
    #                              d1_faces: Literal[2, 4, 6, 8, 10, 12, 20],
    #                              d1_to_roll: app_commands.Range[int, 1, 5],
    #                              d1_target_resistance: Optional[app_commands.Range[0, 10]] = 0,
    #                              d2_faces: Optional[Literal[2, 4, 6, 8, 10, 12, 20]] = 4,
    #                              d2_to_roll: Optional[app_commands.Range[int, 0, 5]] = 0,
    #                              d2_target_resistance: Optional[app_commands.Range[0, 10]] = 0):
    #     await interaction.response.send_message("Not implemented yet!")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiceManager(bot), guilds=[discord.Object(id=Conf.GUILD_ID)])
