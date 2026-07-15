"""Player and clan comparison module.

Provides functions to compare two players or two clans
side by side, highlighting key differences.
"""

from typing import Any, Dict, List, Optional, Tuple


def compare_players(player1, player2) -> dict:
    """Compare two players and return a dict of differences.

    Parameters
    ----------
    player1
        First player object.
    player2
        Second player object.

    Returns
    -------
    dict
        A dictionary with keys ``"left"``, ``"right"``, and ``"diff"``.
    """
    p1 = _player_stats(player1)
    p2 = _player_stats(player2)
    return {
        "left": {"name": _name(player1), "tag": _tag(player1), **p1},
        "right": {"name": _name(player2), "tag": _tag(player2), **p2},
        "diff": _player_diff(p1, p2),
    }


def compare_clans(clan1, clan2) -> dict:
    """Compare two clans and return a dict of differences."""
    c1 = _clan_stats(clan1)
    c2 = _clan_stats(clan2)
    return {
        "left": {"name": _name(clan1), "tag": _tag(clan1), **c1},
        "right": {"name": _name(clan2), "tag": _tag(clan2), **c2},
        "diff": _clan_diff(c1, c2),
    }


# --- Internal helpers ---


def _name(obj) -> str:
    if hasattr(obj, "name"):
        return obj.name
    if isinstance(obj, dict):
        return obj.get("name", "")
    return str(obj)


def _tag(obj) -> str:
    if hasattr(obj, "tag"):
        return obj.tag
    if isinstance(obj, dict):
        return obj.get("tag", "")
    return ""


def _player_stats(p) -> dict:
    return {
        "town_hall": _attr(p, "town_hall", 0),
        "exp_level": _attr(p, "exp_level", 0),
        "trophies": _attr(p, "trophies", 0),
        "war_stars": _attr(p, "war_stars", 0),
        "attack_wins": _attr(p, "attack_wins", 0),
        "defense_wins": _attr(p, "defense_wins", 0),
        "donations": _attr(p, "donations", 0),
        "clan_name": _attr(p, "clan", "").name if _attr(p, "clan", "") else "",
    }


def _clan_stats(c) -> dict:
    members = _attr(c, "members", [])
    if hasattr(members, "__len__") and not isinstance(members, int):
        member_count = len(members)
    else:
        member_count = int(members) if members else _attr(c, "member_count", 0)
    return {
        "level": _attr(c, "level", 0),
        "member_count": member_count,
        "points": _attr(c, "points", 0),
        "war_wins": _attr(c, "war_wins", 0),
        "war_ties": _attr(c, "war_ties", 0),
        "war_losses": _attr(c, "war_losses", 0),
        "war_league": _attr(c, "war_league", ""),
        "description": (_attr(c, "description", "") or "")[:50],
    }


def _attr(obj, key, default=None):
    """Safely get an attribute or dict key."""
    if hasattr(obj, key):
        return getattr(obj, key, default)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def _player_diff(p1: dict, p2: dict) -> dict:
    return {
        "town_hall": p1["town_hall"] - p2["town_hall"],
        "exp_level": p1["exp_level"] - p2["exp_level"],
        "trophies": p1["trophies"] - p2["trophies"],
        "war_stars": p1["war_stars"] - p2["war_stars"],
        "attack_wins": p1["attack_wins"] - p2["attack_wins"],
        "defense_wins": p1["defense_wins"] - p2["defense_wins"],
        "donations": p1["donations"] - p2["donations"],
    }


def _clan_diff(c1: dict, c2: dict) -> dict:
    return {
        "level": c1["level"] - c2["level"],
        "member_count": c1["member_count"] - c2["member_count"],
        "points": c1["points"] - c2["points"],
        "war_wins": c1["war_wins"] - c2["war_wins"],
    }
