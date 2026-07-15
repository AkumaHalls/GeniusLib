"""Shared fixtures for GeniusLib tests."""

from unittest.mock import MagicMock, AsyncMock, PropertyMock
import pytest


@pytest.fixture
def mock_war_attack():
    attack = MagicMock()
    attack.stars = 3
    attack.destruction = 100.0
    attack.order = 1
    attack.attacker_tag = "#ABC123"
    attack.defender_tag = "#DEF456"
    attack.attacker = MagicMock(name="AttackerName")
    attack.defender = MagicMock(name="DefenderName")
    return attack


@pytest.fixture
def mock_clan_war_member():
    member = MagicMock()
    member.tag = "#ABC123"
    member.name = "TestPlayer"
    member.town_hall = 16
    member.trophies = 5000
    member.role = "leader"
    member.attacks = []
    member.defenses = []
    return member


@pytest.fixture
def mock_clan_war():
    war = MagicMock()
    war.state = "warEnded"
    war.clan = MagicMock()
    war.clan.tag = "#CLAN1"
    war.clan.name = "TestClan"
    war.clan.stars = 45
    war.clan.destruction = 90.0
    war.clan.attacks = []
    war.clan.members = []
    war.opponent = MagicMock()
    war.opponent.tag = "#CLAN2"
    war.opponent.name = "OpponentClan"
    war.opponent.stars = 30
    war.opponent.destruction = 75.0
    war.attacks_per_member = 2
    return war


@pytest.fixture
def mock_raid_attack():
    attack = MagicMock()
    attack.stars = 3
    attack.destruction = 100.0
    attack.attacker_tag = "#ABC123"
    return attack


@pytest.fixture
def mock_raid_district():
    district = MagicMock()
    district.name = "Capital Peak"
    district.destruction = 100
    district.attacks = []
    return district


@pytest.fixture
def mock_raid_member():
    member = MagicMock()
    member.tag = "#ABC123"
    member.name = "TestPlayer"
    member.attack_count = 5
    member.attack_limit = 5
    member.bonus_attack_limit = 0
    member.capital_resources_looted = 25000
    member.attacks = []
    return member


@pytest.fixture
def mock_raid_log_entry():
    entry = MagicMock()
    entry.state = "ongoing"
    entry.clan_tag = "#CLAN1"
    entry.start_time = MagicMock()
    entry.end_time = MagicMock()
    entry.total_loot = 100000
    entry.members = []
    entry.attack_log = []
    entry.defense_log = []
    return entry


@pytest.fixture
def mock_player():
    player = MagicMock()
    player.tag = "#ABC123"
    player.name = "TestPlayer"
    player.town_hall = 16
    player.trophies = 5000
    player.versus_trophies = 3000
    return player


@pytest.fixture
def mock_clan_member():
    member = MagicMock()
    member.tag = "#ABC123"
    member.name = "TestMember"
    member.town_hall = 16
    member.trophies = 5000
    member.role = "elder"
    return member


@pytest.fixture
def mock_clan():
    clan = MagicMock()
    clan.tag = "#CLAN1"
    clan.name = "TestClan"
    clan.level = 10
    clan.member_count = 45
    clan.points = 25000
    clan.versus_points = 12000
    clan.members = []
    return clan
