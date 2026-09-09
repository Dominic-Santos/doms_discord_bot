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
        self.author = interaction.user
        self.user = interaction.user
        self.bot = interaction.client

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
    def __init__(self, title, fields, handler, logger_instance=None):
        super().__init__(title=title)
        self.handler = handler
        self.logger = logger_instance or logger
        self.inputs = {}
        self.converters = {}

        for field in fields:
            name = field[0]
            input_field = discord.ui.InputText(
                label=field[1],
                placeholder=field[2],
                required=True,
                value=field[4] if len(field) > 4 else None,
            )
            self.inputs[name] = input_field
            self.converters[name] = field[3]
            self.add_item(input_field)

    async def callback(self, interaction: discord.Interaction):
        self.logger.info("Modal submitted: %s", self.title)
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

    async def on_error(self, error, interaction):
        self.logger.error("Modal submission failed", exc_info=error)