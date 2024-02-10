
import time
from typing import Optional, List, Literal
from discord import Guild
from dom.data_model import Player, Action, Item
import utils.string_decorator as sdec


async def construct_action_display(guild: Guild, player: Optional[Player] = None, actions: Optional[List[Action]] = None,
                                   from_spellbook: bool = False) -> List[str]:
    if actions is None:
        actions = []

    formatted_responses = []
    formatted_action_header = ""

    if from_spellbook:
        formatted_action_header += ""
    elif player is not None:
        formatted_action_header += f'**Player {player.player_discord_name} Actions as of <t:{int(time.time())}>**\n'
    else:
        formatted_action_header += f'**Actions as of <t:{int(time.time())}>**\n'
    formatted_responses.append(await sdec.format_text(text=formatted_action_header, guild=guild))

    if actions is None and player is not None:
        actions = player.player_actions

    if actions:
        formatted_actions = ""
        for action in actions:
            this_formatted_action = await format_action(action)
            if len(formatted_actions) + len(this_formatted_action) <= 1900:
                formatted_actions += this_formatted_action
            else:
                formatted_responses.append(await sdec.format_text(text=formatted_actions, guild=guild))
                formatted_actions = ""
                formatted_actions += this_formatted_action
        formatted_responses.append(await sdec.format_text(text=formatted_actions, guild=guild))
    else:
        formatted_responses.append(await sdec.format_text(text=f'*<No Actions!>*', guild=guild))

    return formatted_responses


async def construct_action_change_display(guild: Guild, status: Literal['gained', 'lost'], action: Action) -> List[str]:
    formatted_responses = []
    formatted_action_change = ""

    if status == 'gained':
        formatted_action_change += f'You have been **granted** the action **{action.action_name}**:\n'
        formatted_action_change += await format_action(action)
    else:
        formatted_action_change += f'You have **lost** the action **{action.action_name}**!\n'

    formatted_responses.append(await sdec.format_text(text=formatted_action_change, guild=guild))

    return formatted_responses


async def format_action(action: Action) -> str:
    formatted_action = f'- **{action.action_name}**:'
    if action.action_timing:
        formatted_action += f' {action.action_timing} '
    if action.action_costs:
        formatted_action += f'- Cost: {action.action_costs} '
    if action.action_uses:
        formatted_action += f'- {action.action_uses} '
    formatted_action += f'- {action.action_desc}'
    formatted_action += '\n'
    return formatted_action


async def construct_item_display(guild: Guild, player: Optional[Player] = None, items: Optional[List[Item]] = None,
                                 from_spellbook: bool = False) -> List[str]:
    if items is None:
        items = []

    formatted_responses = []
    formatted_item_header = ""

    if from_spellbook:
        formatted_item_header += ""
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
            this_formatted_item = await format_item(item)
            if len(formatted_items) + len(this_formatted_item) <= 1900:
                formatted_items += this_formatted_item
            else:
                formatted_responses.append(await sdec.format_text(text=formatted_items, guild=guild))
                formatted_items = ""
                formatted_items += this_formatted_item
        formatted_responses.append(await sdec.format_text(text=formatted_items, guild=guild))
    else:
        formatted_responses.append(await sdec.format_text(text=f'*<No items!>*', guild=guild))

    return formatted_responses


async def construct_item_transfer_display(guild: Guild, action: Literal['gained', 'lost'], item: Item) -> List[str]:
    formatted_responses = []
    formatted_item = ""

    if action == 'gained':
        formatted_item += f'You have **gained possession** of the item **{item.item_name}**:\n'
        formatted_item += await format_item(item)
    else:
        formatted_item += f'You have **lost possession** of the item **{item.item_name}**!\n'

    formatted_responses.append(await sdec.format_text(text=formatted_item, guild=guild))

    return formatted_responses


async def format_item(item: Item) -> str:
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
            formatted_item += f'- Cost: {item_action.action_costs} '
        if item_action.action_uses:
            formatted_item += f'- {item_action.action_uses} '
        formatted_item += f'- {item_action.action_desc}'
    formatted_item += '\n'
    return formatted_item
