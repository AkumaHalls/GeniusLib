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
    # (item_name, level) -> (gold, elixir, de, time_seconds)
    "Town Hall": {
        14: (0, 0, 0, 0),
        15: (12000000, 10000000, 0, 1900800),  # 22 days
        16: (16000000, 14000000, 0, 2246400),  # 26 days
        17: (20000000, 18000000, 0, 2592000),  # 30 days
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
    if target_th is None:
        target_th = current_th + 1

    summary = UpgradeSummary(
        player_tag=player.tag,
        current_th=current_th,
        target_th=target_th,
        builder_count=builder_count,
    )

    buildings = getattr(player, "buildings", [])
    troops = getattr(player, "troops", [])
    heroes = getattr(player, "heroes", [])
    spells = getattr(player, "spells", [])
    pets = getattr(player, "pets", [])

    for b in buildings:
        name = getattr(b, "name", "Unknown")
        level = getattr(b, "level", 0)
        max_level = getattr(b, "max_level", 0)
        if level < max_level:
            _record_upgrade(summary, name, "building", level, max_level)

    for collection, item_type in [
        (troops, "troop"), (heroes, "hero"),
        (spells, "spell"), (pets, "pet"),
    ]:
        for item in collection:
            name = getattr(item, "name", "Unknown")
            level = getattr(item, "level", 0)
            max_level = getattr(item, "max_level", 0)
            if level < max_level:
                _record_upgrade(summary, name, item_type, level, max_level)

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

    lines = [
        f"📊 Resumo de Upgrades TH{summary.current_th} → TH{summary.target_th}",
        f"  🏠 Jogador: {summary.player_tag}",
        f"  🪙 Ouro: {summary.total_gold:,}" if summary.total_gold else None,
        f"  🧪 Elixir: {summary.total_elixir:,}" if summary.total_elixir else None,
        f"  💎 Elixir Negro: {summary.total_dark_elixir:,}" if summary.total_dark_elixir else None,
        f"  ⏱ Tempo total: {summary.total_time_delta}" if summary.total_time_seconds else None,
        f"  ⏳ Tempo real ({summary.builder_count} builders): ~{summary.estimated_real_time}" if summary.total_time_seconds else None,
        f"  📦 Total de upgrades: {len(summary.upgrades)} (níveis restantes: {total_levels})",
    ]
    return "\n".join(line for line in lines if line is not None)
