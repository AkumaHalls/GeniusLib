"""Upgrade Tracker module for GeniusLib.

Calculates upgrade costs, time remaining, and resource requirements
for a player's village at a given Town Hall level.

Usage::

    from geniuslib.upgrade_tracker import (
        estimate_upgrade_cost,
        estimate_upgrade_time,
        get_th_upgrade_summary,
    )

    # Get total cost to max from TH14 to TH15
    summary = get_th_upgrade_summary(player, target_th=15)
    print(summary["total_gold"])
    print(summary["total_elixir"])
    print(summary["total_dark_elixir"])
"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List, Optional


@dataclass
class UpgradeCost:
    """Represents the cost and time for a single upgrade.

    Attributes
    ----------
    name : str
        Name of the item being upgraded.
    item_type : str
        Type: "building", "troop", "hero", "spell", "pet", "equipment".
    from_level : int
        Current level.
    to_level : int
        Target level.
    gold : int
        Gold cost (0 if not gold).
    elixir : int
        Elixir cost (0 if not elixir).
    dark_elixir : int
        Dark elixir cost (0 if not dark elixir).
    time_seconds : int
        Upgrade time in seconds.
    """
    name: str
    item_type: str
    from_level: int
    to_level: int
    gold: int = 0
    elixir: int = 0
    dark_elixir: int = 0
    time_seconds: int = 0

    @property
    def time_delta(self) -> timedelta:
        return timedelta(seconds=self.time_seconds)

    def __repr__(self):
        return (
            f"<UpgradeCost {self.name} {self.from_level}->{self.to_level}"
            f" gold={self.gold} elixir={self.elixir} de={self.dark_elixir}"
            f" time={self.time_delta}>"
        )


@dataclass
class UpgradeSummary:
    """Aggregated upgrade summary for a player.

    Attributes
    ----------
    player_tag : str
        The player's tag.
    current_th : int
        Current Town Hall level.
    target_th : int
        Target Town Hall level.
    upgrades : List[UpgradeCost]
        List of all pending upgrades.
    total_gold : int
        Total gold required.
    total_elixir : int
        Total elixir required.
    total_dark_elixir : int
        Total dark elixir required.
    total_time_seconds : int
        Total upgrade time in seconds.
    builder_count : int
        Number of builders available.
    """
    player_tag: str
    current_th: int
    target_th: int
    upgrades: List[UpgradeCost] = field(default_factory=list)
    total_gold: int = 0
    total_elixir: int = 0
    total_dark_elixir: int = 0
    total_time_seconds: int = 0
    builder_count: int = 5

    @property
    def total_time_delta(self) -> timedelta:
        return timedelta(seconds=self.total_time_seconds)

    @property
    def estimated_real_time(self) -> timedelta:
        """Estimate real-world time with builder_count builders."""
        if self.builder_count <= 0:
            return self.total_time_delta
        return timedelta(seconds=self.total_time_seconds / self.builder_count)

    def __repr__(self):
        return (
            f"<UpgradeSummary TH{self.current_th}->TH{self.target_th}"
            f" gold={self.total_gold:,} elixir={self.total_elixir:,}"
            f" de={self.total_dark_elixir:,} time={self.total_time_delta}"
            f" real≈{self.estimated_real_time}>"
        )


# Approximate upgrade costs and times for key levels.
# These are community-sourced estimates and may not reflect exact in-game values.
_BUILDING_COST_TABLE = {
    "Town Hall": {
        14: (0, 0, 0, 0),
        15: (12000000, 10000000, 0, 1900800),
        16: (16000000, 14000000, 0, 2246400),
        17: (20000000, 18000000, 0, 2592000),
    },
    "Eagle Artillery": {
        1: (8000000, 0, 0, 864000),
        2: (9300000, 0, 0, 950400),
    },
}

_LAB_COST_TABLE = {
    "Barbarian": {
        8: (100000, 0, 0, 86400),
        9: (200000, 0, 0, 172800),
    },
}

_TH_MAX_LEVELS = {
    "building": {
        "Cannon": {14: 12, 15: 14, 16: 15, 17: 16, 18: 17},
        "Archer Tower": {14: 12, 15: 13, 16: 14, 17: 15, 18: 16},
        "Mortar": {14: 12, 15: 13, 16: 14, 17: 15, 18: 16},
        "Wizard Tower": {14: 12, 15: 14, 16: 14, 17: 15, 18: 16},
        "Air Defense": {14: 11, 15: 12, 16: 13, 17: 14, 18: 15},
        "Hidden Tesla": {14: 10, 15: 11, 16: 12, 17: 13, 18: 14},
        "Bomb Tower": {14: 8, 15: 9, 16: 10, 17: 10, 18: 11},
        "Inferno Tower": {14: 7, 15: 8, 16: 9, 17: 10, 18: 11},
        "X-Bow": {14: 6, 15: 7, 16: 8, 17: 9, 18: 10},
        "Eagle Artillery": {14: 2, 15: 3, 16: 4, 17: 5, 18: 6},
        "Scattershot": {14: 3, 15: 4, 16: 5, 17: 6, 18: 7},
        "Spell Tower": {16: 2, 17: 3, 18: 4},
        "Monolith": {16: 2, 17: 3, 18: 4},
        "Workshop": {14: 4, 15: 4, 16: 4, 17: 4, 18: 5},
        "Barracks": {14: 15, 15: 15, 16: 16, 17: 16, 18: 16},
        "Army Camp": {14: 10, 15: 10, 16: 11, 17: 11, 18: 11},
        "Laboratory": {14: 12, 15: 12, 16: 13, 17: 13, 18: 14},
        "Spell Factory": {14: 5, 15: 5, 16: 5, 17: 5, 18: 6},
        "Dark Spell Factory": {14: 5, 15: 5, 16: 5, 17: 5, 18: 6},
        "Clan Castle": {14: 10, 15: 10, 16: 10, 17: 10, 18: 11},
        "Pet House": {15: 5, 16: 6, 17: 7, 18: 8},
        "Blacksmith": {16: 7, 17: 8, 18: 9},
        "Builder Hut": {14: 5, 15: 5, 16: 5, 17: 6, 18: 7},
        "Gold Mine": {14: 14, 15: 14, 16: 14, 17: 14, 18: 15},
        "Elixir Collector": {14: 14, 15: 14, 16: 14, 17: 14, 18: 15},
        "Dark Elixir Drill": {14: 9, 15: 9, 16: 9, 17: 10, 18: 10},
        "Gold Storage": {14: 15, 15: 15, 16: 15, 17: 15, 18: 16},
        "Elixir Storage": {14: 15, 15: 15, 16: 15, 17: 15, 18: 16},
        "Dark Elixir Storage": {14: 9, 15: 9, 16: 9, 17: 10, 18: 11},
        "Silo": {17: 2, 18: 3},
        "Air Sweeper": {14: 7, 15: 7, 16: 7, 17: 7, 18: 8},
        "Multi-Gear Tower": {17: 3, 18: 4},
        "Firespitter": {17: 3, 18: 4},
        "Revenge Tower": {18: 3},
        "Super Wizard Tower": {18: 2},
        "Meteor Castle": {18: 2},
        "Bomb": {14: 9, 15: 9, 16: 9, 17: 9, 18: 10},
        "Spring Trap": {14: 5, 15: 5, 16: 5, 17: 5, 18: 5},
        "Giant Bomb": {14: 6, 15: 6, 16: 6, 17: 6, 18: 7},
        "Air Bomb": {14: 5, 15: 5, 16: 5, 17: 5, 18: 6},
        "Seeking Air Mine": {14: 4, 15: 4, 16: 4, 17: 4, 18: 5},
        "Skeleton Trap": {14: 4, 15: 4, 16: 4, 17: 4, 18: 4},
        "Tornado Trap": {14: 3, 15: 3, 16: 3, 17: 3, 18: 4},
    },
    "troop": {
        "Barbarian": {14: 10, 15: 11, 16: 11, 17: 12, 18: 13},
        "Archer": {14: 10, 15: 11, 16: 11, 17: 12, 18: 13},
        "Goblin": {14: 9, 15: 10, 16: 10, 17: 11, 18: 11},
        "Giant": {14: 10, 15: 11, 16: 11, 17: 12, 18: 13},
        "Wall Breaker": {14: 10, 15: 11, 16: 11, 17: 12, 18: 13},
        "Balloon": {14: 9, 15: 10, 16: 11, 17: 12, 18: 13},
        "Wizard": {14: 10, 15: 11, 16: 11, 17: 12, 18: 12},
        "Healer": {14: 7, 15: 8, 16: 8, 17: 9, 18: 9},
        "Dragon": {14: 9, 15: 10, 16: 11, 17: 12, 18: 12},
        "PEKKA": {14: 9, 15: 10, 16: 10, 17: 11, 18: 12},
        "Baby Dragon": {14: 6, 15: 7, 16: 8, 17: 9, 18: 10},
        "Miner": {14: 8, 15: 9, 16: 9, 17: 10, 18: 11},
        "Electro Dragon": {14: 5, 15: 6, 16: 7, 17: 8, 18: 9},
        "Yeti": {14: 5, 15: 5, 16: 6, 17: 6, 18: 7},
        "Dragon Rider": {14: 3, 15: 4, 16: 5, 17: 6, 18: 6},
        "Electro Titan": {15: 2, 16: 3, 17: 4, 18: 5},
        "Root Rider": {16: 2, 17: 4, 18: 5},
        "Thrower": {17: 3, 18: 4},
        "Meteor Golem": {18: 3},
        "Ice Golem": {14: 6, 15: 7, 16: 7, 17: 8, 18: 8},
        "Headhunter": {14: 4, 15: 5, 16: 5, 17: 6, 18: 7},
        "Apprentice Warden": {16: 2, 17: 5, 18: 6},
        "Ruin Witch": {18: 3},
        "Minion": {14: 10, 15: 10, 16: 10, 17: 11, 18: 12},
        "Hog Rider": {14: 11, 15: 12, 16: 13, 17: 14, 18: 15},
        "Valkyrie": {14: 9, 15: 9, 16: 10, 17: 10, 18: 11},
        "Golem": {14: 10, 15: 10, 16: 10, 17: 11, 18: 11},
        "Witch": {14: 6, 15: 6, 16: 7, 17: 7, 18: 8},
        "Lava Hound": {14: 6, 15: 6, 16: 7, 17: 7, 18: 8},
        "Bowler": {14: 7, 15: 8, 16: 9, 17: 9, 18: 10},
        "Druid": {16: 4, 17: 5, 18: 5},
        "Furnace": {17: 3, 18: 4},
    },
    "hero": {
        "Barbarian King": {14: 75, 15: 80, 16: 85, 17: 95, 18: 110},
        "Archer Queen": {14: 75, 15: 80, 16: 85, 17: 95, 18: 110},
        "Grand Warden": {14: 50, 15: 55, 16: 60, 17: 70, 18: 85},
        "Royal Champion": {14: 25, 15: 30, 16: 35, 17: 40, 18: 55},
        "Minion Prince": {15: 25, 16: 35, 17: 40, 18: 55},
        "Dragon Duke": {15: 8, 16: 12, 17: 18, 18: 25},
        "Battle Machine": {14: 30, 15: 30, 16: 30, 17: 30, 18: 30},
        "Battle Copter": {14: 30, 15: 30, 16: 30, 17: 30, 18: 30},
    },
    "spell": {
        "Lightning Spell": {14: 9, 15: 10, 16: 10, 17: 11, 18: 11},
        "Healing Spell": {14: 8, 15: 9, 16: 9, 17: 10, 18: 11},
        "Rage Spell": {14: 6, 15: 7, 16: 7, 17: 8, 18: 9},
        "Jump Spell": {14: 4, 15: 4, 16: 4, 17: 5, 18: 5},
        "Freeze Spell": {14: 6, 15: 7, 16: 7, 17: 8, 18: 8},
        "Clone Spell": {14: 4, 15: 5, 16: 5, 17: 6, 18: 7},
        "Invisibility Spell": {14: 4, 15: 5, 16: 5, 17: 6, 18: 6},
        "Recall Spell": {14: 2, 15: 3, 16: 3, 17: 4, 18: 5},
        "Bat Spell": {14: 4, 15: 5, 16: 5, 17: 6, 18: 6},
        "Poison Spell": {14: 7, 15: 8, 16: 8, 17: 9, 18: 10},
        "Earthquake Spell": {14: 5, 15: 5, 16: 5, 17: 5, 18: 6},
        "Haste Spell": {14: 5, 15: 5, 16: 5, 17: 5, 18: 6},
        "Skeleton Spell": {14: 6, 15: 7, 16: 7, 17: 8, 18: 8},
        "Overgrowth Spell": {14: 3, 15: 3, 16: 3, 17: 3, 18: 3},
        "Revive Spell": {16: 3, 17: 4, 18: 5},
        "Ice Block Spell": {16: 2, 17: 3, 18: 4},
        "Totem Spell": {18: 3},
        "Angry Spell": {18: 3},
    },
    "pet": {
        "L.A.S.S.I.": {14: 15, 15: 20, 16: 25, 17: 30, 18: 30},
        "Electro Owl": {14: 15, 15: 20, 16: 25, 17: 30, 18: 30},
        "Mighty Yak": {14: 15, 15: 20, 16: 25, 17: 30, 18: 30},
        "Unicorn": {14: 15, 15: 20, 16: 25, 17: 30, 18: 30},
        "Frosty": {15: 20, 16: 25, 17: 30, 18: 30},
        "Diggy": {16: 20, 17: 25, 18: 30},
        "Poison Lizard": {16: 20, 17: 25, 18: 30},
        "Spirit Fox": {16: 10, 17: 15, 18: 20},
        "Phoenix": {17: 5, 18: 10},
        "Angry Jelly": {17: 15, 18: 20},
        "Sneezy": {18: 15},
        "Greedy Raven": {18: 10},
    },
}


def _estimate_building_cost(name: str, from_level: int, to_level: int) -> List[UpgradeCost]:
    """Estimate cumulative cost for upgrading a building across levels."""
    upgrades = []
    total_gold = total_elixir = total_de = total_time = 0
    for level in range(from_level + 1, to_level + 1):
        costs = _BUILDING_COST_TABLE.get(name, {}).get(level, (0, 0, 0, 0))
        total_gold += costs[0]
        total_elixir += costs[1]
        total_de += costs[2]
        total_time += costs[3]
    if total_gold or total_elixir or total_de:
        upgrades.append(UpgradeCost(
            name=name, item_type="building",
            from_level=from_level, to_level=to_level,
            gold=total_gold, elixir=total_elixir,
            dark_elixir=total_de, time_seconds=total_time,
        ))
    return upgrades


def estimate_upgrade_cost(
    current_level: int,
    target_level: int,
    item_name: str,
    item_type: str = "building",
) -> List[UpgradeCost]:
    """Estimate upgrade costs for a given item between two levels.

    Parameters
    ----------
    current_level : int
        Current level of the item.
    target_level : int
        Desired target level.
    item_name : str
        Name of the item (e.g. "Town Hall", "Barbarian").
    item_type : str
        Type of item (building, troop, hero, spell, pet, equipment).

    Returns
    -------
    List[UpgradeCost]
        List of upgrade cost estimates.
    """
    if target_level <= current_level:
        return []

    if item_type == "building":
        return _estimate_building_cost(item_name, current_level, target_level)

    if item_type in ("troop", "spell", "hero", "pet", "equipment"):
        upgrades = []
        total_elixir = total_de = total_time = 0
        table = _LAB_COST_TABLE.get(item_name, {})
        for level in range(current_level + 1, target_level + 1):
            costs = table.get(level, (0, 0, 0, 86400))
            total_elixir += costs[0]
            total_de += costs[1]
            total_time += costs[3]
        if total_elixir or total_de:
            upgrades.append(UpgradeCost(
                name=item_name, item_type=item_type,
                from_level=current_level, to_level=target_level,
                gold=0, elixir=total_elixir,
                dark_elixir=total_de, time_seconds=total_time,
            ))
        return upgrades

    return []


def estimate_upgrade_time(
    current_level: int,
    target_level: int,
    item_name: str,
    item_type: str = "building",
) -> timedelta:
    """Estimate total upgrade time for an item.

    Parameters
    ----------
    current_level : int
        Current level.
    target_level : int
        Target level.
    item_name : str
        Item name.
    item_type : str
        Item type.

    Returns
    -------
    timedelta
        Total estimated upgrade time.
    """
    costs = estimate_upgrade_cost(current_level, target_level, item_name, item_type)
    total_seconds = sum(c.time_seconds for c in costs)
    return timedelta(seconds=total_seconds)


_DEFAULT_DAYS_PER_LEVEL = {
    "building": 3,
    "troop": 7,
    "hero": 5,
    "spell": 4,
    "pet": 5,
    "equipment": 3,
}

def _record_upgrade(summary, name: str, item_type: str, from_level: int, to_level: int):
    """Record an upgrade into the summary, using cost tables or level info as fallback."""
    costs = estimate_upgrade_cost(from_level, to_level, name, item_type)
    if costs:
        for c in costs:
            summary.upgrades.append(c)
            summary.total_gold += c.gold
            summary.total_elixir += c.elixir
            summary.total_dark_elixir += c.dark_elixir
            summary.total_time_seconds += c.time_seconds
    else:
        levels = to_level - from_level
        est_days = _DEFAULT_DAYS_PER_LEVEL.get(item_type, 3)
        est_seconds = levels * est_days * 86400
        fallback = UpgradeCost(
            name=name, item_type=item_type,
            from_level=from_level, to_level=to_level,
            time_seconds=est_seconds,
        )
        summary.upgrades.append(fallback)
        summary.total_time_seconds += est_seconds


def get_th_upgrade_summary(
    player,
    target_th: Optional[int] = None,
    builder_count: int = 5,
) -> UpgradeSummary:
    """Generate a full upgrade summary for a player.

    Iterates over the player's buildings, troops, heroes, spells,
    and pets to compute total remaining upgrade costs and time
    to reach the target Town Hall level.

    When exact costs are not available in the internal tables,
    the upgrade is still recorded with level progress info
    (current level → max level) so the count is always accurate.

    Parameters
    ----------
    player : Player
        The player object from the API.
    target_th : Optional[int]
        Target Town Hall level. Defaults to current TH + 1.
    builder_count : int
        Number of builders. Defaults to 5.

    Returns
    -------
    UpgradeSummary
        Summary of all pending upgrades.
    """
    current_th = getattr(player, "town_hall", 0)
    if target_th and target_th <= current_th:
        target_th = None

    summary = UpgradeSummary(
        player_tag=player.tag,
        current_th=current_th,
        target_th=target_th or current_th,
        builder_count=builder_count,
    )

    effective_th = target_th or current_th

    buildings = getattr(player, "buildings", [])
    troops = getattr(player, "troops", [])
    heroes = getattr(player, "heroes", [])
    spells = getattr(player, "spells", [])
    pets = getattr(player, "pets", [])

    th_table = _TH_MAX_LEVELS

    for b in buildings:
        name = getattr(b, "name", "Unknown")
        level = getattr(b, "level", 0)
        api_max = getattr(b, "max_level", 0)
        th_max = th_table.get("building", {}).get(name, {}).get(effective_th, api_max)
        target = min(th_max, api_max) if api_max else th_max
        if level < target:
            _record_upgrade(summary, name, "building", level, target)

    for collection, item_type in [
        (troops, "troop"), (heroes, "hero"),
        (spells, "spell"), (pets, "pet"),
    ]:
        for item in collection:
            name = getattr(item, "name", "Unknown")
            level = getattr(item, "level", 0)
            api_max = getattr(item, "max_level", 0)
            th_max = th_table.get(item_type, {}).get(name, {}).get(effective_th, api_max)
            target = min(th_max, api_max) if api_max else th_max
            if level < target:
                _record_upgrade(summary, name, item_type, level, target)

    return summary


def format_upgrade_summary(summary: UpgradeSummary) -> str:
    """Format an UpgradeSummary into a readable string (for Discord, terminal, etc.).

    Parameters
    ----------
    summary : UpgradeSummary
        The summary to format.

    Returns
    -------
    str
        Formatted summary string.
    """
    total_levels = sum(
        (u.to_level - u.from_level) for u in summary.upgrades
    ) if summary.upgrades else 0

    th_label = f"TH{summary.current_th}" if summary.target_th == summary.current_th else f"TH{summary.current_th} → TH{summary.target_th}"
    lines = [
        f"📊 {th_label} — Resumo de Upgrades",
        f"  🏠 Jogador: {summary.player_tag}",
        f"  🪙 Ouro: {summary.total_gold:,}" if summary.total_gold else None,
        f"  🧪 Elixir: {summary.total_elixir:,}" if summary.total_elixir else None,
        f"  💎 Elixir Negro: {summary.total_dark_elixir:,}" if summary.total_dark_elixir else None,
        f"  ⏱ Tempo total: {summary.total_time_delta}" if summary.total_time_seconds else None,
        f"  ⏳ Tempo real ({summary.builder_count} builders): ~{summary.estimated_real_time}" if summary.total_time_seconds else None,
        f"  📦 Total de upgrades: {len(summary.upgrades)} (níveis restantes: {total_levels})",
    ]
    return "\n".join(line for line in lines if line is not None)
