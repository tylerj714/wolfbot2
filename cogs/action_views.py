import discord
from discord import app_commands


class ActionButtons(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Button", style=discord.ButtonStyle.gray)
    async def gray_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(content=f"This is an edited button response!")


@app_commands.command()
async def button(ctx):
    await ctx.send("This message has buttons!", view=ActionButtons())
