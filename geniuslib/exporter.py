"""Data export module for GeniusLib.

Provides methods to export player, clan, war, and raid data
to JSON, CSV, and dict formats.

Usage::

    from geniuslib.exporter import to_json, to_csv, to_dict

    player = await client.get_player("#TAG")
    print(to_json(player))
    print(to_csv(player, "player"))
"""

import csv
import io
import json
from typing import Any, List


def to_json(obj, indent: int = 2) -> str:
    """Export a GeniusLib object to a JSON string.

    Extracts ``_raw_data`` if available, otherwise serializes
    public attributes.

    Parameters
    ----------
    obj : Any
        Any GeniusLib model instance (Player, Clan, ClanWar, etc.).
    indent : int
        JSON indentation level. Defaults to 2.

    Returns
    -------
    str
        Pretty-printed JSON string.
    """
    data = _extract_data(obj)
    return json.dumps(data, indent=indent, default=str, ensure_ascii=False)


def to_dict(obj) -> dict:
    """Export a GeniusLib object to a plain dictionary.

    Parameters
    ----------
    obj : Any
        Any GeniusLib model instance.

    Returns
    -------
    dict
        Dictionary representation of the object.
    """
    return _extract_data(obj)


def to_csv(obj, obj_type: str = "player") -> str:
    """Export a GeniusLib object to a CSV string.

    Parameters
    ----------
    obj : Any
        The model instance.
    obj_type : str
        Type of object: ``"player"``, ``"clan"``, ``"war"``, ``"raid"``.

    Returns
    -------
    str
        CSV-formatted string.
    """
    output = io.StringIO()
    data = _extract_data(obj)

    if obj_type == "player":
        writer = csv.DictWriter(output, fieldnames=_PLAYER_FIELDS)
        writer.writeheader()
        writer.writerow(_flatten_player(data))

    elif obj_type == "clan":
        writer = csv.DictWriter(output, fieldnames=_CLAN_FIELDS)
        writer.writeheader()
        writer.writerow(_flatten_clan(data))

        if "members" in data:
            output.write("\n--- Members ---\n")
            mwriter = csv.DictWriter(output, fieldnames=_MEMBER_FIELDS)
            mwriter.writeheader()
            for m in data["members"]:
                mwriter.writerow(_flatten_member(m))

    elif obj_type == "war":
        writer = csv.DictWriter(output, fieldnames=_WAR_FIELDS)
        writer.writeheader()
        writer.writerow(_flatten_war(data))

    elif obj_type == "raid":
        writer = csv.DictWriter(output, fieldnames=_RAID_FIELDS)
        writer.writeheader()
        writer.writerow(_flatten_raid(data))

    return output.getvalue()


def export_players(players: list, format: str = "json") -> str:
    """Export a list of players.

    Parameters
    ----------
    players : list
        List of player objects.
    format : str
        ``"json"`` or ``"csv"``.

    Returns
    -------
    str
        Formatted string.
    """
    data = [_extract_data(p) for p in players]
    if format == "csv":
        return _list_to_csv(data, _PLAYER_FIELDS)
    return json.dumps(data, indent=2, default=str, ensure_ascii=False)


def export_clans(clans: list, format: str = "json") -> str:
    """Export a list of clans."""
    data = [_extract_data(c) for c in clans]
    if format == "csv":
        return _list_to_csv(data, _CLAN_FIELDS)
    return json.dumps(data, indent=2, default=str, ensure_ascii=False)


# --- Internal helpers ---

_PLAYER_FIELDS = [
    "tag",
    "name",
    "town_hall",
    "trophies",
    "exp_level",
    "war_stars",
    "attack_wins",
    "defense_wins",
    "clan",
]

_CLAN_FIELDS = [
    "tag",
    "name",
    "level",
    "member_count",
    "points",
    "builder_base_points",
    "description",
    "war_league",
]

_MEMBER_FIELDS = [
    "tag",
    "name",
    "role",
    "town_hall",
    "trophies",
    "donations",
    "donations_received",
]

_WAR_FIELDS = [
    "state",
    "clan_name",
    "clan_tag",
    "clan_stars",
    "opponent_name",
    "opponent_tag",
    "opponent_stars",
    "attacks_per_member",
]

_RAID_FIELDS = [
    "state",
    "start_time",
    "end_time",
    "total_loot",
    "completed_raid_count",
    "attack_count",
    "destroyed_district_count",
]


def _extract_data(obj) -> dict:
    if hasattr(obj, "_raw_data") and obj._raw_data:
        return obj._raw_data
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    # Try to extract from __slots__ if present (models with __slots__)
    slots = getattr(obj.__class__, "__slots__", None)
    if slots:
        result = {}
        for s in slots:
            if s.startswith("_"):
                continue
            try:
                result[s] = getattr(obj, s)
            except AttributeError:
                continue
        if result:
            return result
    return {}


def _flatten_player(data: dict) -> dict:
    clan_name = ""
    if data.get("clan") and isinstance(data["clan"], dict):
        clan_name = data["clan"].get("name", "")
    elif hasattr(data.get("clan"), "name"):
        clan_name = data["clan"].name
    return {
        "tag": data.get("tag", ""),
        "name": data.get("name", ""),
        "town_hall": data.get("townHallLevel") or data.get("town_hall", 0),
        "trophies": data.get("trophies", 0),
        "exp_level": data.get("expLevel") or data.get("exp_level", 0),
        "war_stars": data.get("warStars") or data.get("war_stars", 0),
        "attack_wins": data.get("attackWins") or data.get("attack_wins", 0),
        "defense_wins": data.get("defenseWins") or data.get("defense_wins", 0),
        "clan": clan_name,
    }


def _flatten_clan(data: dict) -> dict:
    return {
        "tag": data.get("tag", ""),
        "name": data.get("name", ""),
        "level": data.get("clanLevel") or data.get("level", 0),
        "member_count": data.get("members") or data.get("member_count", 0),
        "points": data.get("clanPoints") or data.get("points", 0),
        "builder_base_points": data.get("clanBuilderBasePoints") or data.get("builder_base_points", 0),
        "description": (data.get("description") or "")[:50],
        "war_league": data.get("warLeague", {}).get("name", "") if isinstance(data.get("warLeague"), dict) else "",
    }


def _flatten_member(data: dict) -> dict:
    return {
        "tag": data.get("tag", ""),
        "name": data.get("name", ""),
        "role": data.get("role", ""),
        "town_hall": data.get("townHallLevel") or data.get("town_hall", 0),
        "trophies": data.get("trophies", 0),
        "donations": data.get("donations", 0),
        "donations_received": data.get("donationsReceived") or data.get("donations_received", 0),
    }


def _flatten_war(data: dict) -> dict:
    clan = data.get("clan", {}) if isinstance(data.get("clan"), dict) else {}
    opp = data.get("opponent", {}) if isinstance(data.get("opponent"), dict) else {}
    if hasattr(data.get("clan"), "name") and not clan:
        clan = {
            "name": getattr(data.get("clan"), "name", ""),
            "tag": getattr(data.get("clan"), "tag", ""),
            "stars": getattr(data.get("clan"), "stars", 0),
        }
    if hasattr(data.get("opponent"), "name") and not opp:
        opp = {
            "name": getattr(data.get("opponent"), "name", ""),
            "tag": getattr(data.get("opponent"), "tag", ""),
            "stars": getattr(data.get("opponent"), "stars", 0),
        }
    return {
        "state": data.get("state", ""),
        "clan_name": clan.get("name", ""),
        "clan_tag": clan.get("tag", ""),
        "clan_stars": clan.get("stars", 0),
        "opponent_name": opp.get("name", ""),
        "opponent_tag": opp.get("tag", ""),
        "opponent_stars": opp.get("stars", 0),
        "attacks_per_member": data.get("attacksPerMember") or data.get("attacks_per_member", 0),
    }


def _flatten_raid(data: dict) -> dict:
    return {
        "state": data.get("state", ""),
        "start_time": data.get("startTime") or data.get("start_time") or "",
        "end_time": data.get("endTime") or data.get("end_time") or "",
        "total_loot": data.get("capitalTotalLoot") or data.get("total_loot", 0),
        "completed_raid_count": data.get("raidsCompleted") or data.get("completed_raid_count", 0),
        "attack_count": data.get("totalAttacks") or data.get("attack_count", 0),
        "destroyed_district_count": data.get("enemyDistrictsDestroyed") or data.get("destroyed_district_count", 0),
    }


def _list_to_csv(data: List[dict], fields: List[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for item in data:
        writer.writerow({f: _get_field(item, f) for f in fields})
    return output.getvalue()


def _get_field(data: dict, field: str) -> Any:
    """Extract a field from data using multiple possible API key names."""
    mapping = {
        "town_hall": ["townHallLevel", "town_hall"],
        "exp_level": ["expLevel", "exp_level"],
        "war_stars": ["warStars", "war_stars"],
        "level": ["clanLevel", "level"],
        "member_count": ["members", "member_count"],
        "points": ["clanPoints", "points"],
        "versus_points": ["clanVersusPoints", "versus_points"],
        "builder_base_points": ["clanBuilderBasePoints", "builder_base_points"],
        "role": ["role"],
    }
    for key in mapping.get(field, [field]):
        if key in data:
            val = data[key]
            if isinstance(val, dict):
                return val.get("name", "")
            return val
    return ""
