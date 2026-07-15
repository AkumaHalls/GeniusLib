"""Tests for the raid_analytics module."""

import pytest
from unittest.mock import MagicMock
from geniuslib import raid_analytics


class TestRaidAnalytics:
    def test_total_member_attack_stars(self, mock_raid_member):
        mock_raid_member.attacks = [
            MagicMock(stars=3),
            MagicMock(stars=2),
        ]
        assert raid_analytics.total_member_attack_stars(mock_raid_member) == 5

    def test_total_member_attack_stars_empty(self, mock_raid_member):
        mock_raid_member.attacks = []
        assert raid_analytics.total_member_attack_stars(mock_raid_member) == 0

    def test_total_member_destruction(self, mock_raid_member):
        mock_raid_member.attacks = [
            MagicMock(destruction=80.0),
            MagicMock(destruction=70.0),
        ]
        assert raid_analytics.total_member_destruction(mock_raid_member) == 150.0

    def test_best_raid_attack(self, mock_raid_member):
        a1 = MagicMock(stars=2, destruction=80)
        a2 = MagicMock(stars=3, destruction=100)
        mock_raid_member.attacks = [a1, a2]
        result = raid_analytics.best_raid_attack(mock_raid_member)
        assert result == a2

    def test_best_raid_attack_empty(self, mock_raid_member):
        mock_raid_member.attacks = []
        assert raid_analytics.best_raid_attack(mock_raid_member) is None

    def test_average_attack_destruction(self, mock_raid_member):
        mock_raid_member.attacks = [
            MagicMock(destruction=80.0),
            MagicMock(destruction=100.0),
        ]
        assert raid_analytics.average_attack_destruction(mock_raid_member) == 90.0

    def test_missed_raid_attacks(self, mock_raid_log_entry):
        m1 = MagicMock(attack_limit=5, bonus_attack_limit=0, attack_count=4)
        m2 = MagicMock(attack_limit=5, bonus_attack_limit=0, attack_count=3)
        mock_raid_log_entry.members = [m1, m2]
        assert raid_analytics.count_missed_raid_attacks(mock_raid_log_entry, "#CLAN1") == 3

    def test_inactive_members(self, mock_raid_log_entry):
        active = MagicMock(attack_count=5)
        inactive = MagicMock(attack_count=0)
        mock_raid_log_entry.members = [active, inactive]
        result = raid_analytics.get_inactive_raid_members(mock_raid_log_entry)
        assert len(result) == 1
        assert result[0] == inactive

    def test_member_raid_contribution(self, mock_raid_member):
        mock_raid_member.capital_resources_looted = 25000
        mock_raid_member.raid_log_entry.total_loot = 100000
        assert raid_analytics.member_raid_contribution(mock_raid_member) == 25.0

    def test_district_attack_breakdown(self, mock_raid_district):
        mock_raid_district.attacks = [
            MagicMock(stars=3), MagicMock(stars=3), MagicMock(stars=2),
            MagicMock(stars=1), MagicMock(stars=0),
        ]
        result = raid_analytics.district_attack_breakdown(mock_raid_district)
        assert result["3_stars"] == 2
        assert result["2_stars"] == 1
        assert result["1_star"] == 1
        assert result["0_stars"] == 1

    def test_clan_offensive_stats(self, mock_raid_log_entry):
        rc = MagicMock(looted=50000, attack_count=30, district_count=10, destroyed_district_count=8)
        mock_raid_log_entry.attack_log = [rc]
        result = raid_analytics.clan_offensive_stats(mock_raid_log_entry)
        assert result["total_loot"] == 50000
        assert result["districts_destroyed"] == 8
        assert result["efficiency"] == 80.0

    def test_clan_defensive_stats(self, mock_raid_log_entry):
        rc = MagicMock(looted=20000, attack_count=25, destroyed_district_count=4)
        mock_raid_log_entry.defense_log = [rc]
        result = raid_analytics.clan_defensive_stats(mock_raid_log_entry)
        assert result["total_loot_lost"] == 20000
        assert result["districts_lost"] == 4

    def test_raid_summary(self, mock_raid_log_entry):
        rc = MagicMock(looted=50000, attack_count=30, district_count=10, destroyed_district_count=8)
        mock_raid_log_entry.attack_log = [rc]
        mock_raid_log_entry.defense_log = [MagicMock(looted=20000, attack_count=25, destroyed_district_count=4)]
        m1 = MagicMock(attack_limit=5, bonus_attack_limit=0, attack_count=4, capital_resources_looted=30000)
        m1.name = "Active"
        m2 = MagicMock(attack_limit=5, bonus_attack_limit=0, attack_count=0, capital_resources_looted=0)
        m2.name = "Inactive"
        mock_raid_log_entry.members = [m1, m2]
        mock_raid_log_entry.total_loot = 100000

        result = raid_analytics.raid_summary(mock_raid_log_entry)
        assert result["state"] == "ongoing"
        assert result["missed_attacks"] == 6
        assert len(result["inactive_members"]) == 1
        assert result["top_attacker"] == "Active"
