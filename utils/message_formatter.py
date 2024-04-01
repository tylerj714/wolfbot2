import time
from typing import Optional, List, Literal
from discord import Guild
from dom.data_model import Player, Action, Item, Game
import utils.string_decorator as sdec

uses_to_emoji_map = {0: "uses_zero",
                     1: ":uses_one:",
                     2: ":uses_two:",
                     3: ":uses_three:",
                     4: ":uses_four:",
                     5: ":uses_five:"}


async def convert_uses_to_emoji(uses: int) -> str:
    if uses == 0:
        return ""

    if uses in uses_to_emoji_map:
        return uses_to_emoji_map[uses]
    else:
        return ":uses_any:"


async def construct_action_display(guild: Guild, game: Game, player: Optional[Player] = None,
                                   actions: Optional[list[Action]] = None,
                                   item_actions: Optional[list[(str, Action)]] = None,
                                   from_spellbook: bool = False) -> list[str]:
    if actions is None:
        actions: list[Action] = []
    if item_actions is None:
        item_actions: list[(str, Action)] = []

    formatted_responses = []
    formatted_action_header = ""

    if from_spellbook:
        formatted_action_header += "Viewing Action Details..."
    elif player is not None:
        formatted_action_header += f'**Player {player.player_discord_name} Actions as of <t:{int(time.time())}>**\n'
    else:
        formatted_action_header += f'**Actions as of <t:{int(time.time())}>**\n'
    formatted_responses.append(await sdec.format_text(text=formatted_action_header, guild=guild))

    if actions is None and player is not None:
        actions = player.player_actions

    if item_actions is None and player is not None:
        item_actions = player.get_item_actions()

    if actions:
        formatted_actions = ""
        for action in actions:
            this_formatted_action = await format_action(action, game=game)
            if len(await sdec.format_text(text=formatted_actions, guild=guild)) + len(
                    await sdec.format_text(text=this_formatted_action, guild=guild)) <= 1750:
                formatted_actions += this_formatted_action
            else:
                formatted_responses.append(await sdec.format_text(text=formatted_actions, guild=guild))
                formatted_actions = ""
                formatted_actions += this_formatted_action
        formatted_responses.append(await sdec.format_text(text=formatted_actions, guild=guild))

    if item_actions:
        formatted_item_actions = ""
        for item_name, item_action in item_actions:
            this_formatted_item_action = await format_action(action=item_action, item_name=item_name, game=game)
            if len(await sdec.format_text(text=formatted_item_actions, guild=guild)) + len(
                    await sdec.format_text(text=this_formatted_item_action, guild=guild)) <= 1750:
                formatted_item_actions += this_formatted_item_action
            else:
                formatted_responses.append(await sdec.format_text(text=formatted_item_actions, guild=guild))
                formatted_item_actions = ""
                formatted_item_actions += this_formatted_item_action
        formatted_responses.append(await sdec.format_text(text=formatted_item_actions, guild=guild))

    if not actions and not item_actions:
        formatted_responses.append(await sdec.format_text(text=f'*<No Actions!>*', guild=guild))

    return formatted_responses


async def construct_action_change_display(guild: Guild, status: Literal['gained', 'lost'], action: Action,
                                          game: Game) -> List[str]:
    formatted_responses = []
    formatted_action_change = ""

    if status == 'gained':
        formatted_action_change += f'You have been **granted** the action **{action.action_name}**:\n'
        formatted_action_change += await format_action(action, game=game)
    else:
        formatted_action_change += f'You have **lost** the action **{action.action_name}**!\n'

    formatted_responses.append(await sdec.format_text(text=formatted_action_change, guild=guild))

    return formatted_responses


async def format_action(action: Action, game: Game, item_name: Optional[str] = None) -> str:
    formatted_action = f'- **{action.action_name}**:'
    if item_name:
        formatted_action += f' *(from {item_name})*'
    if action.action_timing:
        formatted_action += f' {action.action_timing} '
    if action.action_costs:
        formatted_action += f'- Cost: '
        costs = []
        for cost in action.action_costs:
            game_res_defs = game.get_resource_definitions()
            if cost.res_name in game_res_defs:
                res_def_display_name = game_res_defs[cost.res_name].emoji_text
            else:
                res_def_display_name = cost.res_name
            costs.append(f'{cost.amount} {res_def_display_name}')
        formatted_action += ' + '.join(costs) + " "
    if action.action_uses and action.action_uses != -1:
        uses_emoji = await convert_uses_to_emoji(action.action_uses)
        formatted_action += f'- {uses_emoji} '
    formatted_action += f'- {action.action_desc}'
    formatted_action += '\n'
    return formatted_action


async def construct_item_display(guild: Guild, game: Game, player: Optional[Player] = None,
                                 items: Optional[List[Item]] = None,
                                 from_spellbook: bool = False, ) -> List[str]:
    if items is None:
        items = []

    formatted_responses = []
    formatted_item_header = ""

    if from_spellbook:
        formatted_item_header += "Viewing Item Details..."
    elif player is not None:
        formatted_item_header += f'**Player {player.player_discord_name} Inventory as of <t:{int(time.time())}>**\n'
    else:
        formatted_item_header += f'**Inventory as of <t:{int(time.time())}>**\n'
    formatted_responses.append(await sdec.format_text(text=formatted_item_header, guild=guild))

    if items is None and player is not None:
        items = player.player_items

    if items:
        formatted_items = ""
        for item in items:
            this_formatted_item = await format_item(item, game=game)
            if len(await sdec.format_text(text=formatted_items, guild=guild)) + len(
                    await sdec.format_text(text=this_formatted_item, guild=guild)) <= 1750:
                formatted_items += this_formatted_item
            else:
                formatted_responses.append(await sdec.format_text(text=formatted_items, guild=guild))
                formatted_items = ""
                formatted_items += this_formatted_item
        formatted_responses.append(await sdec.format_text(text=formatted_items, guild=guild))
    else:
        formatted_responses.append(await sdec.format_text(text=f'*<No items!>*', guild=guild))

    return formatted_responses


async def construct_item_transfer_display(guild: Guild, action: Literal['gained', 'lost'], item: Item, game: Game) -> \
List[str]:
    formatted_responses = []
    formatted_item = ""

    if action == 'gained':
        formatted_item += f'You have **gained possession** of the item **{item.item_name}**:\n'
        formatted_item += await format_item(item, game=game)
    else:
        formatted_item += f'You have **lost possession** of the item **{item.item_name}**!\n'

    formatted_responses.append(await sdec.format_text(text=formatted_item, guild=guild))

    return formatted_responses


async def format_item(item: Item, game: Game) -> str:
    formatted_item = f'- **{item.item_name}**'
    if item.item_properties is not None:
        formatted_item += f' - {item.item_properties}\n'
    formatted_item += f'{item.item_descr}'
    if item.item_action is not None and item.item_action.action_name:
        item_action = item.item_action
        formatted_item += '\n'
        formatted_item += f'> - **{item_action.action_name}**: '
        if item_action.action_timing:
            formatted_item += f' {item_action.action_timing} '
        if item_action.action_costs:
            formatted_item += f'- Cost: '
            costs = []
            for cost in item_action.action_costs:
                game_res_defs = game.get_resource_definitions()
                if cost.res_name in game_res_defs:
                    res_def_display_name = game_res_defs[cost.res_name].emoji_text
                else:
                    res_def_display_name = cost.res_name
                costs.append(f'{cost.amount} {res_def_display_name}')
            formatted_item += ' + '.join(costs) + " "
        if item_action.action_uses and item_action.action_uses != -1:
            uses_emoji = await convert_uses_to_emoji(item_action.action_uses)
            formatted_item += f'- {uses_emoji} '
        formatted_item += f'- {item_action.action_desc}'
    formatted_item += '\n'
    return formatted_item
