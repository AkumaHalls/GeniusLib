"""Tests for the war_analytics module."""

import pytest
from unittest.mock import MagicMock
from geniuslib import war_analytics


class TestNewStars:
    def test_no_prior_defense(self, mock_war_attack):
        mock_war_attack.defender.defenses = []
        assert war_analytics.new_stars(mock_war_attack) == 3

    def test_better_than_prior(self, mock_war_attack):
        prior = MagicMock(stars=2, order=0)
        mock_war_attack.defender.defenses = [prior]
        mock_war_attack.order = 1
        assert war_analytics.new_stars(mock_war_attack) == 1

    def test_worse_than_prior(self, mock_war_attack):
        prior = MagicMock(stars=3, order=0)
        mock_war_attack.defender.defenses = [prior]
        mock_war_attack.stars = 2
        mock_war_attack.order = 1
        assert war_analytics.new_stars(mock_war_attack) == 0


class TestBestAttack:
    def test_best_attack_on(self, mock_clan_war_member):
        a1 = MagicMock(stars=2, destruction=80)
        a2 = MagicMock(stars=3, destruction=100)
        mock_clan_war_member.attacks = [a1, a2]
        result = war_analytics.best_attack_on(mock_clan_war_member)
        assert result == a2

    def test_best_attack_no_attacks(self, mock_clan_war_member):
        mock_clan_war_member.attacks = []
        assert war_analytics.best_attack_on(mock_clan_war_member) is None


class TestBestDefense:
    def test_best_defense_on(self, mock_clan_war_member):
        d1 = MagicMock(stars=3, destruction=100)
        d2 = MagicMock(stars=2, destruction=80)
        mock_clan_war_member.defenses = [d1, d2]
        result = war_analytics.best_defense_on(mock_clan_war_member)
        assert result == d1

    def test_no_defenses(self, mock_clan_war_member):
        mock_clan_war_member.defenses = []
        assert war_analytics.best_defense_on(mock_clan_war_member) is None


class TestTotalStats:
    def test_total_stars(self, mock_clan_war_member):
        mock_clan_war_member.attacks = [
            MagicMock(stars=3),
            MagicMock(stars=2),
        ]
        assert war_analytics.total_attack_stars(mock_clan_war_member) == 5

    def test_total_destruction(self, mock_clan_war_member):
        mock_clan_war_member.attacks = [
            MagicMock(destruction=80.0),
            MagicMock(destruction=70.0),
        ]
        assert war_analytics.total_attack_destruction(mock_clan_war_member) == 150.0


class TestWarResult:
    def test_win(self, mock_clan_war):
        mock_clan_war.clan.stars = 45
        mock_clan_war.opponent.stars = 30
        assert war_analytics.get_war_result(mock_clan_war, "#CLAN1") == "win"

    def test_lose(self, mock_clan_war):
        mock_clan_war.clan.stars = 30
        mock_clan_war.opponent.stars = 45
        assert war_analytics.get_war_result(mock_clan_war, "#CLAN1") == "lose"

    def test_tie(self, mock_clan_war):
        mock_clan_war.clan.stars = 30
        mock_clan_war.opponent.stars = 30
        mock_clan_war.clan.destruction = 90.0
        mock_clan_war.opponent.destruction = 90.0
        assert war_analytics.get_war_result(mock_clan_war, "#CLAN1") == "tie"

    def test_ongoing(self, mock_clan_war):
        mock_clan_war.state = "inWar"
        assert war_analytics.get_war_result(mock_clan_war, "#CLAN1") == "ongoing"

    def test_missed_attacks(self, mock_clan_war):
        mock_clan_war.attacks_per_member = 2
        mock_clan_war.clan.members = [MagicMock(), MagicMock(), MagicMock()]
        mock_clan_war.clan.attacks = [MagicMock(), MagicMock(), MagicMock()]
        assert war_analytics.count_missed_attacks(mock_clan_war, "#CLAN1") == 3

    def test_attack_order(self, mock_clan_war_member):
        mock_clan_war_member.attacks = [
            MagicMock(defender_tag="#DEF1", order=1),
            MagicMock(defender_tag="#DEF2", order=2),
            MagicMock(defender_tag="#DEF1", order=3),
        ]
        assert war_analytics.get_attack_order(mock_clan_war_member, "#DEF1") == 2
        assert war_analytics.get_attack_order(mock_clan_war_member, "#NONE") == 0

    def test_previous_best_attack(self, mock_clan_war_member):
        mock_clan_war_member.attacks = [
            MagicMock(defender_tag="#DEF1", stars=2, destruction=80),
            MagicMock(defender_tag="#DEF1", stars=3, destruction=100),
        ]
        result = war_analytics.previous_best_attack(mock_clan_war_member, "#DEF1")
        assert result.stars == 3

        result2 = war_analytics.previous_best_attack(mock_clan_war_member, "#NONE")
        assert result2 is None
