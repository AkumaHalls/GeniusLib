"""Tests for the formatters module."""

import pytest
from unittest.mock import MagicMock
from geniuslib.enums import Role, WarState, WarResult
from geniuslib import formatters


class TestFormatters:
    def test_town_hall_emoji(self):
        assert formatters.town_hall_emoji(16) is not None
        assert formatters.town_hall_emoji(99) == "❓"

    def test_format_th(self):
        result = formatters.format_th(16)
        assert "TH16" in result

    def test_format_role(self):
        role = MagicMock()
        role.Role = Role.leader
        result = formatters.format_role(Role.leader)
        assert "Líder" in result

        result2 = formatters.format_role(Role.member)
        assert "Membro" in result2

    def test_format_league(self):
        league = MagicMock()
        league.name = "Champion League I"
        result = formatters.format_league(league)
        assert "Champion League I" in result

        result2 = formatters.format_league(None)
        assert "Sem Liga" in result2

    def test_format_trophies(self):
        result = formatters.format_trophies(5000)
        assert "5.000" in result

    def test_format_player_brief(self, mock_player):
        result = formatters.format_player_brief(mock_player)
        assert mock_player.name in result
        assert "TH16" in result
        assert mock_player.tag in result

    def test_format_member_brief(self, mock_clan_member):
        result = formatters.format_member_brief(mock_clan_member)
        assert mock_clan_member.name in result
        assert "TH16" in result

    def test_format_clan_brief(self, mock_clan):
        result = formatters.format_clan_brief(mock_clan)
        assert mock_clan.name in result
        assert "Nível 10" in result

    def test_format_clan_detailed(self, mock_clan):
        result = formatters.format_clan_detailed(mock_clan)
        assert mock_clan.name in result
        assert "Nível" in result

    def test_format_war_state(self):
        result = formatters.format_war_state(WarState.in_war)
        assert "Em guerra" in result
        result2 = formatters.format_war_state(WarState.not_in_war)
        assert "Fora de guerra" in result2

    def test_format_war_result_win(self, mock_clan_war):
        mock_clan_war.state = "warEnded"
        mock_clan_war.clan.stars = 45
        mock_clan_war.opponent.stars = 30
        result = formatters.format_war_result(mock_clan_war, "#CLAN1")
        assert "Vitória" in result

    def test_format_war_result_lose(self, mock_clan_war):
        mock_clan_war.state = "warEnded"
        mock_clan_war.clan.stars = 30
        mock_clan_war.opponent.stars = 45
        result = formatters.format_war_result(mock_clan_war, "#CLAN1")
        assert "Derrota" in result

    def test_format_war_score(self, mock_clan_war):
        mock_clan_war.clan.stars = 45
        mock_clan_war.opponent.stars = 30
        result = formatters.format_war_score(mock_clan_war, "#CLAN1")
        assert "45" in result
        assert "30" in result

    def test_format_attack(self):
        result = formatters.format_attack(2, 85.3)
        assert "85.3%" in result

    def test_format_percentage(self):
        assert formatters.format_percentage(85.3) == "85.3%"

    def test_format_number(self):
        assert formatters.format_number(15000) == "15.000"

    def test_format_raid_brief(self, mock_raid_log_entry):
        rc = MagicMock(looted=50000)
        mock_raid_log_entry.attack_log = [rc]
        mock_raid_log_entry.defense_log = [MagicMock(looted=20000)]
        mock_raid_log_entry.completed_raid_count = 6
        result = formatters.format_raid_brief(mock_raid_log_entry)
        assert "50.000" in result or "50000" in result

    def test_format_builder_base_league(self):
        league = MagicMock()
        league.name = "Wood League"
        result = formatters.format_builder_base_league(league)
        assert "Wood League" in result

        result2 = formatters.format_builder_base_league(None)
        assert "Sem Liga" in result2
