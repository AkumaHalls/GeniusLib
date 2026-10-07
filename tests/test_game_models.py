"""Tests for the model-layer defensive-parsing and hashing audit fixes.

These tests exercise the code paths changed during the audit: missing API keys,
broken paging edge cases, ``__hash__``/``__eq__`` consistency and level-manager
behaviour. No network access is required; models are built from dict payloads.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from geniuslib.abc import LeveledUnit, LevelManager
from geniuslib.battlelog import (
    BattleLogEntry,
    BattleLogResource,
    LeagueHistoryEntry,
    LeagueTierGroupMember,
)
from geniuslib.buildings import Building
from geniuslib.clans import Clan, RankedClan
from geniuslib.entry_logs import RaidLog
from geniuslib.enums import BuildingType, WarRound
from geniuslib.game_data import AccountData
from geniuslib.miscmodels import LoadGameData
from geniuslib.raid import RaidAttack, RaidClan, RaidDistrict, RaidLogEntry, RaidMember
from geniuslib.war_attack import WarAttack
from geniuslib.wars import (
    ClanWar,
    ClanWarLeagueGroup,
    ClanWarLogEntry,
    ExtendedCWLGroup,
)

BADGE_URLS = {"small": "s", "medium": "m", "large": "l"}


def _war_data(clan_tag="#CLAN1", *, home_members=None, opp_members=None, state="warEnded"):
    return {
        "tag": "#WAR1",
        "state": state,
        "season": "2026-10",
        "preparationStartTime": "20260101T000000.000Z",
        "startTime": "20260102T000000.000Z",
        "endTime": "20260103T000000.000Z",
        "teamSize": 5,
        "attacksPerMember": 1,
        "battleModifier": "none",
        "clan": {
            "tag": clan_tag,
            "name": "Clan A",
            "badgeUrls": BADGE_URLS,
            "clanLevel": 10,
            "attacks": 3,
            "stars": 6,
            "destructionPercentage": 60.0,
            "members": home_members or [],
        },
        "opponent": {
            "tag": "#CLAN2",
            "name": "Clan B",
            "badgeUrls": BADGE_URLS,
            "clanLevel": 9,
            "attacks": 0,
            "stars": 0,
            "destructionPercentage": 0.0,
            "members": opp_members or [],
        },
    }


def _build_war(clan_tag="#CLAN1", *, home_members=None, opp_members=None):
    data = _war_data(clan_tag, home_members=home_members, opp_members=opp_members)
    return ClanWar(data=data, client=None, clan_tag=clan_tag)


def _member(tag, name, position, *, attacks=(), opponent_attacks=0, best=None):
    data = {
        "tag": tag,
        "name": name,
        "townhallLevel": 15,
        "mapPosition": position,
        "opponentAttacks": opponent_attacks,
        "attacks": list(attacks),
    }
    if best:
        data["bestOpponentAttack"] = {"attackerTag": best}
    return data


def _attack(attacker, defender, *, stars, destruction, order, duration=60):
    return {
        "attackerTag": attacker,
        "defenderTag": defender,
        "stars": stars,
        "destructionPercentage": destruction,
        "order": order,
        "duration": duration,
    }


def _war_log_data(result="win"):
    return {
        "tag": "#WAR1",
        "result": result,
        "endTime": "20260103T000000.000Z",
        "attacksPerMember": 1,
        "teamSize": 5,
        "clan": {"tag": "#CLAN1", "name": "A", "badgeUrls": BADGE_URLS, "clanLevel": 10},
        "opponent": {"tag": "#CLAN2", "name": "B", "badgeUrls": BADGE_URLS, "clanLevel": 9},
    }


def _clan_data(**overrides):
    data = {
        "tag": "#CLAN1",
        "name": "Clan A",
        "badgeUrls": BADGE_URLS,
        "clanLevel": 10,
        "clanPoints": 25000,
        "members": 2,
        "labels": [],
        "memberList": [],
        "warWins": 15,
    }
    data.update(overrides)
    return data


def _clan_member(tag, name, *, builder, rank):
    return {
        "tag": tag,
        "name": name,
        "expLevel": 10,
        "trophies": 1000,
        "builderBaseTrophies": builder,
        "clanRank": rank,
        "previousClanRank": rank,
        "donations": 0,
        "donationsReceived": 0,
        "role": "member",
        "townHallLevel": 12,
    }


def _cwl_group(state="inWar", rounds=None):
    data = {"state": state, "season": "2026-10", "rounds": rounds or [], "clans": []}
    return ClanWarLeagueGroup(data=data, client=None)


def _raid_log(client=None, json_resp=None, *, limit=1, page=True):
    client = client or MagicMock()
    client.lookup_cache = None
    client.update_cache = None
    client.ignore_cached_errors = None
    log = RaidLog(
        client=client,
        clan_tag="#CLAN",
        limit=limit,
        page=page,
        json_resp=json_resp or {"items": []},
        model=RaidLogEntry,
    )
    return log


def _make_client(static_data):
    client = MagicMock()
    client._static_data = static_data
    client.raw_attribute = False
    return client


class _Unit(LevelManager):
    __slots__ = ("build_cost",)

    def _load_level_data(self):
        self.build_cost = 0


class _RaisingUnit(LevelManager):
    __slots__ = ()

    @property
    def broken(self):
        raise AttributeError("inner failure")


# ---------------------------------------------------------------------------
# game_data.py item 14 hardening
# ---------------------------------------------------------------------------


def test_account_building_without_seasonal_defenses_or_levels():
    static = {
        1000097: {
            "_id": 1000097,
            "name": "Crafting Station",
            "info": "",
            "TID": {"name": "TID_BUILDING_SEASONAL_PLATFORM", "info": ""},
            "type": "Defense",
            "upgrade_resource": "Gold",
            "village": "home",
            "width": 3,
            "superchargeable": False,
            "levels": [],
        }
    }
    account = AccountData(
        data={"buildings": [{"data": 1000097, "lvl": 3, "cnt": 1}]},
        client=_make_client(static),
    )
    assert len(account.buildings) == 1
    building, count = account.buildings[0]
    assert count == 1
    assert isinstance(building, Building)
    assert building.id == 1000097
    assert building.level == 3
    assert building.type == BuildingType.defense
    assert building.seasonal_defenses == []
    assert account.townhall_level == 0


def test_account_building_handles_missing_seasonal_module_data():
    static = {
        1000097: {
            "_id": 1000097,
            "name": "Crafting Station",
            "info": "",
            "TID": {"name": "TID_BUILDING_SEASONAL_PLATFORM", "info": ""},
            "type": "Defense",
            "upgrade_resource": "Gold",
            "village": "home",
            "width": 3,
            "superchargeable": False,
            "levels": [],
            "seasonal_defenses": [
                {"_id": 103000011, "name": "Hot Candle", "info": "", "TID": {"name": "TID_CANDLE", "info": ""}}
            ],
        }
    }
    account_data = {
        "buildings": [
            {
                "data": 1000097,
                "lvl": 1,
                "cnt": 1,
                "types": [{"data": 103000011, "modules": [{"data": 102000033, "lvl": 1}]}],
            }
        ]
    }
    account = AccountData(data=account_data, client=_make_client(static))
    building, _ = account.buildings[0]
    assert building.seasonal_defenses[0].id == 103000011
    assert building.seasonal_defenses[0].modules == []


def test_account_units_default_level_when_lvl_missing():
    static = {
        4000001: {
            "_id": 4000001,
            "name": "Archer",
            "info": "shoots arrows",
            "TID": {"name": "TID_ARCHER", "info": ""},
            "production_building": "Barracks",
            "production_building_level": 2,
            "upgrade_resource": "Elixir",
            "is_flying": False,
            "is_air_targeting": True,
            "is_ground_targeting": True,
            "movement_speed": 300,
            "attack_speed": 1000,
            "attack_range": 350,
            "housing_space": 1,
            "village": "home",
            "levels": [
                {
                    "level": 1,
                    "hitpoints": 22,
                    "dps": 8,
                    "upgrade_time": 3600,
                    "upgrade_cost": 20000,
                    "required_lab_level": 1,
                    "required_townhall": 3,
                }
            ],
        }
    }
    account = AccountData(data={"units": [{"data": 4000001}]}, client=_make_client(static))
    assert len(account.troops) == 1
    troop = account.troops[0]
    assert troop.id == 4000001
    assert troop.level == 1
    assert troop.max_level == 1
    assert troop.hitpoints == 22
    assert account.upgrades == []


# ---------------------------------------------------------------------------
# extended CWL group + rounds guards (items 5/6)
# ---------------------------------------------------------------------------


def test_extended_cwl_group_missing_id_is_none():
    group = ExtendedCWLGroup(
        data={
            "name": "League",
            "TID": {"name": "TID_LEAGUE", "info": ""},
            "cwl_medals": {
                "first_place": 300,
                "position_medal_diff": 50,
                "bonus_reward": 90,
                "minimum_bonus_amount": 20,
            },
            "promotions": 1,
            "demotions": 1,
            "15v15_only": True,
        }
    )
    assert group._id is None
    assert group.first_place_medals == 300
    assert group.only15v15 is True


def test_cwl_group_rounds_filter_invalid():
    group = _cwl_group(
        rounds=[
            {"warTags": ["#0", "#0", "#0"]},
            {},
            {"warTags": ["#W1", "#W2"]},
            {"warTags": ["#W3", "#W4", "#W5"]},
        ]
    )
    assert group.number_of_rounds == 4
    assert group.rounds == [["#W1", "#W2"], ["#W3", "#W4", "#W5"]]


async def test_cwl_group_previous_war_first_round_empty():
    group = _cwl_group(rounds=[{"warTags": ["#W1"]}])
    it = group.get_wars(cwl_round=WarRound.previous_war, cls=None)
    assert it.tags == []


async def test_cwl_group_previous_war_scenarios():
    two_inwar = _cwl_group(
        state="inWar",
        rounds=[{"warTags": ["#W1"]}, {"warTags": ["#W2"]}],
    )
    assert two_inwar.get_wars(cwl_round=WarRound.previous_war, cls=None).tags == []

    prep = _cwl_group(
        state="preparation",
        rounds=[{"warTags": ["#W1"]}, {"warTags": ["#W2"]}],
    )
    assert prep.get_wars(cwl_round=WarRound.previous_war, cls=None).tags == ["#W1"]

    three = _cwl_group(
        state="inWar",
        rounds=[{"warTags": ["#W1"]}, {"warTags": ["#W2"]}, {"warTags": ["#W3"]}],
    )
    assert three.get_wars(cwl_round=WarRound.previous_war, cls=None).tags == ["#W1"]


async def test_cwl_group_current_war_and_prep_shortcuts():
    group = _cwl_group(
        state="inWar",
        rounds=[{"warTags": ["#W1"]}, {"warTags": ["#W2"]}],
    )
    assert group.get_wars(cwl_round=WarRound.current_war, cls=None).tags == ["#W1"]

    prep = _cwl_group(
        state="preparation",
        rounds=[{"warTags": ["#W1"]}, {"warTags": ["#W2"]}],
    )
    assert prep.get_wars(cwl_round=WarRound.current_war, cls=None).tags == []

    ended = _cwl_group(state="warEnded", rounds=[{"warTags": ["#W1"]}])
    assert ended.get_wars(cwl_round=WarRound.current_preparation, cls=None).tags == []


# ---------------------------------------------------------------------------
# entry_logs.py paginator (item 3)
# ---------------------------------------------------------------------------


async def test_raid_log_missing_paging_key_stops():
    log = _raid_log(json_resp={"items": [{"state": "inWar"}]})
    log._fetch_endpoint = AsyncMock(return_value={"items": []})
    entries = []
    async for entry in log:
        entries.append(entry)
    assert len(entries) == 1
    log._fetch_endpoint.assert_not_awaited()


async def test_raid_log_missing_items_key_on_next_page_stops():
    calls = []

    async def fake_fetch(client, clan_tag, **options):
        calls.append(options.get("after"))
        return {"paging": {"cursors": {"after": None}}}

    log = _raid_log(json_resp={"items": [{"state": "inWar"}], "paging": {"cursors": {"after": "cur1"}}})
    log._fetch_endpoint = fake_fetch
    entries = []
    async for entry in log:
        entries.append(entry)
    assert len(entries) == 1
    assert calls == ["cur1"]


async def test_raid_log_repeated_cursor_stalls():
    calls = []

    async def fake_fetch(client, clan_tag, **options):
        calls.append(options.get("after"))
        return {"items": [{"state": "inWar"}], "paging": {"cursors": {"after": "cur1"}}}

    log = _raid_log(json_resp={"items": [{"state": "inWar"}], "paging": {"cursors": {"after": "cur1"}}})
    log._fetch_endpoint = fake_fetch
    entries = []
    async for entry in log:
        entries.append(entry)
    assert len(entries) == 2
    assert len(calls) == 1


async def test_raid_log_empty_next_page_stops():
    calls = []

    async def fake_fetch(client, clan_tag, **options):
        calls.append(options.get("after"))
        return {"items": [], "paging": {"cursors": {"after": "cur2"}}}

    log = _raid_log(json_resp={"items": [{"state": "inWar"}], "paging": {"cursors": {"after": "cur1"}}})
    log._fetch_endpoint = fake_fetch
    entries = []
    async for entry in log:
        entries.append(entry)
    assert len(entries) == 1
    assert calls == ["cur1"]


# ---------------------------------------------------------------------------
# war accessors + previous_best_opponent_attack (items 4/7)
# ---------------------------------------------------------------------------


def test_clan_war_get_unknown_member_and_attack():
    war = _build_war()
    assert war.get_member("#UNKNOWN") is None
    assert war.get_attack("#UNKNOWN", "#OP1") is None
    assert war.get_attack("#PL1", "#UNKNOWN") is None


def test_clan_war_get_defenses_unknown_returns_empty():
    war = _build_war()
    assert war.get_defenses("#UNKNOWN") == []


def test_previous_best_opponent_attack_none_without_defenses():
    war = _build_war(home_members=[], opp_members=[_member("#OP1", "O1", 1, opponent_attacks=0)])
    opp1 = war.get_member("#OP1")
    assert opp1 is not None
    assert opp1.previous_best_opponent_attack is None


def test_previous_best_opponent_attack_excludes_best():
    home = [
        _member("#PL1", "P1", 1, attacks=[_attack("#PL1", "#OP1", stars=2, destruction=60, order=1)]),
        _member("#PL2", "P2", 2, attacks=[_attack("#PL2", "#OP1", stars=3, destruction=95, order=3)]),
        _member("#PL3", "P3", 3, attacks=[_attack("#PL3", "#OP1", stars=3, destruction=90, order=2)]),
    ]
    opp = [_member("#OP1", "O1", 1, opponent_attacks=3, best="#PL1")]
    war = _build_war(home_members=home, opp_members=opp)
    prev = war.get_member("#OP1").previous_best_opponent_attack
    assert prev is not None
    assert prev.attacker_tag == "#PL2"


def test_previous_best_returns_max_when_no_best_attack():
    home = [
        _member("#PL1", "P1", 1, attacks=[_attack("#PL1", "#OP1", stars=2, destruction=60, order=1)]),
        _member("#PL2", "P2", 2, attacks=[_attack("#PL2", "#OP1", stars=3, destruction=95, order=2)]),
    ]
    opp = [_member("#OP1", "O1", 1, opponent_attacks=2)]
    war = _build_war(home_members=home, opp_members=opp)
    prev = war.get_member("#OP1").previous_best_opponent_attack
    assert prev is not None
    assert prev.attacker_tag == "#PL2"


def test_war_attack_missing_fields_defaults():
    attack = WarAttack(data={}, client=None, war=None)
    assert attack.stars == 0
    assert attack.destruction == 0.0
    assert attack.order == 0
    assert attack.duration == 0
    assert attack.attacker_tag is None
    assert attack.defender_tag is None


# ---------------------------------------------------------------------------
# hashing (item 10)
# ---------------------------------------------------------------------------


def test_battle_log_resource_default_amount_and_hash():
    resource = BattleLogResource(data={"name": "gold"})
    assert resource.amount == 0
    other = BattleLogResource(data={"name": "gold", "amount": 0})
    assert resource == other
    assert hash(resource) == hash(other)
    assert len({resource, other}) == 1


def test_battle_log_entry_equal_and_hash():
    data = {
        "attack": True,
        "opponentPlayerTag": "#OP",
        "timestamp": "20260101T000000.000Z",
        "stars": 3,
        "destructionPercentage": 100,
    }
    first = BattleLogEntry(data=data)
    second = BattleLogEntry(data=data)
    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second}) == 1


def test_league_history_entry_defaults_zero():
    entry = LeagueHistoryEntry(data={"leagueSeasonId": 5})
    assert entry.league_season_id == 5
    assert entry.league_trophies == 0
    assert entry.league_tier_id == 0
    assert entry.placement == 0
    assert entry.attack_wins == 0
    assert entry.attack_losses == 0
    assert entry.attack_stars == 0
    assert entry.defense_wins == 0
    assert entry.defense_losses == 0
    assert entry.defense_stars == 0
    assert entry.max_battles == 0
    assert entry.total_attacks == 0


def test_league_history_entry_hash_by_season():
    first = LeagueHistoryEntry(data={"leagueSeasonId": 1, "leagueTrophies": 10})
    second = LeagueHistoryEntry(data={"leagueSeasonId": 1, "leagueTrophies": 20})
    third = LeagueHistoryEntry(data={"leagueSeasonId": 2})
    assert first == second
    assert hash(first) == hash(second)
    assert first != third
    assert hash(first) != hash(third)


def test_league_tier_group_member_defaults_zero():
    member = LeagueTierGroupMember(data={"playerTag": "#P1"})
    assert member.league_trophies == 0
    assert member.attack_win_count == 0
    assert member.attack_lose_count == 0
    assert member.defense_win_count == 0
    assert member.defense_lose_count == 0


def test_raid_member_hash_equal():
    data = {
        "tag": "#P1",
        "name": "P1",
        "attacks": 2,
        "attackLimit": 3,
        "bonusAttackLimit": 1,
        "capitalResourcesLooted": 100,
    }
    first = RaidMember(data=data, client=None, raid_log_entry=None)
    second = RaidMember(data=data, client=None, raid_log_entry=None)
    assert first == second
    assert hash(first) == hash(second)


def test_raid_attack_hash_by_attacker():
    data = {"attacker": {"tag": "#P1", "name": "P1"}, "destructionPercent": 50.0, "stars": 2}
    first = RaidAttack(data, None, None, None, None)
    second = RaidAttack(data, None, None, None, None)
    other = RaidAttack(
        {"attacker": {"tag": "#P2", "name": "P2"}, "destructionPercent": 50.0, "stars": 2}, None, None, None, None
    )
    assert first == second
    assert hash(first) == hash(second)
    assert hash(first) != hash(other)


def test_raid_district_defaults_and_hash():
    district = RaidDistrict(data={}, client=None, raid_log_entry=None, raid_clan=None)
    assert district.stars == 0
    assert district.destruction == 0.0
    assert district.attack_count == 0
    assert district.looted == 0
    assert district.attacks == []
    twin = RaidDistrict(data={}, client=None, raid_log_entry=None, raid_clan=None)
    assert district == twin
    assert hash(district) == hash(twin)


def test_raid_clan_attacker_only_data_and_none():
    attacker = RaidClan(
        data={
            "attacker": {"tag": "#CLAN1", "name": "A", "badgeUrls": BADGE_URLS, "level": 5},
            "attackCount": 3,
            "districtCount": 5,
            "districtsDestroyed": 1,
        },
        client=None,
        raid_log_entry=None,
    )
    assert attacker.tag == "#CLAN1"
    assert attacker.name == "A"
    assert attacker.attack_count == 3

    empty = RaidClan(data={}, client=None, raid_log_entry=None)
    assert empty.tag is None
    assert empty.attack_count is None


def test_raid_clan_hash_by_tag_and_index():
    data = {
        "attacker": {"tag": "#CLAN1", "name": "A", "badgeUrls": BADGE_URLS, "level": 5},
        "attackCount": 3,
        "districtCount": 5,
        "districtsDestroyed": 1,
    }
    first = RaidClan(data=data, client=None, raid_log_entry=None, index=0)
    second = RaidClan(data=data, client=None, raid_log_entry=None, index=0)
    other = RaidClan(data=data, client=None, raid_log_entry=None, index=1)
    assert first == second
    assert hash(first) == hash(second)
    assert hash(first) != hash(other)


def test_raid_log_entry_hash_equal():
    data = {"state": "inWar", "startTime": "20260101T000000.000Z"}
    first = RaidLogEntry(data=data, client=None, clan_tag="#CLAN1")
    second = RaidLogEntry(data=data, client=None, clan_tag="#CLAN1")
    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second}) == 1


def test_clan_war_equal_and_hash():
    first = _build_war(clan_tag="#CLAN1")
    second = _build_war(clan_tag="#CLAN1")
    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second}) == 1


def test_clan_war_unequal_when_preparation_time_differs():
    first = _build_war()
    data = _war_data()
    data["preparationStartTime"] = "20260110T000000.000Z"
    second = ClanWar(data=data, client=None, clan_tag="#CLAN1")
    assert first != second


def test_clan_war_log_entry_equal_and_hash():
    first = ClanWarLogEntry(data=_war_log_data(), client=None)
    second = ClanWarLogEntry(data=_war_log_data(), client=None)
    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second}) == 1


def test_clan_war_log_entry_result_differs_hash():
    first = ClanWarLogEntry(data=_war_log_data(), client=None)
    second = ClanWarLogEntry(data=_war_log_data(result="lose"), client=None)
    assert first != second
    assert hash(first) != hash(second)


def test_base_clan_equal_and_hash():
    first = RankedClan(data=_clan_data(), client=None)
    second = RankedClan(data=_clan_data(), client=None)
    assert first == second
    assert hash(first) == hash(second)


# ---------------------------------------------------------------------------
# clans.py items 8/9 + abc.py item 4
# ---------------------------------------------------------------------------


def test_clan_war_ties_and_losses_default_to_none():
    clan = Clan(data=_clan_data(), client=None)
    assert clan.war_ties is None
    assert clan.war_losses is None
    assert clan.war_wins == 15
    assert clan.war_ties == clan.war_losses


def test_clan_members_sorted_by_builder_trophies_and_raw_untouched():
    member_list = [
        _clan_member("#PL1", "A", builder=500, rank=2),
        _clan_member("#PL2", "B", builder=900, rank=1),
    ]
    data = _clan_data(memberList=list(member_list))
    clan = Clan(data=data, client=None)
    assert [m.tag for m in clan.members] == ["#PL2", "#PL1"]
    assert clan.get_member("#PL2").builder_base_rank == 1
    assert clan.get_member("#PL1").builder_base_rank == 2
    assert "builderBaseRank" not in member_list[0]
    assert "builderBaseRank" not in member_list[1]


def test_ranked_clan_members_raises_not_implemented():
    clan = RankedClan(data=_clan_data(), client=None)
    with pytest.raises(NotImplementedError, match="does not load members"):
        clan.members


# ---------------------------------------------------------------------------
# abc.py LevelManager (item 12)
# ---------------------------------------------------------------------------


def test_level_manager_setter_rejects_zero():
    unit = _Unit(1, {"levels": [{"level": 1, "max_level": 5}]})
    with pytest.raises(ValueError, match="Level must be greater than 1"):
        unit.level = 0


def test_level_manager_missing_levels_key_safe():
    unit = _Unit(1, {"no_levels": True})
    assert unit.max_level == 0
    unit.level = 3
    assert unit.level == 3


def test_level_manager_static_data_hint_for_slot_missing():
    unit = _Unit(1, None)
    with pytest.raises(AttributeError, match="static game data"):
        unit.build_cost


def test_level_manager_raw_data_hint():
    unit = LevelManager(initial_level=1, static_data=None)
    with pytest.raises(AttributeError, match="raw_attribute"):
        unit._raw_data


def test_level_manager_preserves_inner_attribute_error():
    unit = _RaisingUnit(1, None)
    with pytest.raises(AttributeError, match="inner failure"):
        unit.broken


def test_max_level_for_townhall_returns_none_without_static():
    unit = LeveledUnit(initial_level=1, static_data=None)
    assert unit.get_max_level_for_townhall(15) is None


def test_max_level_for_townhall_matches_level_data():
    unit = LeveledUnit(
        0,
        {
            "levels": [
                {"level": 1, "required_townhall": 3},
                {"level": 2, "required_townhall": 5},
                {"level": 3, "required_townhall": 5},
                {"level": 4, "required_townhall": 9},
            ]
        },
    )
    assert unit.get_max_level_for_townhall(2) is None
    assert unit.get_max_level_for_townhall(5) == 3
    assert unit.get_max_level_for_townhall(9) == 4


# ---------------------------------------------------------------------------
# miscmodels.py LoadGameData message (item 13)
# ---------------------------------------------------------------------------


def test_load_game_data_invalid_option_message():
    with pytest.raises(RuntimeError, match="not a valid LoadGameData option"):
        LoadGameData(foo=True)
