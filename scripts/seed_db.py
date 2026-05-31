"""Seed the database with exercises and equipment from JSON data."""

from __future__ import annotations

import asyncio
import logging

from wod.db.seeding import seed_database

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(seed_database())
