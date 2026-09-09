import unittest
from unittest.mock import AsyncMock, MagicMock

from src.chat_prompts import PromptContext, run_chat_prompt, send_prompt


class TestChatPrompts(unittest.IsolatedAsyncioTestCase):
    async def test_send_prompt_uses_initial_response_then_followup(self):
        ctx = MagicMock()
        ctx.response.is_done.side_effect = [False, True]
        ctx.respond = AsyncMock()
        ctx.followup.send = AsyncMock()

        await send_prompt(ctx, "first", ephemeral=True)
        await send_prompt(ctx, "second", ephemeral=True)

        ctx.respond.assert_awaited_once_with("first", ephemeral=True)
        ctx.followup.send.assert_awaited_once_with(
            "second", ephemeral=True
        )

    async def test_run_chat_prompt_converts_integer_and_calls_handler(self):
        ctx = MagicMock()
        ctx.response.is_done.return_value = False
        ctx.respond = AsyncMock()
        ctx.followup.send = AsyncMock()
        ctx.author.id = 1
        ctx.channel.id = 2
        ctx.bot.wait_for = AsyncMock(
            side_effect=[
                MagicMock(
                    author=MagicMock(id=1),
                    channel=MagicMock(id=2),
                    content="Ash Ketchum",
                    delete=AsyncMock(),
                ),
                MagicMock(
                    author=MagicMock(id=1),
                    channel=MagicMock(id=2),
                    content="123",
                    delete=AsyncMock(),
                ),
            ]
        )
        handler = AsyncMock()

        await run_chat_prompt(
            ctx,
            [("name", "Name", str), ("pokemon_id", "ID", int)],
            handler,
        )

        handler.assert_awaited_once()
        assert handler.await_args.args[1] == {
            "name": "Ash Ketchum",
            "pokemon_id": 123,
        }
        assert isinstance(handler.await_args.args[0], PromptContext)