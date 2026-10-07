"""New tests for export and reports covering audit fixes."""

from unittest.mock import MagicMock

from geniuslib import battlelog_analytics, formatters, war_analytics


def test_format_clan_detailed_uses_builder_base():
    mock_clan = MagicMock()
    mock_clan.name = "TestClan"
    mock_clan.tag = "#CLAN1"
    mock_clan.level = 10
    mock_clan.member_count = 45
    mock_clan.points = 25000
    mock_clan.builder_base_points = 12000
    result = formatters.format_clan_detailed(mock_clan)
    assert "BB:" in result or "builder" in result.lower() or "12000" in result


def test_format_role_elder():
    from geniuslib.enums import Role
    result = formatters.format_role(Role.elder)
    assert "Ancião" in result


def test_format_trophies_none_safe():
    assert "0" in formatters.format_trophies(None)
    assert "0" in formatters.format_trophies(0)


def test_battle_streak_best_differs_from_current():
    from tests.test_battlelog_analytics import _make_attack_entry
    entries = [
        _make_attack_entry(stars=3, ts="20260101T100000.000Z"),
        _make_attack_entry(stars=3, ts="20260101T110000.000Z"),
        _make_attack_entry(stars=0, ts="20260101T120000.000Z"),
        _make_attack_entry(stars=0, ts="20260101T130000.000Z"),
        _make_attack_entry(stars=0, ts="20260101T140000.000Z"),
    ]
    current, best, streak_type = battlelog_analytics.battle_streak(entries)
    assert best >= current


def test_decode_army_code_handles_bad_parts():
    result = battlelog_analytics.decode_army_code("invalid###", {})
    assert result["troops"] == []
    assert result["spells"] == []
    assert result["heroes"] == []


def test_war_analytics_none_safe():
    mock_attack = MagicMock()
    mock_attack.defender = MagicMock()
    mock_attack.defender.defenses = []
    mock_attack.stars = None
    mock_attack.order = 1
    assert war_analytics.new_stars(mock_attack) == 0


def test_export_to_json_works_with_slots():
    from geniuslib import exporter
    from geniuslib.raid import RaidMember

    rm = RaidMember(
        data={
            "name": "P1",
            "tag": "#P1",
            "attacks": 1,
            "attackLimit": 5,
            "bonusAttackLimit": 0,
            "capitalResourcesLooted": 100,
        },
        client=None,
        raid_log_entry=MagicMock(),
    )
    json_str = exporter.to_json(rm)
    assert isinstance(json_str, str)
    assert len(json_str) > 0
