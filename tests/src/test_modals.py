import unittest
from unittest.mock import AsyncMock, MagicMock

from src.modals import CommandModal, ModalInteractionContext, choice_converter


class TestCommandModal(unittest.IsolatedAsyncioTestCase):
    async def test_modal_on_error_logs(self):
        logger = MagicMock()
        modal = CommandModal("Test", [], AsyncMock(), logger)
        await modal.on_error(Exception("failed"), MagicMock())
        logger.error.assert_called_once()

    async def test_context_responds_before_and_after_defer(self):
        response = MagicMock()
        response.is_done.side_effect = [False, True]
        response.send_message = AsyncMock()
        response.defer = AsyncMock()
        followup = MagicMock()
        followup.send = AsyncMock()
        interaction = MagicMock(response=response, followup=followup)
        context = ModalInteractionContext(interaction)

        assert context.guild == interaction.guild
        assert context.author == interaction.user
        assert context.user == interaction.user
        assert context.bot == interaction.client
        await context.respond("first", ephemeral=True)
        await context.defer(ephemeral=True)
        await context.respond("second", ephemeral=True)

        response.send_message.assert_awaited_once_with(
            "first", ephemeral=True
        )
        response.defer.assert_awaited_once_with(ephemeral=True)
        followup.send.assert_awaited_once_with(
            "second", ephemeral=True
        )

    def test_choice_converter(self):
        convert = choice_converter("standard", "expanded")
        assert convert("standard") == "standard"
        with self.assertRaises(ValueError):
            convert("unlimited")

    async def test_submit_converts_values_and_calls_handler(self):
        handler = AsyncMock()
        modal = CommandModal(
            "Test form",
            [("count", "Count", "42", int)],
            handler,
        )
        modal.inputs["count"].value = "42"

        interaction = MagicMock()
        await modal.callback(interaction)

        handler.assert_awaited_once()
        values = handler.await_args.args[1]
        assert values == {"count": 42}

    async def test_context_respond_allows_file_attachment(self):
        response = MagicMock()
        response.is_done.return_value = False
        response.send_message = AsyncMock()
        interaction = MagicMock(response=response)
        context = ModalInteractionContext(interaction)
        file_obj = object()

        await context.respond("done", file=file_obj)

        response.send_message.assert_awaited_once_with(
            "done",
            ephemeral=False,
            file=file_obj,
        )

    async def test_submit_reports_invalid_values(self):
        handler = AsyncMock()
        modal = CommandModal(
            "Test form",
            [("count", "Count", "42", int)],
            handler,
        )
        modal.inputs["count"].value = "not a number"

        interaction = MagicMock()
        interaction.response.send_message = AsyncMock()
        await modal.callback(interaction)

        interaction.response.send_message.assert_awaited_once_with(
            "Invalid value for count.",
            ephemeral=True,
        )
        handler.assert_not_awaited()
