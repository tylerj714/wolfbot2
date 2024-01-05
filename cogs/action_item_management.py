#! action_item_management.py
# Class with slash commands managing actions and items

import discord
from discord import app_commands, Guild
from discord.ext import commands
from dom.conf_vars import ConfVars as Conf
from typing import Optional, List, Literal
import dom.data_model as gdm
from dom.data_model import Item, Action, Player
from bot_logging.logging_manager import log_interaction_call, log_info
import utils.string_decorator as sdec
import time
from utils.command_autocompletes import game_item_autocomplete, player_item_autocomplete, player_list_autocomplete, \
    game_action_autocomplete, player_action_autocomplete
from cogs.moderator_request_management import send_message_to_moderator as modmsg


async def construct_action_display(guild: Guild, player: Optional[Player] = None, actions: Optional[List[Action]] = None,
                                   from_spellbook: bool = False) -> str:
    if actions is None:
        actions = []

    formatted_actions = ""

    if from_spellbook:
        formatted_actions += ""
    elif player is not None:
        formatted_actions += f'**Player {player.player_discord_name} Actions as of <t:{int(time.time())}>**\n'
    else:
        formatted_actions += f'**Actions as of <t:{int(time.time())}>**\n'

    if actions is None and player is not None:
        actions = player.player_actions

    if actions:
        for action in actions:
            formatted_actions += await format_action(action)
    else:
        formatted_actions += f'*<No Actions!>*'

    formatted_actions = await sdec.format_text(text=formatted_actions, guild=guild)

    return formatted_actions


async def construct_action_change_display(guild: Guild, status: Literal['gained', 'lost'], action: Action) -> str:
    formatted_action = ""

    if status == 'gained':
        formatted_action += f'You have been **granted** the action **{action.name}**:\n'
        formatted_action += await format_action(action)
    else:
        formatted_action += f'You have **lost** the action **{action.name}**!\n'

    formatted_action = await sdec.format_text(text=formatted_action, guild=guild)

    return formatted_action


async def format_action(action: Action) -> str:
    formatted_action = f'- **{action.name}**:'
    if action.timing:
        formatted_action += f' {action.timing} '
    if action.cost:
        formatted_action += f'- Cost: {action.cost} '
    if action.uses:
        formatted_action += f'- {action.uses} '
    formatted_action += f'- {action.desc}'
    formatted_action += '\n'
    return formatted_action


async def construct_item_display(guild: Guild, player: Optional[Player] = None, items: Optional[List[Item]] = None,
                                 from_spellbook: bool = False) -> str:
    if items is None:
        items = []

    formatted_items = ""

    if from_spellbook:
        formatted_items += ""
    elif player is not None:
        formatted_items += f'**Player {player.player_discord_name} Inventory as of <t:{int(time.time())}>**\n'
    else:
        formatted_items += f'**Inventory as of <t:{int(time.time())}>**\n'

    if items is None and player is not None:
        items = player.player_items

    if items:
        for item in items:
            formatted_items += await format_item(item)
    else:
        formatted_items += f'*<No items!>*'

    formatted_items = await sdec.format_text(text=formatted_items, guild=guild)

    return formatted_items


async def construct_item_transfer_display(guild: Guild, action: Literal['gained', 'lost'], item: Item) -> str:
    formatted_item = ""

    if action == 'gained':
        formatted_item += f'You have **gained possession** of the item **{item.item_name}**:\n'
        formatted_item += await format_item(item)
    else:
        formatted_item += f'You have **lost possession** of the item **{item.item_name}**!\n'

    formatted_item = await sdec.format_text(text=formatted_item, guild=guild)

    return formatted_item


async def format_item(item: Item) -> str:
    formatted_item = f'- **{item.item_name}**'
    if item.item_properties is not None:
        formatted_item += f' - {item.item_properties}\n'
    formatted_item += f'{item.item_descr}'
    if item.item_action is not None and item.item_action.name:
        item_action = item.item_action
        formatted_item += '\n'
        formatted_item += f'> - **{item_action.name}**: '
        if item_action.timing:
            formatted_item += f' {item_action.timing} '
        if item_action.cost:
            formatted_item += f'- Cost: {item_action.cost} '
        if item_action.uses:
            formatted_item += f'- {item_action.uses} '
        formatted_item += f'- {item_action.desc}'
    formatted_item += '\n'
    return formatted_item


class ActionItemManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="items-handbook-view",
                          description="Displays an item from the spellbook")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    @app_commands.autocomplete(item=game_item_autocomplete)
    async def items_handbook_view(self,
                                  interaction: discord.Interaction,
                                  item: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)
        guild = interaction.guild

        item = game.get_item(item_name=item)

        formatted_items = await construct_item_display(items=[item], from_spellbook=True, guild=guild)

        await interaction.response.send_message(f'{formatted_items}', ephemeral=True)

    @app_commands.command(name="items-inventory-view",
                          description="Displays all current items in your inventory")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    async def items_inventory_view(self,
                                   interaction: discord.Interaction):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)
        guild = interaction.guild

        game_player = game.get_player(interaction.user.id)

        formatted_items = await construct_item_display(player=game_player, items=game_player.player_items, guild=guild)

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
        guild = interaction.guild

        game_player = game.get_player(int(player))

        formatted_items = await construct_item_display(player=game_player, items=game_player.player_items, guild=guild)

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
        guild = interaction.guild

        if not game.is_active or game.items_locked:
            await interaction.response.send_message(
                f'The bot has been put in an inactive state by the moderator. Please try again later.', ephemeral=True)
            return
        elif game.items_locked:
            await interaction.response.send_message(f'Items cannot currently be sent!', ephemeral=True)
            return

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

        item_lost_message = await construct_item_transfer_display(action='lost', item=item_to_send, guild=guild)
        item_gained_message = await construct_item_transfer_display(action='gained', item=item_to_send, guild=guild)

        if sending_player_mod_channel is not None:
            await sending_player_mod_channel.send(f'{item_lost_message}')
        if receiving_player_mod_channel is not None:
            await receiving_player_mod_channel.send(f'{item_gained_message}')

        mod_message = f'Player **{sending_player.player_discord_name}** sent item **{item_to_send.item_name}** to **{receiving_player.player_discord_name}**'
        await modmsg(mod_message, guild)

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
        guild = interaction.guild

        game_player = game.get_player(int(player))

        game_item = game.get_item(item)

        if game_item is None:
            await interaction.response.send_message(f'Item {item} not defined in this game!', ephemeral=True)
        if game_player is None:
            await interaction.response.send_message(f'Recipient player was not a valid choice!', ephemeral=True)

        game_player.add_item(game_item)
        item_mod_message = await construct_item_transfer_display(action='gained', item=game_item, guild=guild)

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
        guild = interaction.guild

        game_player = game.get_player(int(player))

        if game_player is None:
            await interaction.response.send_message(f'Recipient player was not a valid choice!', ephemeral=True)
            return

        player_item = game_player.get_item(item)

        if player_item is None:
            await interaction.response.send_message(f'Item {item} not defined in this game!', ephemeral=True)
            return

        game_player.remove_item(player_item)
        item_mod_message = await construct_item_transfer_display(action='lost', item=player_item, guild=guild)

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
        guild = interaction.guild

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

        item_lost_message = await construct_item_transfer_display(action='lost', item=item_to_send, guild=guild)
        item_gained_message = await construct_item_transfer_display(action='gained', item=item_to_send, guild=guild)

        if sending_player_mod_channel is not None:
            await sending_player_mod_channel.send(f'{item_lost_message}')
        if receiving_player_mod_channel is not None:
            await receiving_player_mod_channel.send(f'{item_gained_message}')

    @app_commands.command(name="actions-handbook-view",
                          description="Displays a chosen action from the public spellbook")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    @app_commands.autocomplete(action=game_action_autocomplete)
    async def actions_handbook_view(self,
                                    interaction: discord.Interaction,
                                    action: str):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)
        guild = interaction.guild

        action = game.get_action(action_name=action)

        formatted_actions = await construct_action_display(actions=[action], from_spellbook=True, guild=guild)

        await interaction.response.send_message(f'{formatted_actions}', ephemeral=True)

    @app_commands.command(name="actions-available-view",
                          description="Displays all current actions you can use")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.guild_id)
    async def actions_available_view(self,
                                     interaction: discord.Interaction):
        log_interaction_call(interaction)
        game = await gdm.get_game(file_path=Conf.GAME_PATH)
        guild = interaction.guild

        game_player = game.get_player(interaction.user.id)

        if game_player is None:
            await interaction.response.send_message(f'You are not an active player of the current game!')
            return

        formatted_actions = await construct_action_display(player=game_player, actions=game_player.player_actions, guild=guild)

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
        guild = interaction.guild

        game_player = game.get_player(int(player))

        formatted_actions = await construct_action_display(player=game_player, actions=game_player.player_actions, guild=guild)

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
        guild = interaction.guild

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

        formatted_action = await construct_action_change_display(status='gained', action=game_action, guild=guild)

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
        guild = interaction.guild
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

        formatted_action = await construct_action_change_display(status='lost', action=player_action, guild=guild)

        player_mod_channel = await interaction.guild.fetch_channel(
            game_player.player_mod_channel) if game_player.player_mod_channel is not None else None
        if player_mod_channel is not None:
            await player_mod_channel.send(f'{formatted_action}')

        await interaction.response.send_message(
            f'Removed the action {action} from player {game_player.player_discord_name}!', ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    cog = ActionItemManager(bot)
    await bot.add_cog(cog, guilds=[discord.Object(id=Conf.GUILD_ID)])
    log_info(f'Cog {cog.__class__.__name__} loaded!')
