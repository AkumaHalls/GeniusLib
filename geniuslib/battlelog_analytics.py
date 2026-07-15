# GeniusLib - Clash of Clans API wrapper
# (c) 2026 AkumaHalls / ClashGenius

import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .battlelog import (
    BattleLogEntry,
    LeagueHistoryEntry,
    LeagueTierGroup,
    LeagueTierGroupMember,
)
from .utils import format_season_id


def decode_army_code(code: str, static_data: dict) -> dict:
    """Decode an army share code into human-readable components.

    Parameters
    ----------
    code:
        The raw ``armyShareCode`` from the battle log API.
    static_data:
        The client's ``_static_data`` dict mapping internal IDs to static data records.

    Returns
    -------
    :class:`dict`
        Dictionary with ``troops``, ``spells``, ``heroes`` (each a list of
        ``{"name": str, "quantity": int}``).
    """
    if not code or not static_data:
        return {"troops": [], "spells": [], "heroes": []}

    TROOP_BASE = 4000000
    SPELL_BASE = 26000000
    HERO_BASE = 28000000
    PET_BASE = 73000000
    EQUIP_BASE = 90000000

    import re

    troop_items = []
    spell_items = []
    hero_items = []

    sections = re.finditer(
        r"h(?P<heroes>[^idus]+)"
        r"|u(?P<units>[\d+x-]+)"
        r"|s(?P<spells>[\d+x-]+)",
        code,
    )

    for m in sections:
        if m.group("heroes"):
            hero_entries = m.group("heroes").split("-")
            hero_re = re.compile(
                r"(?P<hero_id>\d+)"
                r"(?:m\d+)?"
                r"(?:p(?P<pet_id>\d+))?"
                r"(?:e(?P<eq1>\d+)(?:_(?P<eq2>\d+))?)?"
            )
            for he in hero_entries:
                hm = hero_re.fullmatch(he)
                if not hm:
                    continue
                hero_id = HERO_BASE + int(hm.group("hero_id"))
                hero_data = static_data.get(hero_id, {})
                hero_name = hero_data.get("name", f"Hero#{hm.group('hero_id')}")
                pet_name = None
                if hm.group("pet_id"):
                    pet_id = PET_BASE + int(hm.group("pet_id"))
                    pet_data = static_data.get(pet_id, {})
                    pet_name = pet_data.get("name", f"Pet#{hm.group('pet_id')}")
                eq_names = []
                for eq_group in ("eq1", "eq2"):
                    eq_val = hm.group(eq_group)
                    if eq_val:
                        eq_id = EQUIP_BASE + int(eq_val)
                        eq_data = static_data.get(eq_id, {})
                        eq_names.append(eq_data.get("name", f"Eq#{eq_val}"))
                hero_items.append({
                    "name": hero_name,
                    "pet": pet_name,
                    "equipment": eq_names,
                })

        elif m.group("units"):
            for part in m.group("units").split("-"):
                if "x" not in part:
                    continue
                qty_str, id_str = part.split("x", 1)
                item_id = TROOP_BASE + int(id_str)
                data = static_data.get(item_id, {})
                name = data.get("name", f"Troop#{id_str}")
                troop_items.append({"name": name, "quantity": int(qty_str)})

        elif m.group("spells"):
            for part in m.group("spells").split("-"):
                if "x" not in part:
                    continue
                qty_str, id_str = part.split("x", 1)
                item_id = SPELL_BASE + int(id_str)
                data = static_data.get(item_id, {})
                name = data.get("name", f"Spell#{id_str}")
                spell_items.append({"name": name, "quantity": int(qty_str)})

    return {"troops": troop_items, "spells": spell_items, "heroes": hero_items}


def battle_win_rate(entries: List[BattleLogEntry]) -> float:
    """Calculate the win rate from attack entries.

    A ``win`` is defined as an attack that earned at least 1 star.

    Parameters
    ----------
    entries:
        List of battle log entries.

    Returns
    -------
    :class:`float`
        Win rate as a percentage (0-100). Returns 0.0 if no attack entries.
    """
    attacks = [e for e in entries if e.is_attack]
    if not attacks:
        return 0.0
    wins = sum(1 for a in attacks if a.stars > 0)
    return (wins / len(attacks)) * 100.0


def battle_attack_stats(entries: List[BattleLogEntry]) -> dict:
    """Compute attack statistics from battle log entries.

    Parameters
    ----------
    entries:
        List of battle log entries.

    Returns
    -------
    :class:`dict`
        Dictionary with keys: ``total_attacks``, ``wins``, ``losses``,
        ``avg_stars``, ``avg_destruction``, ``total_stars``, ``star_distribution``.
    """
    attacks = [e for e in entries if e.is_attack]
    if not attacks:
        return {
            "total_attacks": 0,
            "wins": 0,
            "losses": 0,
            "avg_stars": 0.0,
            "avg_destruction": 0.0,
            "total_stars": 0,
            "star_distribution": {0: 0, 1: 0, 2: 0, 3: 0},
        }

    wins = sum(1 for a in attacks if a.stars > 0)
    total_stars = sum(a.stars for a in attacks)
    total_destruction = sum(a.destruction_percentage for a in attacks)
    star_dist = Counter(a.stars for a in attacks)

    return {
        "total_attacks": len(attacks),
        "wins": wins,
        "losses": len(attacks) - wins,
        "avg_stars": round(total_stars / len(attacks), 2),
        "avg_destruction": round(total_destruction / len(attacks), 1),
        "total_stars": total_stars,
        "star_distribution": {i: star_dist.get(i, 0) for i in range(4)},
    }


def battle_defense_stats(entries: List[BattleLogEntry]) -> dict:
    """Compute defense statistics from battle log entries.

    Parameters
    ----------
    entries:
        List of battle log entries.

    Returns
    -------
    :class:`dict`
        Dictionary with keys: ``total_defenses``, ``wins``, ``losses``,
        ``avg_stars_received``, ``avg_destruction_received``, ``total_stars_received``.
    """
    defenses = [e for e in entries if e.is_defense]
    if not defenses:
        return {
            "total_defenses": 0,
            "wins": 0,
            "losses": 0,
            "avg_stars_received": 0.0,
            "avg_destruction_received": 0.0,
            "total_stars_received": 0,
        }

    wins = sum(1 for d in defenses if d.stars == 0)
    total_stars = sum(d.stars for d in defenses)
    total_destruction = sum(d.destruction_percentage for d in defenses)

    return {
        "total_defenses": len(defenses),
        "wins": wins,
        "losses": len(defenses) - wins,
        "avg_stars_received": round(total_stars / len(defenses), 2),
        "avg_destruction_received": round(total_destruction / len(defenses), 1),
        "total_stars_received": total_stars,
    }


def battle_loot_summary(entries: List[BattleLogEntry]) -> dict:
    """Compute loot statistics from attack entries.

    Parameters
    ----------
    entries:
        List of battle log entries.

    Returns
    -------
    :class:`dict`
        Dictionary with keys: ``total_gold``, ``total_elixir``, ``total_dark``,
        ``avg_per_attack``, ``total_looted``.
    """
    attacks = [e for e in entries if e.is_attack]
    if not attacks:
        return {
            "total_gold": 0,
            "total_elixir": 0,
            "total_dark": 0,
            "avg_per_attack": 0,
            "total_looted": 0,
        }

    gold = 0
    elixir = 0
    dark = 0

    for attack in attacks:
        for resource in attack.looted_resources:
            name = (resource.name or "").lower()
            if "gold" in name:
                gold += resource.amount
            elif "dark" in name:
                dark += resource.amount
            elif "elixir" in name:
                elixir += resource.amount

    total = gold + elixir + dark

    return {
        "total_gold": gold,
        "total_elixir": elixir,
        "total_dark": dark,
        "avg_per_attack": round(total / len(attacks)) if attacks else 0,
        "total_looted": total,
    }


def battle_streak(entries: List[BattleLogEntry]) -> Tuple[int, int, str]:
    """Compute the current and best win/loss streak from attack entries.

    Parameters
    ----------
    entries:
        List of battle log entries (should be sorted by timestamp ascending).

    Returns
    -------
    :class:`tuple`
        ``(current_streak, best_streak, streak_type)`` where ``streak_type``
        is ``"win"`` or ``"loss"``.
    """
    attacks = sorted(
        [e for e in entries if e.is_attack],
        key=lambda e: e.timestamp or datetime.min,
    )
    if not attacks:
        return (0, 0, "win")

    current_streak = 0
    current_type = None
    best_streak = 0
    best_type = "win"

    for attack in attacks:
        is_win = attack.stars > 0

        if current_type is None:
            current_type = "win" if is_win else "loss"
            current_streak = 1
        elif (is_win and current_type == "win") or (not is_win and current_type == "loss"):
            current_streak += 1
        else:
            if current_streak > best_streak:
                best_streak = current_streak
                best_type = current_type
            current_type = "win" if is_win else "loss"
            current_streak = 1

    if current_streak > best_streak:
        best_streak = current_streak
        best_type = current_type

    return (current_streak, best_streak, current_type or "win")


def battle_consistency_score(entries: List[BattleLogEntry]) -> float:
    """Compute a consistency score (0-100) based on the standard deviation of stars.

    Lower deviation = higher consistency. A perfect score means all attacks
    earned the same number of stars.

    Parameters
    ----------
    entries:
        List of battle log entries.

    Returns
    -------
    :class:`float`
        Consistency score from 0 to 100.
    """
    attacks = [e for e in entries if e.is_attack]
    if len(attacks) < 2:
        return 100.0

    stars = [a.stars for a in attacks]
    stdev = statistics.stdev(stars)

    score = max(0.0, 100.0 - (stdev * 30.0))
    return round(score, 1)


def battle_daily_summary(entries: List[BattleLogEntry], target_date: date) -> dict:
    """Compute a summary for a specific day.

    Parameters
    ----------
    entries:
        List of battle log entries.
    target_date:
        The date to summarize.

    Returns
    -------
    :class:`dict`
        Daily summary with attack/defense stats and loot.
    """
    day_entries = [
        e for e in entries
        if e.timestamp and e.timestamp.date() == target_date
    ]

    attacks = [e for e in day_entries if e.is_attack]
    defenses = [e for e in day_entries if e.is_defense]

    attack_wins = sum(1 for a in attacks if a.stars > 0)
    defense_wins = sum(1 for d in defenses if d.stars == 0)
    total_stars = sum(a.stars for a in attacks)

    return {
        "date": target_date.isoformat(),
        "total_battles": len(day_entries),
        "attacks": len(attacks),
        "defenses": len(defenses),
        "attack_wins": attack_wins,
        "defense_wins": defense_wins,
        "total_stars": total_stars,
        "avg_stars": round(total_stars / len(attacks), 2) if attacks else 0.0,
    }


def battle_period_summary(
    entries: List[BattleLogEntry],
    start_date: date,
    end_date: date,
) -> dict:
    """Compute a summary for a date range.

    Parameters
    ----------
    entries:
        List of battle log entries.
    start_date:
        Start of the period (inclusive).
    end_date:
        End of the period (inclusive).

    Returns
    -------
    :class:`dict`
        Period summary with aggregated stats.
    """
    period_entries = [
        e for e in entries
        if e.timestamp and start_date <= e.timestamp.date() <= end_date
    ]

    attack_stats = battle_attack_stats(period_entries)
    defense_stats = battle_defense_stats(period_entries)
    loot = battle_loot_summary(period_entries)
    win_rate = battle_win_rate(period_entries)

    days = (end_date - start_date).days + 1

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": days,
        "win_rate": round(win_rate, 1),
        "attacks": attack_stats,
        "defenses": defense_stats,
        "loot": loot,
    }


def league_history_progression(history: List[LeagueHistoryEntry]) -> dict:
    """Analyze league progression across seasons.

    Parameters
    ----------
    history:
        List of league history entries.

    Returns
    -------
    :class:`dict`
        Progression analysis with trophy trend, best season, average stats.
    """
    if not history:
        return {
            "total_seasons": 0,
            "trophy_trend": [],
            "best_trophies": 0,
            "worst_trophies": 0,
            "avg_trophies": 0.0,
            "avg_attack_win_rate": 0.0,
            "avg_defense_win_rate": 0.0,
            "best_placement": 0,
            "total_attack_stars": 0,
        }

    sorted_history = sorted(history, key=lambda h: h.league_season_id)
    trophies = [h.league_trophies for h in sorted_history]

    trophy_trend = [
        {
            "season": h.league_season_id,
            "season_label": format_season_id(h.league_season_id),
            "trophies": h.league_trophies,
            "placement": h.placement,
        }
        for h in sorted_history
    ]

    attack_win_rates = [h.attack_win_rate for h in history if h.total_attacks > 0]
    defense_win_rates = [h.defense_win_rate for h in history if h.total_defenses > 0]

    return {
        "total_seasons": len(history),
        "trophy_trend": trophy_trend,
        "best_trophies": max(trophies),
        "worst_trophies": min(trophies),
        "avg_trophies": round(statistics.mean(trophies), 1),
        "avg_attack_win_rate": round(statistics.mean(attack_win_rates), 1) if attack_win_rates else 0.0,
        "avg_defense_win_rate": round(statistics.mean(defense_win_rates), 1) if defense_win_rates else 0.0,
        "best_placement": min(h.placement for h in history),
        "total_attack_stars": sum(h.attack_stars for h in history),
    }


def league_season_stats(
    history: List[LeagueHistoryEntry],
    season_id: int,
) -> Optional[dict]:
    """Get detailed stats for a specific season.

    Parameters
    ----------
    history:
        List of league history entries.
    season_id:
        The season identifier to look up.

    Returns
    -------
    Optional[:class:`dict`]
        Season stats dict, or ``None`` if the season was not found.
    """
    for entry in history:
        if entry.league_season_id == season_id:
            return {
                "season_id": entry.league_season_id,
                "trophies": entry.league_trophies,
                "tier_id": entry.league_tier_id,
                "placement": entry.placement,
                "attack_wins": entry.attack_wins,
                "attack_losses": entry.attack_losses,
                "attack_stars": entry.attack_stars,
                "attack_win_rate": round(entry.attack_win_rate, 1),
                "defense_wins": entry.defense_wins,
                "defense_losses": entry.defense_losses,
                "defense_stars": entry.defense_stars,
                "defense_win_rate": round(entry.defense_win_rate, 1),
                "total_attacks": entry.total_attacks,
                "total_defenses": entry.total_defenses,
            }
    return None


def league_tier_distribution(history: List[LeagueHistoryEntry]) -> Dict[int, int]:
    """Count how many seasons were spent in each tier.

    Parameters
    ----------
    history:
        List of league history entries.

    Returns
    -------
    :class:`dict`
        Mapping of ``tier_id -> season_count``.
    """
    return dict(Counter(h.league_tier_id for h in history))


def tier_group_member_stats(group: LeagueTierGroup) -> List[dict]:
    """Compute per-member stats for a league tier group.

    Parameters
    ----------
    group:
        A league tier group.

    Returns
    -------
    List[:class:`dict`]
        One dict per member with attack/defense stats and win rates.
    """
    stats = []
    for member in group.members:
        stats.append({
            "player_tag": member.player_tag,
            "player_name": member.player_name,
            "clan_tag": member.clan_tag,
            "clan_name": member.clan_name,
            "league_trophies": member.league_trophies,
            "attack_wins": member.attack_win_count,
            "attack_losses": member.attack_lose_count,
            "defense_wins": member.defense_win_count,
            "defense_losses": member.defense_lose_count,
            "total_attacks": member.total_attacks,
            "total_defenses": member.total_defenses,
            "attack_win_rate": round(member.attack_win_rate, 1),
        })
    return stats


def tier_group_attack_analysis(group: LeagueTierGroup) -> dict:
    """Analyze attack logs in a league tier group.

    Parameters
    ----------
    group:
        A league tier group.

    Returns
    -------
    :class:`dict`
        Aggregate attack stats for the group.
    """
    logs = group.attack_logs
    if not logs:
        return {
            "total_attacks": 0,
            "total_stars": 0,
            "avg_stars": 0.0,
            "avg_destruction": 0.0,
            "three_stars": 0,
            "two_stars": 0,
            "one_star": 0,
            "zero_stars": 0,
        }

    total_stars = sum(l.stars for l in logs)
    star_dist = Counter(l.stars for l in logs)

    return {
        "total_attacks": len(logs),
        "total_stars": total_stars,
        "avg_stars": round(total_stars / len(logs), 2),
        "avg_destruction": round(sum(l.destruction_percentage for l in logs) / len(logs), 1),
        "three_stars": star_dist.get(3, 0),
        "two_stars": star_dist.get(2, 0),
        "one_star": star_dist.get(1, 0),
        "zero_stars": star_dist.get(0, 0),
    }


def tier_group_defense_analysis(group: LeagueTierGroup) -> dict:
    """Analyze defense logs in a league tier group.

    Parameters
    ----------
    group:
        A league tier group.

    Returns
    -------
    :class:`dict`
        Aggregate defense stats for the group.
    """
    logs = group.defense_logs
    if not logs:
        return {
            "total_defenses": 0,
            "total_stars_received": 0,
            "avg_stars_received": 0.0,
            "avg_destruction_received": 0.0,
            "clean_sheets": 0,
            "three_star_losses": 0,
        }

    total_stars = sum(l.stars for l in logs)
    star_dist = Counter(l.stars for l in logs)

    return {
        "total_defenses": len(logs),
        "total_stars_received": total_stars,
        "avg_stars_received": round(total_stars / len(logs), 2),
        "avg_destruction_received": round(sum(l.destruction_percentage for l in logs) / len(logs), 1),
        "clean_sheets": star_dist.get(0, 0),
        "three_star_losses": star_dist.get(3, 0),
    }


def tier_group_mvp(group: LeagueTierGroup) -> Optional[dict]:
    """Find the MVP of a league tier group based on trophies earned and win rate.

    Parameters
    ----------
    group:
        A league tier group.

    Returns
    -------
    Optional[:class:`dict`]
        MVP info dict, or ``None`` if the group has no members.
    """
    if not group.members:
        return None

    best = max(
        group.members,
        key=lambda m: (m.league_trophies, m.attack_win_rate),
    )

    return {
        "player_tag": best.player_tag,
        "player_name": best.player_name,
        "clan_name": best.clan_name,
        "league_trophies": best.league_trophies,
        "attack_wins": best.attack_win_count,
        "attack_losses": best.attack_lose_count,
        "attack_win_rate": round(best.attack_win_rate, 1),
    }
