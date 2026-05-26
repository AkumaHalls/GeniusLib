# GeniusLib - Clash of Clans API wrapper
# Based on coc.py (MIT License, copyright (c) 2019-2020 mathsman5133)
# (c) 2026 AkumaHalls / ClashGenius

from geniuslib.abc import BaseClan


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
    """
