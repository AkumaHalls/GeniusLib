"""Batch Fetch — fetch multiple clans and players in parallel.

Demonstrates GeniusLib's parallel fetching capabilities:
- ClanIterator for batch clan lookups
- PlayerIterator for batch player lookups
- asyncio.gather for ad-hoc parallel requests
"""

import asyncio
import os
import time

from geniuslib import Client, ClanIterator, PlayerIterator

COC_EMAIL = os.environ.get("COC_EMAIL", "seu_email@exemplo.com")
COC_PASSWORD = os.environ.get("COC_PASSWORD", "sua_senha")


async def batch_clans():
    """Fetch multiple clans using ClanIterator."""
    async with Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)

        tags = [
            "#2PP",      # Bitter Work
            "#CRCY8RQ", # Some clan
            "#QJ8YJQ2", # Another clan
        ]

        print("=== Batch Clan Fetch ===")
        start = time.perf_counter()

        async for clan in ClanIterator(client, tags):
            print(f"  {clan.name} ({clan.tag}) — Level {clan.level}, {clan.member_count}/50 members")

        elapsed = time.perf_counter() - start
        print(f"  Fetched {len(tags)} clans in {elapsed:.2f}s\n")


async def batch_players():
    """Fetch multiple players using PlayerIterator."""
    async with Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)

        tags = ["#PQU80VUJ", "#YJV2808UQ", "#28QUYJCJR"]

        print("=== Batch Player Fetch ===")
        start = time.perf_counter()

        async for player in PlayerIterator(client, tags):
            clan = player.clan.name if player.clan else "No clan"
            print(f"  {player.name} ({player.tag}) — TH{player.town_hall}, {player.trophies} trophies, {clan}")

        elapsed = time.perf_counter() - start
        print(f"  Fetched {len(tags)} players in {elapsed:.2f}s\n")


async def parallel_gather():
    """Ad-hoc parallel fetch using asyncio.gather."""
    async with Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)

        print("=== Parallel Gather ===")
        start = time.perf_counter()

        # Mix different request types in parallel
        player, clan, war = await asyncio.gather(
            client.get_player("#PQU80VUJ"),
            client.get_clan("#2PP"),
            client.get_current_war("#2PP"),
            return_exceptions=True,
        )

        elapsed = time.perf_counter() - start

        if not isinstance(player, Exception):
            print(f"  Player: {player.name} — TH{player.town_hall}")
        if not isinstance(clan, Exception):
            print(f"  Clan: {clan.name} — Level {clan.level}")
        if not isinstance(war, Exception) and war is not None:
            print(f"  War: {war.clan.name} vs {war.opponent.name}")
        elif war is None:
            print("  War: Not in war")

        print(f"  3 parallel requests in {elapsed:.2f}s\n")


async def main():
    await batch_clans()
    await batch_players()
    await parallel_gather()


if __name__ == "__main__":
    asyncio.run(main())
