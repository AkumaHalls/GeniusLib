# GeniusLib - Clash of Clans API wrapper
# Based on coc.py (MIT License, copyright (c) 2019-2020 mathsman5133)
# (c) 2026 AkumaHalls / ClashGenius

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from .utils import from_timestamp

if TYPE_CHECKING:
    from .client import Client


class BattleLogResource:
    """Represents a resource amount in a player battle log entry.

    Attributes
    ----------
    name:
        :class:`str`: The resource name (e.g. ``gold``, ``elixir``, ``darkElixir``).
    amount:
        :class:`int`: The amount of this resource.
    """

    __slots__ = ("name", "amount")

    def __init__(self, *, data):
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        self.name: str = data.get("name")
        self.amount: int = data.get("amount")

    def __repr__(self):
        attrs = [("name", self.name), ("amount", self.amount)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name and self.amount == other.amount


class BattleLogEntry:
    """Represents a single player battle log entry from the ``/players/{tag}/battlelog`` endpoint.

    Attributes
    ----------
    battle_type:
        :class:`str`: The type of battle (e.g. ``legendLeague``).
    attack:
        :class:`bool`: ``True`` if this was an attack, ``False`` if a defense.
    timestamp:
        Optional[:class:`datetime`]: When the battle occurred.
    army_share_code:
        :class:`str`: Code to share the army composition used.
    opponent_player_tag:
        :class:`str`: The tag of the opponent player.
    stars:
        :class:`int`: Stars earned in this battle.
    destruction_percentage:
        :class:`int`: Destruction percentage achieved.
    looted_resources:
        List[:class:`BattleLogResource`]: Resources looted.
    extra_looted_resources:
        List[:class:`BattleLogResource`]: Bonus resources looted.
    available_loot:
        List[:class:`BattleLogResource`]: Resources available to loot before the battle.
    """

    __slots__ = (
        "battle_type",
        "attack",
        "timestamp",
        "army_share_code",
        "opponent_player_tag",
        "stars",
        "destruction_percentage",
        "looted_resources",
        "extra_looted_resources",
        "available_loot",
        "_client",
        "_response_retry",
        "_raw_data",
    )

    def __init__(self, *, data, client: Optional[Client] = None, **_):
        self._client = client
        self._response_retry = data.get("_response_retry")
        self._raw_data = data if client and client.raw_attribute else None
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        data_get = data.get
        self.battle_type: str = data_get("battleType")
        self.attack: bool = data_get("attack")
        raw_ts = data_get("timestamp")
        self.timestamp: Optional[datetime] = from_timestamp(raw_ts) if raw_ts else None
        self.army_share_code: str = data_get("armyShareCode")
        self.opponent_player_tag: str = data_get("opponentPlayerTag")
        self.stars: int = data_get("stars")
        self.destruction_percentage: int = data_get("destructionPercentage")
        self.looted_resources: List[BattleLogResource] = [
            BattleLogResource(data=item) for item in data_get("lootedResources", [])
        ]
        self.extra_looted_resources: List[BattleLogResource] = [
            BattleLogResource(data=item) for item in data_get("extraLootedResources", [])
        ]
        self.available_loot: List[BattleLogResource] = [
            BattleLogResource(data=item) for item in data_get("availableLoot", [])
        ]

    def __repr__(self):
        attrs = [
            ("battle_type", self.battle_type),
            ("attack", self.attack),
            ("stars", self.stars),
            ("destruction_percentage", self.destruction_percentage),
            ("opponent", self.opponent_player_tag),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (
            self.opponent_player_tag == other.opponent_player_tag
            and self.timestamp == other.timestamp
            and self.attack == other.attack
        )

    @property
    def is_attack(self) -> bool:
        """:class:`bool`: Returns ``True`` if this entry is an attack."""
        return self.attack is True

    @property
    def is_defense(self) -> bool:
        """:class:`bool`: Returns ``True`` if this entry is a defense."""
        return self.attack is False

    @property
    def total_looted(self) -> int:
        """:class:`int`: Total resources looted across all resource types."""
        return sum(r.amount for r in self.looted_resources)

    @property
    def total_available(self) -> int:
        """:class:`int`: Total resources available before the battle."""
        return sum(r.amount for r in self.available_loot)

    @property
    def loot_efficiency(self) -> float:
        """:class:`float`: Percentage of available loot that was actually looted."""
        available = self.total_available
        if available == 0:
            return 0.0
        return (self.total_looted / available) * 100.0


class LeagueHistoryEntry:
    """Represents a player league season history entry from the ``/players/{tag}/leaguehistory`` endpoint.

    Attributes
    ----------
    league_season_id:
        :class:`int`: The league season identifier.
    league_trophies:
        :class:`int`: Trophies earned in this season.
    league_tier_id:
        :class:`int`: The league tier ID.
    placement:
        :class:`int`: Global or local ranking placement.
    attack_wins:
        :class:`int`: Number of attack wins.
    attack_losses:
        :class:`int`: Number of attack losses.
    attack_stars:
        :class:`int`: Total stars earned from attacks.
    defense_wins:
        :class:`int`: Number of defense wins.
    defense_losses:
        :class:`int`: Number of defense losses.
    defense_stars:
        :class:`int`: Total stars conceded from defenses.
    max_battles:
        :class:`int`: Maximum battles available this season.
    """

    __slots__ = (
        "league_season_id",
        "league_trophies",
        "league_tier_id",
        "placement",
        "attack_wins",
        "attack_losses",
        "attack_stars",
        "defense_wins",
        "defense_losses",
        "defense_stars",
        "max_battles",
        "_client",
        "_response_retry",
        "_raw_data",
    )

    def __init__(self, *, data, client: Optional[Client] = None, **_):
        self._client = client
        self._response_retry = data.get("_response_retry")
        self._raw_data = data if client and client.raw_attribute else None
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        data_get = data.get
        self.league_season_id: int = data_get("leagueSeasonId")
        self.league_trophies: int = data_get("leagueTrophies")
        self.league_tier_id: int = data_get("leagueTierId")
        self.placement: int = data_get("placement")
        self.attack_wins: int = data_get("attackWins")
        self.attack_losses: int = data_get("attackLosses")
        self.attack_stars: int = data_get("attackStars")
        self.defense_wins: int = data_get("defenseWins")
        self.defense_losses: int = data_get("defenseLosses")
        self.defense_stars: int = data_get("defenseStars")
        self.max_battles: int = data_get("maxBattles")

    def __repr__(self):
        attrs = [
            ("season", self.league_season_id),
            ("trophies", self.league_trophies),
            ("tier", self.league_tier_id),
            ("placement", self.placement),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.league_season_id == other.league_season_id

    @property
    def total_attacks(self) -> int:
        """:class:`int`: Total attacks performed (wins + losses)."""
        return self.attack_wins + self.attack_losses

    @property
    def total_defenses(self) -> int:
        """:class:`int`: Total defenses received (wins + losses)."""
        return self.defense_wins + self.defense_losses

    @property
    def attack_win_rate(self) -> float:
        """:class:`float`: Attack win rate as a percentage (0-100)."""
        total = self.total_attacks
        if total == 0:
            return 0.0
        return (self.attack_wins / total) * 100.0

    @property
    def defense_win_rate(self) -> float:
        """:class:`float`: Defense win rate as a percentage (0-100)."""
        total = self.total_defenses
        if total == 0:
            return 0.0
        return (self.defense_wins / total) * 100.0


class LeagueTierGroupBattleLogEntry:
    """Represents an attack or defense log entry inside a league tier group.

    Attributes
    ----------
    opponent_player_tag:
        :class:`str`: The tag of the opponent.
    opponent_name:
        :class:`str`: The name of the opponent.
    stars:
        :class:`int`: Stars earned or conceded.
    destruction_percentage:
        :class:`int`: Destruction percentage.
    trophies:
        :class:`int`: Trophies gained or lost.
    creation_time:
        Optional[:class:`datetime`]: When the battle occurred.
    """

    __slots__ = (
        "opponent_player_tag",
        "opponent_name",
        "stars",
        "destruction_percentage",
        "trophies",
        "creation_time",
    )

    def __init__(self, *, data):
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        data_get = data.get
        self.opponent_player_tag: str = data_get("opponentPlayerTag")
        self.opponent_name: str = data_get("opponentName")
        self.stars: int = data_get("stars")
        self.destruction_percentage: int = data_get("destructionPercentage")
        self.trophies: int = data_get("trophies")
        raw_time = data_get("creationTime")
        self.creation_time: Optional[datetime] = from_timestamp(raw_time) if raw_time else None

    def __repr__(self):
        attrs = [
            ("opponent", self.opponent_name),
            ("stars", self.stars),
            ("trophies", self.trophies),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)


class LeagueTierGroupMember:
    """Represents a member inside a league tier group.

    Attributes
    ----------
    player_tag:
        :class:`str`: The player's tag.
    player_name:
        :class:`str`: The player's name.
    clan_tag:
        :class:`str`: The player's clan tag.
    clan_name:
        :class:`str`: The player's clan name.
    league_trophies:
        :class:`int`: Current league trophies.
    attack_win_count:
        :class:`int`: Number of attack wins in this group.
    attack_lose_count:
        :class:`int`: Number of attack losses in this group.
    defense_win_count:
        :class:`int`: Number of defense wins in this group.
    defense_lose_count:
        :class:`int`: Number of defense losses in this group.
    """

    __slots__ = (
        "player_tag",
        "player_name",
        "clan_tag",
        "clan_name",
        "league_trophies",
        "attack_win_count",
        "attack_lose_count",
        "defense_win_count",
        "defense_lose_count",
    )

    def __init__(self, *, data):
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        data_get = data.get
        self.player_tag: str = data_get("playerTag")
        self.player_name: str = data_get("playerName")
        self.clan_tag: str = data_get("clanTag")
        self.clan_name: str = data_get("clanName")
        self.league_trophies: int = data_get("leagueTrophies")
        self.attack_win_count: int = data_get("attackWinCount")
        self.attack_lose_count: int = data_get("attackLoseCount")
        self.defense_win_count: int = data_get("defenseWinCount")
        self.defense_lose_count: int = data_get("defenseLoseCount")

    def __repr__(self):
        attrs = [
            ("name", self.player_name),
            ("clan", self.clan_name),
            ("trophies", self.league_trophies),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    @property
    def total_attacks(self) -> int:
        """:class:`int`: Total attacks (wins + losses)."""
        return self.attack_win_count + self.attack_lose_count

    @property
    def total_defenses(self) -> int:
        """:class:`int`: Total defenses (wins + losses)."""
        return self.defense_win_count + self.defense_lose_count

    @property
    def attack_win_rate(self) -> float:
        """:class:`float`: Attack win rate as a percentage (0-100)."""
        total = self.total_attacks
        if total == 0:
            return 0.0
        return (self.attack_win_count / total) * 100.0


class LeagueTierGroup:
    """Represents a league tier group for a league season from the ``/leaguegroup/{tag}/{seasonId}`` endpoint.

    Attributes
    ----------
    members:
        List[:class:`LeagueTierGroupMember`]: All members in the group.
    attack_logs:
        List[:class:`LeagueTierGroupBattleLogEntry`]: Detailed attack history.
    defense_logs:
        List[:class:`LeagueTierGroupBattleLogEntry`]: Detailed defense history.
    """

    __slots__ = (
        "members",
        "attack_logs",
        "defense_logs",
        "_client",
        "_response_retry",
        "_raw_data",
    )

    def __init__(self, *, data, client: Optional[Client] = None, **_):
        self._client = client
        self._response_retry = data.get("_response_retry")
        self._raw_data = data if client and client.raw_attribute else None
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        self.members: List[LeagueTierGroupMember] = [
            LeagueTierGroupMember(data=item) for item in data.get("members", [])
        ]
        self.attack_logs: List[LeagueTierGroupBattleLogEntry] = [
            LeagueTierGroupBattleLogEntry(data=item) for item in data.get("attackLogs", [])
        ]
        self.defense_logs: List[LeagueTierGroupBattleLogEntry] = [
            LeagueTierGroupBattleLogEntry(data=item) for item in data.get("defenseLogs", [])
        ]

    def __repr__(self):
        attrs = [
            ("members", len(self.members)),
            ("attacks", len(self.attack_logs)),
            ("defenses", len(self.defense_logs)),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def get_member(self, tag: str) -> Optional[LeagueTierGroupMember]:
        """Find a member by their player tag.

        Parameters
        ----------
        tag:
            :class:`str`: The player tag to search for.

        Returns
        -------
        Optional[:class:`LeagueTierGroupMember`]
            The member, or ``None`` if not found.
        """
        for member in self.members:
            if member.player_tag == tag:
                return member
        return None
