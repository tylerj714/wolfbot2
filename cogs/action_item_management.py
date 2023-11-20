#! action_item_management.py
# Class with slash commands managing game state

import discord
from discord import app_commands
from discord.ext import commands
from dom.conf_vars import ConfVars as Conf
from typing import Optional, List, Literal
import dom.data_model as gdm
from dom.data_model import Game, Item, Action, Player
from bot_logging.logging_manager import log_interaction_call
import random
import string
import time
from utils.command_autocompletes import game_item_autocomplete, player_item_autocomplete, player_list_autocomplete, \
    game_action_autocomplete, player_action_autocomplete


async def construct_action_display(player: Optional[Player] = None, actions: Optional[List[Action]] = None) -> str:
    if actions is None:
        actions = []

    formatted_actions = ""

    if player is not None:
        f'**Player {player.player_discord_name} Actions as of <t:{int(time.time())}>**\n'
    else:
        f'**Actions as of <t:{int(time.time())}>**\n'

    if actions is None and player is not None:
        actions = player.player_actions

    if actions:
        for action in actions:
            formatted_actions += f'- **{action.name}**:'
            if action.timing is not None:
                formatted_actions += f'{action.timing} '
            if action.uses is not None:
                formatted_actions += f'{action.uses} '
            formatted_actions += f'- {action.desc}'
            formatted_actions += '\n'
    else:
        formatted_actions += f'*<No Actions!>*'

    return formatted_actions


async def construct_action_change_display(status: Literal['gained', 'lost'], action: Action) -> str:
    formatted_action = ""

    if status == 'gained':
        formatted_action += f'You have been **granted** the action **{action.name}**:\n'
        formatted_action += f'- **{action.name}**: '
        if action.timing is not None:
            formatted_action += f'{action.timing} '
        if action.uses is not None:
            formatted_action += f'{action.uses} '
        formatted_action += f'- {action.desc}'
        formatted_action += '\n'
    else:
        formatted_action += f'You have **lost** the action **{action.name}**!\n'

    return formatted_action


async def construct_item_display(player: Optional[Player] = None, items: Optional[List[Item]] = None) -> str:
    if items is None:
        items = []

    formatted_items = ""

    if player is not None:
        f'**Player {player.player_discord_name} Inventory as of <t:{int(time.time())}>**\n'
    else:
        f'**Inventory as of <t:{int(time.time())}>**\n'

    if items is None and player is not None:
        items = player.player_items

    if items:
        for item in items:
            formatted_items += f'- **{item.item_name}** - {item.item_descr}'
            if item.item_action is not None and item.item_action.name:
                formatted_items += '\n'
                item_action = item.item_action
                formatted_items += f'> **{item_action.name}**: '
                if item_action.timing is not None:
                    formatted_items += f'{item_action.timing} '
                if item_action.uses is not None:
                    formatted_items += f'{item_action.uses} '
                formatted_items += f'- {item_action.desc}'
            formatted_items += '\n'
    else:
        formatted_items += f'*<No items!>*'

    return formatted_items


async def construct_item_transfer_display(action: Literal['gained', 'lost'], item: Item) -> str:
    formatted_item = ""

    if action == 'gained':
        formatted_item += f'You have **gained possession** of the item **{item.item_name}**:\n'
        formatted_item += f'- **{item.item_name}** - {item.item_descr}'
        if item.item_action is not None and item.item_action.name is not None:
            formatted_item += '\n'
            item_action = item.item_action
            formatted_item += f'> **{item_action.name}**: '
            if item_action.timing is not None:
                formatted_item += f'{item_action.timing} '
            if item_action.uses is not None:
                formatted_item += f'{item_action.uses} '
            formatted_item += f'- {item_action.desc}'
        formatted_item += '\n'
    else:
        formatted_item += f'You have **lost possession** of the item **{item.item_name}**!\n'

    return formatted_item


class ActionItemManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="items-inventory-view",
                          description="Displays all current items in your inventory")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    async def items_inventory_view(self,
                                   interaction: discord.Interaction):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        game_player = game.get_player(interaction.user.id)

        formatted_items = await construct_item_display(player=game_player, items=game_player.player_items)

        await interaction.response.send_message(f'{formatted_items}', ephemeral=True)

    @app_commands.command(name="items-player-inventory-view",
                          description="Displays all current items in the chosen player's inventory")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(player=player_list_autocomplete)
    async def items_player_inventory_view(self,
                                          interaction: discord.Interaction,
                                          player: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        game_player = game.get_player(int(player))

        formatted_items = await construct_item_display(player=game_player, items=game_player.player_items)

        await interaction.response.send_message(f'{formatted_items}', ephemeral=True)

    @app_commands.command(name="items-send-to-player",
                          description="Allows a player to send an item to another player")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    @app_commands.autocomplete(player=player_list_autocomplete)
    @app_commands.autocomplete(item=player_item_autocomplete)
    async def items_send_to_player(self,
                                   interaction: discord.Interaction,
                                   item: str,
                                   player: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        sending_player = game.get_player(interaction.user.id)
        receiving_player = game.get_player(int(player))

        item_to_send = sending_player.get_item(item)

        if item_to_send is None:
            await interaction.response.send_message(f'Item {item} not found in your inventory!', ephemeral=True)
        if receiving_player is None:
            await interaction.response.send_message(f'Recipient player was not a valid choice!', ephemeral=True)

        sending_player.remove_item(item_to_send)
        receiving_player.add_item(item_to_send)

        await gdm.write_game(game=game)

        await interaction.response.send_message(f'Sent item {item} to player {receiving_player.player_discord_name}!',
                                                ephemeral=True)

        sending_player_mod_channel = await interaction.guild.fetch_channel(
            sending_player.player_mod_channel) if sending_player.player_mod_channel is not None else None
        receiving_player_mod_channel = await interaction.guild.fetch_channel(
            receiving_player.player_mod_channel) if receiving_player.player_mod_channel is not None else None

        item_lost_message = await construct_item_transfer_display('lost', item_to_send)
        item_gained_message = await construct_item_transfer_display('gained', item_to_send)

        if sending_player_mod_channel is not None:
            await sending_player_mod_channel.send(f'{item_lost_message}')
        if receiving_player_mod_channel is not None:
            await receiving_player_mod_channel.send(f'{item_gained_message}')

    @app_commands.command(name="items-player-add",
                          description="Adds an item to a player's inventory from the game item config")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(player=player_list_autocomplete)
    @app_commands.autocomplete(item=game_item_autocomplete)
    async def items_player_add(self,
                               interaction: discord.Interaction,
                               player: str,
                               item: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        game_player = game.get_player(int(player))

        game_item = game.get_item(item)

        if game_item is None:
            await interaction.response.send_message(f'Item {item} not defined in this game!', ephemeral=True)
        if game_player is None:
            await interaction.response.send_message(f'Recipient player was not a valid choice!', ephemeral=True)

        game_player.add_item(game_item)
        item_mod_message = await construct_item_transfer_display('gained', game_item)

        await gdm.write_game(game=game)

        await interaction.response.send_message(
            f'Added item {item} to player {game_player.player_discord_name}\'s inventory!',
            ephemeral=True)

        player_mod_channel = await interaction.guild.fetch_channel(
            game_player.player_mod_channel) if game_player.player_mod_channel is not None else None

        if player_mod_channel is not None:
            await player_mod_channel.send(f'{item_mod_message}')

    @app_commands.command(name="items-player-remove",
                          description="Removes an item from a player's inventory")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(player=player_list_autocomplete)
    @app_commands.autocomplete(item=player_item_autocomplete)
    async def items_player_remove(self,
                                  interaction: discord.Interaction,
                                  player: str,
                                  item: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        game_player = game.get_player(int(player))

        if game_player is None:
            await interaction.response.send_message(f'Recipient player was not a valid choice!', ephemeral=True)
            return

        player_item = game_player.get_item(item)

        if player_item is None:
            await interaction.response.send_message(f'Item {item} not defined in this game!', ephemeral=True)
            return

        game_player.remove_item(player_item)
        item_mod_message = await construct_item_transfer_display('lost', player_item)

        await gdm.write_game(game=game)

        await interaction.response.send_message(
            f'Remove item {item} from player {game_player.player_discord_name}\'s inventory!',
            ephemeral=True)

        player_mod_channel = await interaction.guild.fetch_channel(
            game_player.player_mod_channel) if game_player.player_mod_channel is not None else None

        if player_mod_channel is not None:
            await player_mod_channel.send(f'{item_mod_message}')

    @app_commands.command(name="items-transfer-player",
                          description="Transfers an item from one player to another player")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(player=player_list_autocomplete)
    @app_commands.autocomplete(recipient_player=player_list_autocomplete)
    @app_commands.autocomplete(item=player_item_autocomplete)
    async def items_transfer_player(self,
                                    interaction: discord.Interaction,
                                    player: str,
                                    recipient_player: str,
                                    item: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        sending_player = game.get_player(int(player))
        receiving_player = game.get_player(int(recipient_player))

        item_to_send = sending_player.get_item(item)

        if item_to_send is None:
            await interaction.response.send_message(
                f'Item {item} not found in the player {sending_player.player_discord_name}\'s inventory!',
                ephemeral=True)
        if receiving_player is None:
            await interaction.response.send_message(f'Recipient player was not a valid choice!', ephemeral=True)

        sending_player.remove_item(item_to_send)
        receiving_player.add_item(item_to_send)

        await gdm.write_game(game=game)

        await interaction.response.send_message(f'Sent item {item} to player {receiving_player.player_discord_name}!',
                                                ephemeral=True)

        sending_player_mod_channel = await interaction.guild.fetch_channel(
            sending_player.player_mod_channel) if sending_player.player_mod_channel is not None else None
        receiving_player_mod_channel = await interaction.guild.fetch_channel(
            receiving_player.player_mod_channel) if receiving_player.player_mod_channel is not None else None

        item_lost_message = await construct_item_transfer_display('lost', item_to_send)
        item_gained_message = await construct_item_transfer_display('gained', item_to_send)

        if sending_player_mod_channel is not None:
            await sending_player_mod_channel.send(f'{item_lost_message}')
        if receiving_player_mod_channel is not None:
            await receiving_player_mod_channel.send(f'{item_gained_message}')

    @app_commands.command(name="actions-view",
                          description="Displays all current actions you can use")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    async def actions_view(self,
                           interaction: discord.Interaction):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        game_player = game.get_player(interaction.user.id)

        if game_player is None:
            await interaction.response.send_message(f'You are not an active player of the current game!')
            return

        formatted_actions = await construct_action_display(player=game_player, actions=game_player.player_actions)

        await interaction.response.send_message(f'{formatted_actions}', ephemeral=True)

    @app_commands.command(name="actions-player-view",
                          description="Displays all current actions usable by the chosen player")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(player=player_list_autocomplete)
    async def actions_player_view(self,
                                  interaction: discord.Interaction,
                                  player: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        game_player = game.get_player(int(player))

        formatted_actions = await construct_action_display(player=game_player, actions=game_player.player_actions)

        await interaction.response.send_message(f'{formatted_actions}', ephemeral=True)

    @app_commands.command(name="actions-player-add",
                          description="Adds an action to the chosen player's action list")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(player=player_list_autocomplete)
    @app_commands.autocomplete(action=game_action_autocomplete)
    async def actions_player_add(self,
                                 interaction: discord.Interaction,
                                 player: str,
                                 action: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        game_player = game.get_player(int(player))

        game_action = game.get_action(action)

        if game_player is None:
            await interaction.response.send_message(f'No valid player found with that identifier in the current game!')
            return
        if game_action is None:
            await interaction.response.send_message(f'No action {action} could be found in the current game!')
            return

        game_player.add_action(game_action)

        await gdm.write_game(game=game)

        formatted_action = await construct_action_change_display(status='gained', action=game_action)

        player_mod_channel = await interaction.guild.fetch_channel(
            game_player.player_mod_channel) if game_player.player_mod_channel is not None else None
        if player_mod_channel is not None:
            await player_mod_channel.send(f'{formatted_action}')

        await interaction.response.send_message(
            f'Granted the action {action} to player {game_player.player_discord_name}!', ephemeral=True)

    @app_commands.command(name="actions-player-remove",
                          description="Removes an action from the chosen player's action list")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(player=player_list_autocomplete)
    @app_commands.autocomplete(action=player_action_autocomplete)
    async def actions_player_remove(self,
                                    interaction: discord.Interaction,
                                    player: str,
                                    action: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)

        game_player = game.get_player(int(player))

        if game_player is None:
            await interaction.response.send_message(f'No valid player found with that identifier in the current game!')
            return

        player_action = game_player.get_action(action)

        if player_action is None:
            await interaction.response.send_message(f'No action {action} could be found in the current game!')
            return

        game_player.remove_action(player_action)

        await gdm.write_game(game=game)

        formatted_action = await construct_action_change_display(status='lost', action=player_action)

        player_mod_channel = await interaction.guild.fetch_channel(
            game_player.player_mod_channel) if game_player.player_mod_channel is not None else None
        if player_mod_channel is not None:
            await player_mod_channel.send(f'{formatted_action}')

        await interaction.response.send_message(
            f'Removed the action {action} from player {game_player.player_discord_name}!', ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ActionItemManager(bot), guilds=[discord.Object(id=Conf.GUILD_ID)])
