"""Tests for the battlelog_analytics module."""

import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from geniuslib.battlelog import (
    BattleLogEntry,
    BattleLogResource,
    LeagueHistoryEntry,
    LeagueTierGroup,
    LeagueTierGroupBattleLogEntry,
    LeagueTierGroupMember,
)
from geniuslib import battlelog_analytics


# ---------------------------------------------------------------------------
# Helpers – build real model objects from minimal dicts
# ---------------------------------------------------------------------------

def _make_attack_entry(stars=3, destruction=100, gold=100000, elixir=80000, dark=0, ts="20260101T120000.000Z"):
    return BattleLogEntry(data={
        "battleType": "legendLeague",
        "attack": True,
        "timestamp": ts,
        "armyShareCode": "ABC123",
        "opponentPlayerTag": "#OPP1",
        "stars": stars,
        "destructionPercentage": destruction,
        "lootedResources": [
            {"name": "gold", "amount": gold},
            {"name": "elixir", "amount": elixir},
        ] + ([{"name": "darkElixir", "amount": dark}] if dark else []),
        "extraLootedResources": [],
        "availableLoot": [
            {"name": "gold", "amount": 300000},
            {"name": "elixir", "amount": 300000},
        ],
    })


def _make_defense_entry(stars=1, destruction=45, ts="20260101T130000.000Z"):
    return BattleLogEntry(data={
        "battleType": "legendLeague",
        "attack": False,
        "timestamp": ts,
        "armyShareCode": "",
        "opponentPlayerTag": "#OPP2",
        "stars": stars,
        "destructionPercentage": destruction,
        "lootedResources": [],
        "extraLootedResources": [],
        "availableLoot": [],
    })


def _make_league_history(season_id=202601, trophies=5200, tier_id=22, placement=150,
                         atk_w=5, atk_l=3, atk_s=14, def_w=4, def_l=4, def_s=8):
    return LeagueHistoryEntry(data={
        "leagueSeasonId": season_id,
        "leagueTrophies": trophies,
        "leagueTierId": tier_id,
        "placement": placement,
        "attackWins": atk_w,
        "attackLosses": atk_l,
        "attackStars": atk_s,
        "defenseWins": def_w,
        "defenseLosses": def_l,
        "defenseStars": def_s,
        "maxBattles": 8,
    })


def _make_tier_group_member(name="Player1", clan="TestClan", trophies=5100,
                            atk_w=6, atk_l=2, def_w=3, def_l=5):
    return LeagueTierGroupMember(data={
        "playerTag": "#P1",
        "playerName": name,
        "clanTag": "#CLAN1",
        "clanName": clan,
        "leagueTrophies": trophies,
        "attackWinCount": atk_w,
        "attackLoseCount": atk_l,
        "defenseWinCount": def_w,
        "defenseLoseCount": def_l,
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBattleWinRate:
    def test_basic(self):
        entries = [_make_attack_entry(stars=3), _make_attack_entry(stars=0), _make_attack_entry(stars=1)]
        assert battlelog_analytics.battle_win_rate(entries) == pytest.approx(66.67, abs=0.1)

    def test_all_wins(self):
        entries = [_make_attack_entry(stars=3), _make_attack_entry(stars=2)]
        assert battlelog_analytics.battle_win_rate(entries) == 100.0

    def test_no_entries(self):
        assert battlelog_analytics.battle_win_rate([]) == 0.0

    def test_only_defenses(self):
        entries = [_make_defense_entry(stars=0)]
        assert battlelog_analytics.battle_win_rate(entries) == 0.0


class TestBattleAttackStats:
    def test_basic(self):
        entries = [_make_attack_entry(stars=3, destruction=100), _make_attack_entry(stars=1, destruction=40)]
        result = battlelog_analytics.battle_attack_stats(entries)
        assert result["total_attacks"] == 2
        assert result["wins"] == 2
        assert result["losses"] == 0
        assert result["avg_stars"] == 2.0
        assert result["total_stars"] == 4
        assert result["star_distribution"][3] == 1
        assert result["star_distribution"][1] == 1

    def test_empty(self):
        result = battlelog_analytics.battle_attack_stats([])
        assert result["total_attacks"] == 0


class TestBattleDefenseStats:
    def test_basic(self):
        entries = [_make_defense_entry(stars=0), _make_defense_entry(stars=3)]
        result = battlelog_analytics.battle_defense_stats(entries)
        assert result["total_defenses"] == 2
        assert result["wins"] == 1
        assert result["losses"] == 1
        assert result["total_stars_received"] == 3

    def test_empty(self):
        result = battlelog_analytics.battle_defense_stats([])
        assert result["total_defenses"] == 0


class TestBattleLootSummary:
    def test_basic(self):
        entries = [_make_attack_entry(gold=100000, elixir=80000), _make_attack_entry(gold=50000, elixir=30000)]
        result = battlelog_analytics.battle_loot_summary(entries)
        assert result["total_gold"] == 150000
        assert result["total_elixir"] == 110000
        assert result["total_looted"] == 260000

    def test_with_dark(self):
        entries = [_make_attack_entry(dark=500)]
        result = battlelog_analytics.battle_loot_summary(entries)
        assert result["total_dark"] == 500

    def test_empty(self):
        result = battlelog_analytics.battle_loot_summary([])
        assert result["total_gold"] == 0


class TestBattleStreak:
    def test_win_streak(self):
        entries = [
            _make_attack_entry(stars=3, ts="20260101T100000.000Z"),
            _make_attack_entry(stars=2, ts="20260101T110000.000Z"),
            _make_attack_entry(stars=1, ts="20260101T120000.000Z"),
        ]
        current, best, streak_type = battlelog_analytics.battle_streak(entries)
        assert current == 3
        assert best == 3
        assert streak_type == "win"

    def test_mixed_streak(self):
        entries = [
            _make_attack_entry(stars=3, ts="20260101T100000.000Z"),
            _make_attack_entry(stars=0, ts="20260101T110000.000Z"),
            _make_attack_entry(stars=3, ts="20260101T120000.000Z"),
        ]
        current, best, streak_type = battlelog_analytics.battle_streak(entries)
        assert current == 1
        assert best == 1
        assert streak_type == "win"

    def test_empty(self):
        current, best, streak_type = battlelog_analytics.battle_streak([])
        assert current == 0


class TestBattleConsistencyScore:
    def test_consistent(self):
        entries = [_make_attack_entry(stars=3) for _ in range(5)]
        score = battlelog_analytics.battle_consistency_score(entries)
        assert score == 100.0

    def test_inconsistent(self):
        entries = [_make_attack_entry(stars=s) for s in [0, 1, 2, 3, 0]]
        score = battlelog_analytics.battle_consistency_score(entries)
        assert score < 80.0

    def test_single_entry(self):
        entries = [_make_attack_entry(stars=3)]
        assert battlelog_analytics.battle_consistency_score(entries) == 100.0


class TestBattleDailySummary:
    def test_basic(self):
        entries = [
            _make_attack_entry(stars=3, ts="20260101T100000.000Z"),
            _make_defense_entry(stars=1, ts="20260101T110000.000Z"),
            _make_attack_entry(stars=0, ts="20260102T100000.000Z"),
        ]
        result = battlelog_analytics.battle_daily_summary(entries, date(2026, 1, 1))
        assert result["attacks"] == 1
        assert result["defenses"] == 1
        assert result["total_battles"] == 2

    def test_no_battles_on_date(self):
        entries = [_make_attack_entry(ts="20260101T100000.000Z")]
        result = battlelog_analytics.battle_daily_summary(entries, date(2026, 6, 1))
        assert result["total_battles"] == 0


class TestBattlePeriodSummary:
    def test_basic(self):
        entries = [
            _make_attack_entry(stars=3, ts="20260101T100000.000Z"),
            _make_attack_entry(stars=0, ts="20260103T100000.000Z"),
        ]
        result = battlelog_analytics.battle_period_summary(entries, date(2026, 1, 1), date(2026, 1, 3))
        assert result["days"] == 3
        assert result["attacks"]["total_attacks"] == 2


class TestLeagueHistoryProgression:
    def test_basic(self):
        history = [
            _make_league_history(season_id=202501, trophies=4800),
            _make_league_history(season_id=202601, trophies=5200),
        ]
        result = battlelog_analytics.league_history_progression(history)
        assert result["total_seasons"] == 2
        assert result["best_trophies"] == 5200
        assert result["worst_trophies"] == 4800

    def test_empty(self):
        result = battlelog_analytics.league_history_progression([])
        assert result["total_seasons"] == 0


class TestLeagueSeasonStats:
    def test_found(self):
        history = [_make_league_history(season_id=202601)]
        result = battlelog_analytics.league_season_stats(history, 202601)
        assert result is not None
        assert result["trophies"] == 5200

    def test_not_found(self):
        history = [_make_league_history(season_id=202601)]
        result = battlelog_analytics.league_season_stats(history, 209999)
        assert result is None


class TestLeagueTierDistribution:
    def test_basic(self):
        history = [
            _make_league_history(tier_id=22),
            _make_league_history(tier_id=22),
            _make_league_history(tier_id=23),
        ]
        dist = battlelog_analytics.league_tier_distribution(history)
        assert dist[22] == 2
        assert dist[23] == 1


class TestTierGroupMemberStats:
    def test_basic(self):
        members = [_make_tier_group_member(name="P1"), _make_tier_group_member(name="P2")]
        group = LeagueTierGroup(data={"members": [], "attackLogs": [], "defenseLogs": []})
        group.members = members
        result = battlelog_analytics.tier_group_member_stats(group)
        assert len(result) == 2
        assert result[0]["player_name"] == "P1"


class TestTierGroupAttackAnalysis:
    def test_basic(self):
        group = LeagueTierGroup(data={"members": [], "attackLogs": [], "defenseLogs": []})
        group.attack_logs = [
            LeagueTierGroupBattleLogEntry(data={"opponentPlayerTag": "#O1", "opponentName": "O1", "stars": 3, "destructionPercentage": 100, "trophies": 30, "creationTime": None}),
            LeagueTierGroupBattleLogEntry(data={"opponentPlayerTag": "#O2", "opponentName": "O2", "stars": 2, "destructionPercentage": 75, "trophies": 15, "creationTime": None}),
        ]
        result = battlelog_analytics.tier_group_attack_analysis(group)
        assert result["total_attacks"] == 2
        assert result["three_stars"] == 1
        assert result["two_stars"] == 1


class TestTierGroupDefenseAnalysis:
    def test_basic(self):
        group = LeagueTierGroup(data={"members": [], "attackLogs": [], "defenseLogs": []})
        group.defense_logs = [
            LeagueTierGroupBattleLogEntry(data={"opponentPlayerTag": "#O1", "opponentName": "O1", "stars": 0, "destructionPercentage": 20, "trophies": 0, "creationTime": None}),
        ]
        result = battlelog_analytics.tier_group_defense_analysis(group)
        assert result["clean_sheets"] == 1


class TestTierGroupMVP:
    def test_basic(self):
        group = LeagueTierGroup(data={"members": [], "attackLogs": [], "defenseLogs": []})
        group.members = [
            _make_tier_group_member(name="P1", trophies=5100, atk_w=6, atk_l=2),
            _make_tier_group_member(name="P2", trophies=4900, atk_w=4, atk_l=4),
        ]
        result = battlelog_analytics.tier_group_mvp(group)
        assert result["player_name"] == "P1"

    def test_empty_group(self):
        group = LeagueTierGroup(data={"members": [], "attackLogs": [], "defenseLogs": []})
        assert battlelog_analytics.tier_group_mvp(group) is None
