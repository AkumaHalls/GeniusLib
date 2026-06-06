"""Tests for the utils module."""

import pytest
from datetime import datetime, timezone
from geniuslib import utils


class TestTagEncodeDecode:
    def test_encode_tag(self):
        assert utils.encode_tag("#2PP") == 256
        assert utils.encode_tag("2PP") == 256
        assert utils.encode_tag("#") == 0

    def test_decode_tag(self):
        assert utils.decode_tag(256) == "#2PP"
        assert utils.decode_tag(0) == "#0"

    def test_roundtrip(self):
        tags = ["#2PP", "#9Y", "#PYLQGRJCUV", "#0"]
        for tag in tags:
            encoded = utils.encode_tag(tag)
            decoded = utils.decode_tag(encoded)
            assert decoded == tag


class TestTagValidation:
    def test_is_valid_tag(self):
        assert utils.is_valid_tag("#2PP") is True
        assert utils.is_valid_tag("#9Y") is True
        assert utils.is_valid_tag("#XYZ!") is False
        assert utils.is_valid_tag("") is False

    def test_correct_tag(self):
        assert utils.correct_tag(" 123aBc O") == "#123ABC0"
        assert utils.correct_tag("#abc") == "#ABC"
        assert utils.correct_tag("") == ""


class TestFind:
    def test_find_found(self):
        items = [{"name": "a", "val": 1}, {"name": "b", "val": 2}]
        result = utils.find(lambda x: x["name"] == "b", items)
        assert result["val"] == 2

    def test_find_not_found(self):
        items = [{"name": "a", "val": 1}]
        result = utils.find(lambda x: x["name"] == "z", items)
        assert result is None


class TestGet:
    def test_get_found(self):
        class Obj:
            def __init__(self, name, level):
                self.name = name
                self.level = level

        items = [Obj("a", 1), Obj("b", 2)]
        result = utils.get(items, name="b", level=2)
        assert result is items[1]

    def test_get_not_found(self):
        class Obj:
            def __init__(self, name):
                self.name = name

        items = [Obj("a")]
        result = utils.get(items, name="z")
        assert result is None


class TestTimestamp:
    def test_from_timestamp(self):
        dt = utils.from_timestamp("20260501T120000.000Z")
        assert dt.year == 2026
        assert dt.month == 5
        assert dt.day == 1
        assert dt.hour == 12


class TestSeasonMath:
    def test_get_season_id_format(self):
        sid = utils.get_season_id(5, 2026)
        assert sid == "2026-05"
        assert isinstance(sid, str)

    def test_get_season_start_end(self):
        start = utils.get_season_start(5, 2026)
        end = utils.get_season_end(5, 2026)
        assert end > start

    def test_get_league_trophies(self):
        assert utils.get_league_trophies(5200) == 300
        assert utils.get_league_trophies(4900) == 0
        assert utils.get_league_trophies(4000) == 0

    def test_estimate_trophy_change(self):
        result = utils.estimate_trophy_change(3, 100, 5000, 4900)
        assert isinstance(result, int)
        assert result > 0

    def test_estimate_raid_medals(self):
        medals = utils.estimate_raid_medals(50000, 6, 4, "Gold I")
        assert isinstance(medals, int)
        assert medals > 100


class TestTTLCache:
    @pytest.mark.asyncio
    async def test_basic_operations(self):
        cache = utils.TTLCache(ttl=300)
        cache["key"] = "value"
        assert cache["key"] == "value"
        assert "key" in cache
        assert cache.get("key") == "value"
        assert cache.size == 1

    def test_eviction_by_maxsize(self):
        cache = utils.TTLCache(ttl=300, maxsize=2)
        cache["a"] = 1
        cache["b"] = 2
        cache["c"] = 3
        assert cache.size <= 2
        assert "a" not in cache

    def test_clear(self):
        cache = utils.TTLCache(ttl=300)
        cache["a"] = 1
        cache.clear()
        assert cache.size == 0


class TestHTTPStats:
    def test_record_and_average(self):
        stats = utils.HTTPStats(max_size=100)
        stats["/clans"] = 100.0
        stats["/clans"] = 200.0
        assert stats.get_average("/clans") == 150.0

    def test_mixed_average(self):
        stats = utils.HTTPStats(max_size=100)
        stats["/clans"] = 100.0
        stats["/players"] = 200.0
        assert stats.get_mixed_average() == 150.0


class TestClanGames:
    def test_clan_games_start_end(self):
        start = utils.get_clan_games_start()
        end = utils.get_clan_games_end()
        assert end > start

    def test_raid_weekend_start_end(self):
        start = utils.get_raid_weekend_start()
        end = utils.get_raid_weekend_end()
        assert end > start
