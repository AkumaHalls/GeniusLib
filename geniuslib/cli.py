"""Command-line interface for GeniusLib.

Usage::

    geniuslib player #TAG
    geniuslib clan #TAG
    geniuslib war #CLAN_TAG
    geniuslib raid #CLAN_TAG
    geniuslib search --name "clan name"
    geniuslib export #TAG --format json
    geniuslib compare player #TAG1 #TAG2
"""

import argparse
import asyncio
import json
import sys
from typing import Optional

from . import Client
from .formatters import (
    format_player_brief, format_clan_brief, format_clan_detailed,
    format_war_state, format_war_result, format_war_score,
    format_raid_brief, format_member_brief,
)
from .war_analytics import get_war_result, count_missed_attacks
from .raid_analytics import raid_summary


def _parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="geniuslib",
        description="GeniusLib - Clash of Clans API CLI",
    )
    parser.add_argument("--email", help="Developer site email")
    parser.add_argument("--password", help="Developer site password")
    parser.add_argument("--token", help="API token (alternative to email/password)")

    sub = parser.add_subparsers(dest="command")

    p_player = sub.add_parser("player", help="Get player info")
    p_player.add_argument("tag", help="Player tag (e.g. #ABC123)")

    p_clan = sub.add_parser("clan", help="Get clan info")
    p_clan.add_argument("tag", help="Clan tag")
    p_clan.add_argument("--members", action="store_true", help="List members")

    p_war = sub.add_parser("war", help="Get current war info")
    p_war.add_argument("tag", help="Clan tag")

    p_raid = sub.add_parser("raid", help="Get latest raid info")
    p_raid.add_argument("tag", help="Clan tag")

    p_search = sub.add_parser("search", help="Search clans")
    p_search.add_argument("--name", help="Clan name")
    p_search.add_argument("--min-members", type=int, help="Min members")
    p_search.add_argument("--max-members", type=int, help="Max members")
    p_search.add_argument("--min-level", type=int, help="Min clan level")
    p_search.add_argument("--limit", type=int, default=5, help="Result limit")

    p_export = sub.add_parser("export", help="Export data")
    p_export.add_argument("tag", help="Player or clan tag")
    p_export.add_argument("--type", choices=["player", "clan"], default="player")
    p_export.add_argument("--format", choices=["json", "csv"], default="json")

    p_compare = sub.add_parser("compare", help="Compare players or clans")
    p_compare.add_argument("type", choices=["player", "clan"])
    p_compare.add_argument("tag1", help="First tag")
    p_compare.add_argument("tag2", help="Second tag")

    return parser.parse_args(argv)


def _print_json(data) -> None:
    print(json.dumps(data, indent=2, default=str))


async def _login(args) -> Client:
    client = Client()
    if args.token:
        await client.login_with_tokens(args.token)
    elif args.email and args.password:
        await client.login(args.email, args.password)
    else:
        print("Use --email/--password or --token to authenticate", file=sys.stderr)
        sys.exit(1)
    return client


async def _cmd_player(client: Client, args) -> None:
    player = await client.get_player(args.tag)
    print(format_player_brief(player))
    print(f"  Nível: {player.exp_level}")
    print(f"  Clã: {player.clan.name if player.clan else 'Nenhum'}")
    print(f"  Estrelas de guerra: {player.war_stars}")
    if hasattr(player, "attack_wins"):
        print(f"  Ataques vitoriosos: {player.attack_wins}")
    if hasattr(player, "defense_wins"):
        print(f"  Defesas vitoriosas: {player.defense_wins}")


async def _cmd_clan(client: Client, args) -> None:
    clan = await client.get_clan(args.tag)
    print(format_clan_detailed(clan))
    print(f"  Descrição: {clan.description[:100] if clan.description else 'N/A'}...")
    print(f"  Guerra: {format_war_state(clan.war_state)}")
    print(f"  Liga: {clan.war_league.name if clan.war_league else 'N/A'}")

    if args.members and clan.members:
        print(f"\nMembros ({len(clan.members)}):")
        for m in sorted(clan.members, key=lambda x: x.trophies, reverse=True):
            status = "✅" if getattr(m, "war_opted_in", False) else "⬜"
            print(f"  {status} {format_member_brief(m)}")


async def _cmd_war(client: Client, args) -> None:
    war = await client.get_current_war(args.tag)
    if war is None:
        print("Clã não está em guerra no momento.")
        return
    print(f"Estado: {format_war_state(war.state)}")
    print(f"Resultado: {format_war_result(war, args.tag)}")
    print(f"Placar: {format_war_score(war, args.tag)}")
    missed = count_missed_attacks(war, args.tag)
    print(f"Ataques perdidos: {missed}")


async def _cmd_raid(client: Client, args) -> None:
    logs = await client.get_raid_log(args.tag, limit=1)
    if not logs:
        print("Nenhum raid encontrado.")
        return
    [entry] = logs
    summary = raid_summary(entry)
    _print_json(summary)


async def _cmd_search(client: Client, args) -> None:
    kwargs = {}
    if args.name:
        kwargs["name"] = args.name
    if args.min_members:
        kwargs["min_members"] = args.min_members
    if args.max_members:
        kwargs["max_members"] = args.max_members
    if args.min_level:
        kwargs["min_clan_level"] = args.min_level

    clans = await client.search_clans(limit=args.limit, **kwargs)
    if not clans:
        print("Nenhum clã encontrado.")
        return
    for clan in clans:
        print(f"  {format_clan_brief(clan)}")
        print(f"    {clan.war_league.name if clan.war_league else 'N/A'}")


async def _cmd_export(client: Client, args) -> None:
    if args.type == "player":
        data = await client.get_player(args.tag)
    else:
        data = await client.get_clan(args.tag)

    raw = data._raw_data if hasattr(data, "_raw_data") else {}

    if args.format == "json":
        print(json.dumps(raw, indent=2, default=str))
    else:
        if args.type == "player":
            print("tag,name,town_hall,trophies,exp_level,clan")
            clan_name = (raw.get("clan") or {}).get("name", "")
            print(f"{raw.get('tag')},{raw.get('name')},{raw.get('townHallLevel')},"
                  f"{raw.get('trophies')},{raw.get('expLevel')},{clan_name}")
        else:
            print("tag,name,level,members,points")
            print(f"{raw.get('tag')},{raw.get('name')},{raw.get('clanLevel')},"
                  f"{raw.get('members')},{raw.get('clanPoints')}")


async def _cmd_compare(client: Client, args) -> None:
    if args.type == "player":
        p1 = await client.get_player(args.tag1)
        p2 = await client.get_player(args.tag2)
        print("Atributo            | Player 1          | Player 2")
        print("-" * 55)
        rows = [
            ("Nome", p1.name, p2.name),
            ("Tag", p1.tag, p2.tag),
            ("TH", str(p1.town_hall), str(p2.town_hall)),
            ("Troféus", str(p1.trophies), str(p2.trophies)),
            ("Nível", str(p1.exp_level), str(p2.exp_level)),
            ("Estrelas Guerra", str(p1.war_stars), str(p2.war_stars)),
        ]
        for label, v1, v2 in rows:
            print(f"  {label:20s} | {v1:18s} | {v2}")
    else:
        c1 = await client.get_clan(args.tag1)
        c2 = await client.get_clan(args.tag2)
        print("Atributo            | Clã 1              | Clã 2")
        print("-" * 55)
        rows = [
            ("Nome", c1.name, c2.name),
            ("Tag", c1.tag, c2.tag),
            ("Nível", str(c1.level), str(c2.level)),
            ("Membros", str(c1.member_count), str(c2.member_count)),
            ("Troféus", str(c1.points), str(c2.points)),
        ]
        for label, v1, v2 in rows:
            print(f"  {label:20s} | {v1:18s} | {v2}")


COMMANDS = {
    "player": _cmd_player,
    "clan": _cmd_clan,
    "war": _cmd_war,
    "raid": _cmd_raid,
    "search": _cmd_search,
    "export": _cmd_export,
    "compare": _cmd_compare,
}


async def main(argv: Optional[list] = None) -> None:
    args = _parse_args(argv)
    if args.command is None:
        _parse_args(["--help"])
        return

    client = await _login(args)
    try:
        cmd = COMMANDS.get(args.command)
        if cmd:
            await cmd(client, args)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
