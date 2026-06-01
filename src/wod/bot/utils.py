"""Utility functions for Telegram Bot handlers."""

from __future__ import annotations

import logging
from typing import Any

from telegram import Message, Update

logger = logging.getLogger(__name__)


def split_message_text(
    text: str, max_chars: int = 4000, wrap_code: bool = True
) -> list[str]:
    """Split a string into chunks of at most `max_chars` length.

    Aimed at splitting telegram messages nicely by avoiding line splits where possible.
    If `wrap_code` is True, each chunk is wrapped in ```code blocks.
    """
    if not text:
        return []

    lines = text.split("\n")
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    wrapper_len = 8 if wrap_code else 0  # "```\n" + "\n```"

    for line in lines:
        # Length of this line with a newline character
        line_len = len(line) + 1

        if current_length + line_len + wrapper_len > max_chars:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0

            # If a single line exceeds the limit itself, split it hard
            if line_len + wrapper_len > max_chars:
                sub_chars = max_chars - wrapper_len - 1
                for i in range(0, len(line), sub_chars):
                    chunks.append(line[i : i + sub_chars])
                continue

        current_chunk.append(line)
        current_length += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


async def send_workout_text(
    update: Update,
    text: str,
    reply_markup: Any = None,
    parse_mode: str = "Markdown",
) -> None:
    """Send formatted workout text safely, splitting if it exceeds limit.

    If update contains a callback query, the first chunk will edit the message,
    and subsequent chunks will be sent as follow-up replies.
    The `reply_markup` is attached ONLY to the last chunk.
    """
    chunks = split_message_text(text, max_chars=4000, wrap_code=True)
    if not chunks:
        return

    formatted_chunks = [f"```\n{chunk}\n```" for chunk in chunks]
    total_chunks = len(formatted_chunks)

    query = update.callback_query

    if query:
        # Edit the callback query message for the first chunk
        is_last = total_chunks == 1
        await query.edit_message_text(
            text=formatted_chunks[0],
            parse_mode=parse_mode,
            reply_markup=reply_markup if is_last else None,
        )
        # Send subsequent chunks as replies to the parent message
        for i in range(1, total_chunks):
            is_last = i == total_chunks - 1
            assert query.message is not None
            if isinstance(query.message, Message):
                await query.message.reply_text(
                    text=formatted_chunks[i],
                    parse_mode=parse_mode,
                    reply_markup=reply_markup if is_last else None,
                )
    else:
        # Direct command message
        assert update.message is not None
        for i, chunk in enumerate(formatted_chunks):
            is_last = i == total_chunks - 1
            await update.message.reply_text(
                text=chunk,
                parse_mode=parse_mode,
                reply_markup=reply_markup if is_last else None,
            )
