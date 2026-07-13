# GeniusLib - Clash of Clans API wrapper
# Based on coc.py (MIT License, copyright (c) 2019-2020 mathsman5133)
# (c) 2026 AkumaHalls / ClashGenius

import asyncio
import inspect
import calendar
import re
import time as _time

from collections import deque, UserDict
from datetime import datetime, timedelta, timezone
from functools import wraps
from operator import attrgetter
from typing import Any, Callable, Generic, Iterable, List, Optional, Type, TypeVar, Union


TAG_VALIDATOR = re.compile(r"^#?[PYLQGRJCUV0289]+$")

TAG_ALPHABET = "0289PYLQGRJCUV"
"""Base-14 character set used for Clash of Clans tags."""


def encode_tag(tag: str) -> int:
    tag = tag.lstrip("#").upper()
    result = 0
    for char in tag:
        result = result * 14 + TAG_ALPHABET.index(char)
    return result


def decode_tag(value: int) -> str:
    if value == 0:
        return "#" + TAG_ALPHABET[0]
    result = ""
    while value > 0:
        result = TAG_ALPHABET[value % 14] + result
        value //= 14
    return "#" + result


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)


def find(predicate: Callable[[T], Any], iterable: Iterable[T]) -> Optional[T]:
    """A helper to return the first element found in the sequence
    that meets the predicate.

    For example: ::

        leader = geniuslib.utils.find(lambda m: m.trophies > 5000, clan.members)

    would find the first :class:`~geniuslib.ClanMember` who has more than 5000 trophies and return it.
    If no members have more than 5000 trophies, then ``None`` is returned.

    Parameters
    -----------
    predicate
        A function that returns a boolean-like result.
    iterable: iterable
        The iterable to search through.

    Returns
    -------
    The first item in the iterable which matches the predicate passed.
    """
    for element in iterable:
        if predicate(element):
            return element
    return None


def get(iterable: Iterable[T], **attrs: Any) -> Optional[T]:
    r"""A helper that returns the first item in an iterable that matches the attributes passed.

    If no match is found, ``None`` is returned.

    Example
    -------
    .. code-block:: python3

        member = utils.get(clan.members, level=100, name="Mathsman")
        # returns the first member who has the name "Mathsman" and is level 100

        member = utils.get(clan.members, role=geniuslib.Role.leader)
        # returns the clan leader

        label = utils.get(player.labels, name="Competitive")
        # returns the player's label if they have Competitive.

    Parameters
    ----------
    iterable: iterable
        The list of items to match the attributes from
    \*\*attrs
        A series of kwargs that specify which attributes to match.

    Returns
    -------
    The object from the iterable that matches the attributes passed, or ``None`` if not found.
    """
    converted = [(attrgetter(attr), value) for attr, value in attrs.items()]
    for elem in iterable:
        if all(pred(elem) == value for pred, value in converted):
            return elem
    return None


def from_timestamp(timestamp: str) -> datetime:
    """Parses the raw timestamp given by the API into a :class:`datetime.datetime` object."""
    return datetime.strptime(timestamp, "%Y%m%dT%H%M%S.000Z")


def is_valid_tag(tag: str) -> bool:
    """Validates that a string is a valid Clash of Clans tag.

    This uses the assumption that tags can only consist of the characters PYLQGRJCUV0289.

    Example
    -------

    .. code-block:: python3

        from geniuslib import utils

        user_input = input("Please enter a tag")

        if utils.is_valid_tag(user_input) is True:
            print("{} is a valid tag".format(user_input))
        else:
            print("{} is not a valid tag".format(user_input))

    Returns
    -------
    :class:`bool`
        Whether the tag is a valid tag.
    """
    if TAG_VALIDATOR.match(correct_tag(tag)):
        return True
    return False


def correct_tag(tag: str, prefix: str = "#") -> str:
    """Attempts to correct malformed Clash of Clans tags
    to match how they are formatted in game

    Example
    -------

    .. code-block:: python3

            new_tag = utils.correct_tag(" 123aBc O")
            # new_tag is "#123ABC0".


    Parameters
    ----------
    tag: str
        The tag to correct.
    prefix: str
        The prefix to insert at the start of the tag. Defaults to ``#``.

    Returns
    -------
    str
        The corrected tag.
    """
    return tag and prefix + re.sub(r"[^A-Z0-9]+", "", tag.upper()).replace("O", "0")


def corrected_tag() -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Helper decorator to fix tags passed into client calls. The tag must be the first parameter."""

    def deco(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            self = args[0]

            if not self.correct_tags:
                return func(*args, **kwargs)

            args = list(args)
            args[1] = correct_tag(args[1])
            return func(*tuple(args), **kwargs)

        return wrapper

    return deco


def maybe_sort(
        seq: Iterable[T], sort: bool, itr: bool = False, key: Callable[[str], Any] = attrgetter("order")
) -> Union[List[T], Iterable[T]]:
    """Returns list or iter based on itr if sort is false otherwise sorted
    with key defaulting to operator.attrgetter('order')
    """
    return (list, iter)[itr](n for n in sorted(seq, key=key)) if sort else (list, iter)[itr](n for n in seq)


def item(
    _object,
    *,
    index: bool = False,
    index_type: Union[int, str] = 0,
    attribute: str = None,
    index_before_attribute: bool = True
):
    """Returns an object, an index, and/or an attribute of the object."""
    attr_get = attrgetter(attribute or "")
    if not (index or index_type or attribute):
        return _object
    if (index or index_type) and not attribute:
        return _object[index_type]
    if attribute and not (index or index_type):
        return attr_get(_object)
    if index_before_attribute:
        return attr_get(_object[index_type])
    return attr_get(_object)[index_type]


def custom_isinstance(obj, module, name):
    """Helper utility to do an `isinstance` check without importing the module (circular imports)"""
    # pylint: disable=broad-except
    for cls in inspect.getmro(type(obj)):
        try:
            if cls.__module__ == module and cls.__name__ == name:
                return True
        except Exception:
            pass
    return False


async def maybe_coroutine(function_, *args, **kwargs):
    """Returns the result of a function which may or may not be a coroutine."""
    value = function_(*args, **kwargs)
    if inspect.isawaitable(value):
        return await value

    return value


def get_season_start(month: Optional[int] = None, year: Optional[int] = None) -> datetime:
    """Get the datetime that the season started.

    This goes by the assumption that SC resets the season on the last monday of every month at 5am UTC.

    .. note::

        If you want the start of the current season, do not pass any parameters in,
        as doing so won't check to ensure the season start is in the past.

    Parameters
    ----------
    month: Optional[int]
        The month to get the season start for. Defaults to the current month/season.
    year: Optional[int]
        The year to get the season start for. Defaults to the current year/season.

    Returns
    -------
    season_start: :class:`datetime.datetime`
        The start of the season.
    """
    # Start date is the last Monday of the month. That's when SC resets the season values
    def get_start_for_month_year(m, y):
        (weekday_of_first_day, days_in_month) = calendar.monthrange(y, m)
        season_start_day = days_in_month - datetime(year=y, month=m, day=days_in_month).weekday()
        return datetime(year=y, month=m, day=season_start_day, hour=5, minute=0, second=0, microsecond=0)

    if month and year:
        # they want a specific month/year combo
        return get_start_for_month_year(month, year)

    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    start = get_start_for_month_year(now.month, now.year)
    if now > start:
        # we got the right one, season started this month
        return start

    # season started last month, so let's try it again.
    if now.month == 1:
        month = 12
        year = now.year - 1
    else:
        month = now.month - 1
        year = now.year
    return get_start_for_month_year(month, year)


def get_season_end(month: Optional[int] = None, year: Optional[int] = None) -> datetime:
    """Get the datetime that the season ends.

    This goes by the assumption that SC resets the season on the last monday of every month at 5am UTC.

    .. note::

        If you want the end of the current season, do not pass any parameters in,
        as doing so won't check to ensure the season end is in the future.

    Parameters
    ----------
    month: Optional[int]
        The month to get the season end for. Defaults to the current month/season.
    year: Optional[int]
        The year to get the season end for. Defaults to the current year/season.

    Returns
    -------
    season_end: :class:`datetime.datetime`
        The end of the season.
    """
    if month and year:
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        return get_season_start(next_month, next_year)

    now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    end = get_season_start(now.month, now.year)
    if end > now:
        return end

    # season ends next month, let's try again
    if now.month == 12:
        month = 1
        year = now.year + 1
    else:
        month = now.month + 1
        year = now.year
    return get_season_start(month, year)


def get_clan_games_start(time: Optional[datetime] = None) -> datetime:
    """Get the datetime that the next clan games will start.

    This goes by the assumption that clan games start at 8am UTC at the 22nd of each month.

    .. note::

        If you want the start of the next or running clan games, do not pass any parameters in,
        for any other pass a datetime in the month before.

    Parameters
    ----------
    time: Optional[datetime]
        Some time in the month before the clan games you want the start of.

    Returns
    -------
    clan_games_start: :class:`datetime.datetime`
        The start of the next or running clan games.
    """
    if time is None:
        time = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    month = time.month
    year = time.year
    this_months_cg_end = datetime(year=time.year, month=time.month, day=28, hour=8, minute=0, second=0)
    if time > this_months_cg_end and month < 12:
        month += 1
    elif time > this_months_cg_end:  # we're at the end of December
        month = 1
        year += 1
    return datetime(year=year, month=month, day=22, hour=8, minute=0, second=0)


def get_clan_games_end(time: Optional[datetime] = None) -> datetime:
    """Get the datetime that the next clan games will end.

    This goes by the assumption that clan games end at 8am UTC at the 28th of each month.

    .. note::

        If you want the end of the next or running clan games, do not pass any parameters in,
        for any other pass a datetime in the month before.

    Parameters
    ----------
    time: Optional[datetime]
        Some time in the month before the clan games you want the end of.

    Returns
    -------
    clan_games_end: :class:`datetime.datetime`
        The end of the next or running clan games.
    """
    if time is None:
        time = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    month = time.month
    year = time.year
    this_months_cg_end = datetime(year=time.year, month=time.month, day=28, hour=8, minute=0, second=0)
    if time > this_months_cg_end and month < 12:
        month += 1
    elif time > this_months_cg_end:  # we're in December
        month = 1
        year += 1
    return datetime(year=year, month=month, day=28, hour=8, minute=0, second=0)


def get_raid_weekend_start(time: Optional[datetime] = None) -> datetime:
    """Get the datetime that the raid weekend will start.

    This goes by the assumption that raid weekends start at friday 7am UTC.

    .. note::

        If you want the start of the next or running raid weekend, do not pass any parameters in,
        for any other pass a datetime in the week before.

    Parameters
    ----------
    time: Optional[datetime]
        Some time in the week before the raid weekend you want the start of.

    Returns
    -------
    raid_weekend_start: :class:`datetime.datetime`
        The start of the raid weekend.
    """
    if time is None:
        time = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    time = get_raid_weekend_end(time)
    time = time - timedelta(days=3)
    return time


def get_raid_weekend_end(time: Optional[datetime] = None) -> datetime:
    """Get the datetime that the raid weekend will end.

    This goes by the assumption that raid weekends end at monday 7am UTC.

    .. note::

        If you want the end of the next or running raid weekend, do not pass any parameters in,
        for any other pass a datetime in the week before.

    Parameters
    ----------
    time: Optional[datetime]
        Some time in the week before the raid weekend you want the end of.

    Returns
    -------
    raid_weekend_end: :class:`datetime.datetime`
        The end of the raid weekend.
    """
    # Shift the time so that we can pretend the raid ends just after midnight
    if time is None:
        time = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    time = time - timedelta(hours=7, microseconds=1)
    time = time + timedelta(weeks=1, days=-time.weekday())  # Go to the next monday
    time = time.replace(hour=7, minute=0, second=0, microsecond=0)
    return time


class _CachedProperty(Generic[T, T_co]):
    def __init__(self, name: str, function: Callable[[T], T_co]) -> None:
        self.name = name
        self.function = function
        self.__doc__ = getattr(function, '__doc__')

    def __get__(self, instance: T, owner: Type[T]) -> T_co:
        try:
            return getattr(instance, self.name)
        except AttributeError:
            result = self.function(instance)
            setattr(instance, self.name, result)
            return result


def cached_property(name: str) -> Callable[[Callable[[T], T_co]], _CachedProperty[T, T_co]]:
    def deco(func: Callable[[T], T_co]) -> _CachedProperty[T, T_co]:
        return _CachedProperty(name, func)
    return deco


class FIFO(UserDict):
    """Implements a FIFO (least-recently-used) dict with a settable max size."""

    __slots__ = (
        "__keys",
        "max_size",
    )

    def __init__(self, max_size):
        self.max_size = max_size
        self.__keys = deque()
        super().__init__()

    def __verify_max_size(self):
        while len(self) > self.max_size:
            del self[self.__keys.popleft()]

    def __setitem__(self, key, value):
        if key in self.data:
            try:
                self.__keys.remove(key)
            except ValueError:
                pass
        self.__keys.append(key)
        super().__setitem__(key, value)
        self.__verify_max_size()

    def __getitem__(self, key):
        self.__verify_max_size()
        return super().__getitem__(key)

    def __contains__(self, key):
        self.__verify_max_size()
        return super().__contains__(key)

    def copy(self):
        new_fifo = FIFO(self.max_size)
        new_fifo.data = self.data.copy()
        new_fifo._FIFO__keys = deque(self.__keys)
        return new_fifo


class HTTPStats(dict):
    """Implements a basic key: deque value to aid with HTTP performance stats."""

    __slots__ = ("max_size",)

    def __init__(self, max_size):
        self.max_size = max_size
        super().__init__()

    def __setitem__(self, key, value):
        try:
            super().__getitem__(key).append(value)
        except (KeyError, AttributeError):
            super().__setitem__(key, deque((value,), maxlen=self.max_size))

    def get_average(self, key):
        """Get the average latency / performance counter for an API endpoint"""
        try:
            stats = self[key]
        except KeyError:
            return None

        return sum(stats) / len(stats)

    def get_mixed_average(self):
        """Get the average latency / performance counter for all API endpoints"""
        all_values = [v for values in self.values() for v in values]
        if not all_values:
            return 0.0
        return sum(all_values) / len(all_values)

    def get_all_average(self):
        """Get the average latency / performance counter for each API endpoint."""
        return {k: sum(v) / len(v) for k, v in self.items()}


class CaseInsensitiveDict(dict):
    def __getitem__(self, key):
        if isinstance(key, tuple):
            key = tuple(x.lower() if isinstance(x, str) else x for x in key)
        else:
            key = key.lower()

        return super().__getitem__(key)

    def get(self, key, default=None):
        if isinstance(key, tuple):
            key = tuple(x.lower() if isinstance(x, str) else x for x in key)
        else:
            key = key.lower()

        return super().get(key, default)

    def __setitem__(self, key, v):
        if isinstance(key, tuple):
            key = tuple(x.lower() if isinstance(x, str) else x for x in key)
        else:
            key = key.lower()

        super().__setitem__(key, v)


def get_season_id(month: Optional[int] = None, year: Optional[int] = None) -> str:
    if month is None or year is None:
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        start = get_season_start(now.month, now.year)
        if now < start:
            if now.month == 1:
                month, year = 12, now.year - 1
            else:
                month, year = now.month - 1, now.year
        else:
            month, year = now.month, now.year
    return f"{year:04d}-{month:02d}"


def get_league_trophies(trophies: int) -> int:
    return max(0, trophies - 4900)


def estimate_trophy_change(
    stars: int,
    destruction: float,
    attacker_trophies: int,
    defender_trophies: int,
) -> int:
    trophy_diff = defender_trophies - attacker_trophies
    base = trophy_diff * 0.05
    star_bonus = stars * 5.0
    destruction_bonus = (destruction / 100.0) * 3.0
    return round(base + star_bonus + destruction_bonus)


def estimate_raid_medals(
    capital_gold_looted: int,
    attacks_used: int,
    districts_destroyed: int,
    clan_league: Optional[str] = None,
) -> int:
    league_bonuses = {
        "Unranked": 0, "Bronze III": 45, "Bronze II": 54, "Bronze I": 63,
        "Silver III": 72, "Silver II": 81, "Silver I": 90,
        "Gold III": 99, "Gold II": 108, "Gold I": 117,
        "Master III": 126, "Master II": 135, "Master I": 144,
        "Champion III": 153, "Champion II": 162, "Champion I": 171,
        "Titan III": 180, "Titan II": 185, "Titan I": 190,
        "Legend III": 195, "Legend II": 200, "Legend I": 205,
    }
    league_bonus = league_bonuses.get(clan_league, 100) if clan_league else 100

    gold_bonus = int(capital_gold_looted * 0.015)
    attack_bonus = attacks_used * 2
    district_bonus = districts_destroyed * 5

    return league_bonus + gold_bonus + attack_bonus + district_bonus


class TTLCache(UserDict):
    __slots__ = ("ttl", "maxsize", "_times", "_sweeper_task", "_loop")

    def __init__(self, ttl: int = 300, maxsize: Optional[int] = None):
        self.ttl = ttl
        self.maxsize = maxsize
        self._times: dict = {}
        self._sweeper_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        super().__init__()

    def _now(self) -> float:
        return _time.monotonic()

    def _evict_expired(self) -> None:
        now = self._now()
        expired = [k for k, t in self._times.items() if now - t > self.ttl]
        for k in expired:
            super().__delitem__(k)
            del self._times[k]

    def _enforce_maxsize(self) -> None:
        if self.maxsize is None:
            return
        while len(self) > self.maxsize:
            oldest = min(self._times, key=self._times.get)
            super().__delitem__(oldest)
            del self._times[oldest]

    def __setitem__(self, key, value) -> None:
        self._times[key] = self._now()
        super().__setitem__(key, value)
        self._enforce_maxsize()

    def __getitem__(self, key):
        self._evict_expired()
        return super().__getitem__(key)

    def __contains__(self, key) -> bool:
        self._evict_expired()
        return super().__contains__(key)

    def get(self, key, default=None):
        self._evict_expired()
        return super().get(key, default)

    async def start_sweeper(self, interval: int = 60) -> None:
        self._loop = asyncio.get_running_loop()
        self._sweeper_task = asyncio.create_task(self._sweep_loop(interval))

    async def _sweep_loop(self, interval: int) -> None:
        while True:
            await asyncio.sleep(interval)
            self._evict_expired()

    def stop_sweeper(self) -> None:
        if self._sweeper_task:
            self._sweeper_task.cancel()
            self._sweeper_task = None

    @property
    def size(self) -> int:
        self._evict_expired()
        return len(self.data)

    def clear(self) -> None:
        super().clear()
        self._times.clear()


def _get_maybe_first(dict_items, lookup, default=None):
    try:
        items = dict_items[lookup]
    except KeyError:
        return default
    else:
        try:
            return items[0]
        except (IndexError, KeyError):
            return default
