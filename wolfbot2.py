# wolfbot.py
import discord
from discord.ext import commands
from discord import app_commands
from bot_logging.logging_manager import logger
from dom.conf_vars import ConfVars as Conf

class WolfBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=discord.Intents.all(), help_command=None)
        self.synced = False

    async def setup_hook(self):
        await self.load_extension(f"cogs.test")
        await self.load_extension(f"cogs.game_management")
        await self.load_extension(f"cogs.player_management")
        await self.load_extension(f"cogs.voting")
        await self.load_extension(f"cogs.dice_rolling")
        await bot.tree.sync(guild=discord.Object(id=Conf.GUILD_ID))

    async def on_ready(self):
        await self.wait_until_ready()
        print(f"We have logged in as {self.user}.")

bot = WolfBot()

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Cooldown is in force, please wait for {round(error.retry_after)} seconds", ephemeral=True)
    else:
        raise error


def log_interaction_call(interaction: discord.Interaction):
    logger.info(f'Received command {interaction.command.name} with parameters {interaction.data} initiated by user {interaction.user.name}')


bot.run(Conf.TOKEN)
