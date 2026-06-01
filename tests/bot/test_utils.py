"""Tests for the bot utility functions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Message, Update

from wod.bot.utils import send_workout_text, split_message_text


class TestSplitMessageText:
    """Tests for split_message_text."""

    def test_empty_string(self) -> None:
        result = split_message_text("")
        assert not result
        assert isinstance(result, list)

    def test_short_string(self) -> None:
        text = "Hello\nWorld"
        chunks = split_message_text(text, max_chars=100, wrap_code=False)
        assert chunks == ["Hello\nWorld"]

    def test_split_by_line(self) -> None:
        # Wrap code is False to make length calculations simpler
        text = "Line1\nLine2\nLine3\nLine4"
        # Each line has length 5. Line with separator length is 6.
        # Max chars 13 should fit at most 2 lines (Line1\nLine2 is 11 chars).
        chunks = split_message_text(text, max_chars=13, wrap_code=False)
        assert chunks == ["Line1\nLine2", "Line3\nLine4"]

    def test_split_by_line_with_wrap_code(self) -> None:
        text = "Line1\nLine2"
        # wrapper_len is 8. "Line1\n" + wrap_code = 6 + 8 = 14.
        # Max chars 20 should easily fit everything in one chunk
        chunks = split_message_text(text, max_chars=20, wrap_code=True)
        assert chunks == ["Line1\nLine2"]

    def test_single_extremely_long_line(self) -> None:
        # Single line of length 30
        text = "A" * 30
        # max_chars = 15. wrapper_len = 0.
        chunks = split_message_text(text, max_chars=15, wrap_code=False)
        assert chunks == ["A" * 14, "A" * 14, "AA"]


class TestSendWorkoutText:
    """Tests for send_workout_text."""

    @pytest.mark.asyncio
    async def test_send_single_chunk_command(self) -> None:
        # Arrange
        update = MagicMock(spec=Update)
        update.callback_query = None
        update.message = AsyncMock()

        text = "Hello workout"
        reply_markup = MagicMock()

        # Act
        await send_workout_text(update, text, reply_markup=reply_markup)

        # Assert
        update.message.reply_text.assert_called_once_with(
            text="```\nHello workout\n```",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

    @pytest.mark.asyncio
    async def test_send_multiple_chunks_command(self) -> None:
        # Arrange
        update = MagicMock(spec=Update)
        update.callback_query = None
        update.message = AsyncMock()

        # Generate a text that will split (e.g., limit set to 4000, we make a long text)
        # Or let's mock split_message_text in our test, but we can also just pass a text
        # that naturally splits if we mock the helper, or just use a long text.
        # Actually, let's just make the text long enough to split or we can use patch!
        # Let's use patch to mock split_message_text to return two controlled chunks.

        chunks = ["Part 1", "Part 2"]
        reply_markup = MagicMock()

        with patch("wod.bot.utils.split_message_text", return_value=chunks):
            # Act
            await send_workout_text(
                update, "some dummy text", reply_markup=reply_markup
            )

        # Assert
        assert update.message.reply_text.call_count == 2
        update.message.reply_text.assert_any_call(
            text="```\nPart 1\n```",
            parse_mode="Markdown",
            reply_markup=None,
        )
        update.message.reply_text.assert_any_call(
            text="```\nPart 2\n```",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

    @pytest.mark.asyncio
    async def test_send_single_chunk_callback_query(self) -> None:
        # Arrange
        update = MagicMock(spec=Update)
        query = AsyncMock()
        update.callback_query = query
        query.message = AsyncMock(spec=Message)

        text = "Hello workout"
        reply_markup = MagicMock()

        # Act
        await send_workout_text(update, text, reply_markup=reply_markup)

        # Assert
        query.edit_message_text.assert_called_once_with(
            text="```\nHello workout\n```",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
        query.message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_multiple_chunks_callback_query(self) -> None:
        # Arrange
        update = MagicMock(spec=Update)
        query = AsyncMock()
        update.callback_query = query
        query.message = AsyncMock(spec=Message)

        chunks = ["Part 1", "Part 2", "Part 3"]
        reply_markup = MagicMock()

        with patch("wod.bot.utils.split_message_text", return_value=chunks):
            # Act
            await send_workout_text(
                update, "some dummy text", reply_markup=reply_markup
            )

        # Assert
        query.edit_message_text.assert_called_once_with(
            text="```\nPart 1\n```",
            parse_mode="Markdown",
            reply_markup=None,
        )
        assert query.message.reply_text.call_count == 2
        query.message.reply_text.assert_any_call(
            text="```\nPart 2\n```",
            parse_mode="Markdown",
            reply_markup=None,
        )
        query.message.reply_text.assert_any_call(
            text="```\nPart 3\n```",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
