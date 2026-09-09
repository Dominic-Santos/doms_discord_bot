import logging

import discord


logger = logging.getLogger(__name__)


def choice_converter(*allowed_values):
    def convert(value):
        if value not in allowed_values:
            raise ValueError
        return value

    return convert


class ModalInteractionContext:
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction

    def __getattr__(self, name):
        return getattr(self.interaction, name)

    async def defer(self, ephemeral=False):
        await self.interaction.response.defer(ephemeral=ephemeral)

    async def respond(self, message, ephemeral=False):
        if self.interaction.response.is_done():
            await self.interaction.followup.send(
                message,
                ephemeral=ephemeral
            )
            return

        await self.interaction.response.send_message(
            message,
            ephemeral=ephemeral
        )


class CommandModal(discord.ui.Modal):
    def __init__(self, title, fields, handler):
        super().__init__(title=title)
        self.handler = handler
        self.inputs = {}
        self.converters = {}

        for field in fields:
            name = field[0]
            input_field = discord.ui.InputText(
                label=field[1],
                placeholder=field[2],
                required=True,
            )
            self.inputs[name] = input_field
            self.converters[name] = field[3]
            self.add_item(input_field)

    async def on_submit(self, interaction: discord.Interaction):
        values = {}
        for name, input_field in self.inputs.items():
            try:
                values[name] = self.converters[name](input_field.value)
            except ValueError:
                await interaction.response.send_message(
                    f"Invalid value for {name}.",
                    ephemeral=True
                )
                return

        await self.handler(ModalInteractionContext(interaction), values)

    async def on_error(self, error, item, interaction):
        logger.exception("Modal submission failed", exc_info=error)