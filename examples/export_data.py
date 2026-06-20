"""Export example — como exportar dados em JSON, CSV, dict.

Uso: python export_data.py <tag> [--format json|csv]
"""

import asyncio
import argparse
import os
import sys

from geniuslib import Client
from geniuslib.exporter import to_json, to_csv

COC_EMAIL = os.environ.get("COC_EMAIL", "seu_email@exemplo.com")
COC_PASSWORD = os.environ.get("COC_PASSWORD", "sua_senha")


async def export_player(tag: str, fmt: str = "json") -> None:
    async with Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)
        player = await client.get_player(tag)

        if fmt == "json":
            print(to_json(player))
        else:
            print(to_csv(player, "player"))


async def export_clan(tag: str, fmt: str = "json") -> None:
    async with Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)
        clan = await client.get_clan(tag)

        if fmt == "json":
            print(to_json(clan))
        else:
            print(to_csv(clan, "clan"))


async def main():
    parser = argparse.ArgumentParser(description="GeniusLib Export Example")
    parser.add_argument("tag", help="Player or clan tag")
    parser.add_argument("--type", choices=["player", "clan"], default="player")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    args = parser.parse_args()

    if args.type == "player":
        await export_player(args.tag, args.format)
    else:
        await export_clan(args.tag, args.format)


if __name__ == "__main__":
    asyncio.run(main())
