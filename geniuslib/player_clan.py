# GeniusLib - Clash of Clans API wrapper
# Based on coc.py (MIT License, copyright (c) 2019-2020 mathsman5133)
# (c) 2026 AkumaHalls / ClashGenius

from geniuslib.abc import BaseClan
from geniuslib.miscmodels import try_enum, Badge


class PlayerClan(BaseClan):
    """Represents a clan that belongs to a player.

    Attributes
    ----------
    tag: :class:`str`
        The clan's tag
    name: :class:`str`
        The clan's name
    badge: :class:`Badge`
        The clan's badge
    level: :class:`int`
        The clan's level.
    clan_points: :class:`int`
        The clan's points.
    clan_builder_base_points: :class:`int`
        The clan's builder base points.
    clan_capital_points: :class:`int`
        The clan's capital points.
    """

    __slots__ = (
        "clan_points",
        "clan_builder_base_points",
        "clan_capital_points",
    )

    def __init__(self, *, data, client=None, **_):
        super().__init__(data=data, client=client)
        data_get = data.get
        self.clan_points: int = data_get("clanPoints", 0)
        self.clan_builder_base_points: int = data_get("clanBuilderBasePoints", 0)
        self.clan_capital_points: int = data_get("clanCapitalPoints", 0)
