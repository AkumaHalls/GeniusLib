# GeniusLib - Clash of Clans API wrapper
# Based on coc.py v4.0.0 (MIT License, copyright (c) 2019-2020 mathsman5133)
# (c) 2026 AkumaHalls / ClashGenius

__version__ = "5.6.0"

__all__ = [
    'AccountData', 'Achievement', 'ACHIEVEMENT_ORDER', 'ArmyRecipe',
    'ASSETS_PREFIX', 'average_attack_destruction', 'Badge', 'BaseClan',
    'BaseLeague', 'BasePlayer', 'BasicThrottler', 'BatchThrottler',
    'battle_attack_stats', 'battle_consistency_score', 'battle_daily_summary', 'battle_defense_stats',
    'battle_loot_summary', 'battle_period_summary', 'battle_streak', 'battle_win_rate',
    'BattleLogEntry', 'BattleLogResource', 'BattleModifier', 'best_attack_on',
    'best_defense_on', 'best_raid_attack', 'Boosts', 'BUILDER_BASE_HERO_ORDER',
    'BUILDER_TROOPS_ORDER', 'Building', 'BuildingType', 'CapitalDistrict',
    'ChatLanguage', 'Clan', 'clan_defensive_stats', 'clan_offensive_stats',
    'ClanCapitalHousePart', 'ClanEvents', 'ClanIterator', 'ClanMember',
    'ClanWar', 'ClanWarIterator', 'ClanWarLeagueClan', 'ClanWarLeagueClanMember',
    'ClanWarLeagueGroup', 'ClanWarLogEntry', 'ClanWarMember', 'ClashOfClansException',
    'Client', 'ClientEvents', 'compare_clans', 'compare_players',
    'count_missed_attacks', 'count_missed_raid_attacks', 'CurrentWarIterator', 'DARK_ELIXIR_SPELL_ORDER',
    'DARK_ELIXIR_TROOP_ORDER', 'decode_army_code', 'Decoration', 'district_attack_breakdown',
    'ELIXIR_SPELL_ORDER', 'ELIXIR_TROOP_ORDER', 'EQUIPMENT', 'Equipment',
    'EquipmentRarity', 'estimate_upgrade_cost', 'estimate_upgrade_time', 'EventsClient',
    'export_clans', 'export_players', 'ExtendedCWLGroup', 'Forbidden',
    'format_attack', 'format_builder_base_league', 'format_clan_brief', 'format_clan_detailed',
    'format_league', 'format_member_brief', 'format_number', 'format_percentage',
    'format_player_brief', 'format_raid_brief', 'format_role', 'format_th',
    'format_trophies', 'format_upgrade_summary', 'format_war_result', 'format_war_score',
    'format_war_state', 'GatewayError', 'GearUp', 'get_assets_dir',
    'get_attack_order', 'get_cleanup_attacks', 'get_inactive_raid_members', 'get_raid_cleanup_attacks',
    'get_th_upgrade_summary', 'get_war_result', 'get_wasted_attacks', 'GoldPassSeason',
    'Guardian', 'Helper', 'Hero', 'HERO_ORDER',
    'HeroLoadout', 'HOME_BASE_HERO_ORDER', 'HOME_TROOP_ORDER', 'HTTPClient',
    'HTTPException', 'HV_BUILDINGS', 'HV_TROOP_ORDER', 'Icon',
    'InvalidArgument', 'InvalidCredentials', 'Label', 'League',
    'league_history_progression', 'league_season_stats', 'league_tier_distribution', 'LeagueGroupClan',
    'LeagueGroupInfo', 'LeagueHistoryEntry', 'LeagueTierGroup', 'LeagueTierGroupBattleLogEntry',
    'LeagueTierGroupMember', 'LeagueWarIterator', 'LegendStatistics', 'LoadGameData',
    'Location', 'LoginError', 'Maintenance', 'member_raid_contribution',
    'MergeRequirement', 'Middleware', 'middleware', 'new_stars',
    'NotFound', 'Obstacle', 'Pet', 'PETS_ORDER',
    'Player', 'PlayerClan', 'PlayerEvents', 'PlayerHouseElement',
    'PlayerHouseElementType', 'PlayerIterator', 'previous_best_attack', 'PrivateWarLog',
    'ProductionBuildingType', 'raid_summary', 'RaidAttack', 'RaidClan',
    'RaidDistrict', 'RaidLogEntry', 'RaidMember', 'RankedClan',
    'RankedPlayer', 'request_logger', 'RequestMiddleware', 'Resource',
    'response_logger', 'ResponseMiddleware', 'Role', 'Scenery',
    'SceneryType', 'Season', 'SEASONAL_SPELL_ORDER', 'SEASONAL_TROOP_ORDER',
    'SeasonalDefense', 'SeasonalDefenseModule', 'SeasonIterator', 'SIEGE_MACHINE_ORDER',
    'Skin', 'SkinTier', 'Spell', 'SPELL_ORDER',
    'StaticData', 'SUPER_TROOP_ORDER', 'Supercharge', 'TID',
    'tier_group_attack_analysis', 'tier_group_defense_analysis', 'tier_group_member_stats', 'tier_group_mvp',
    'TimeDelta', 'Timestamp', 'timing_header', 'to_csv',
    'to_dict', 'to_json', 'total_attack_destruction', 'total_attack_stars',
    'total_member_attack_stars', 'total_member_destruction', 'town_hall_emoji', 'TownhallUnlock',
    'TownhallWeapon', 'Translation', 'Trap', 'Troop',
    'Upgrade', 'UpgradeCost', 'UpgradeSummary', 'utils',
    '__version__', 'VillageType', 'WarAttack', 'WarClan',
    'WarEvents', 'WarResult', 'WarRound', 'WarState',
]

from . import utils
from .abc import BaseClan, BasePlayer
from .battlelog import (
    BattleLogEntry,
    BattleLogResource,
    LeagueHistoryEntry,
    LeagueTierGroup,
    LeagueTierGroupBattleLogEntry,
    LeagueTierGroupMember,
)
from .battlelog_analytics import (
    battle_attack_stats,
    battle_consistency_score,
    battle_daily_summary,
    battle_defense_stats,
    battle_loot_summary,
    battle_period_summary,
    battle_streak,
    battle_win_rate,
    decode_army_code,
    league_history_progression,
    league_season_stats,
    league_tier_distribution,
    tier_group_attack_analysis,
    tier_group_defense_analysis,
    tier_group_member_stats,
    tier_group_mvp,
)
from .buildings import (
    Building,
    GearUp,
    MergeRequirement,
    SeasonalDefense,
    SeasonalDefenseModule,
    Supercharge,
    TownhallUnlock,
    TownhallWeapon,
    Trap,
)
from .characters import Guardian, Helper
from .clans import Clan, RankedClan
from .client import Client
from .comparer import compare_clans, compare_players
from .constants import (
    ACHIEVEMENT_ORDER,
    BUILDER_BASE_HERO_ORDER,
    BUILDER_TROOPS_ORDER,
    DARK_ELIXIR_SPELL_ORDER,
    DARK_ELIXIR_TROOP_ORDER,
    ELIXIR_SPELL_ORDER,
    ELIXIR_TROOP_ORDER,
    EQUIPMENT,
    HERO_ORDER,
    HOME_BASE_HERO_ORDER,
    HOME_TROOP_ORDER,
    HV_BUILDINGS,
    HV_TROOP_ORDER,
    PETS_ORDER,
    SEASONAL_SPELL_ORDER,
    SEASONAL_TROOP_ORDER,
    SIEGE_MACHINE_ORDER,
    SPELL_ORDER,
    SUPER_TROOP_ORDER,
)
from .cosmetics import ClanCapitalHousePart, Decoration, Obstacle, Scenery, Skin
from .enums import (
    BattleModifier,
    BuildingType,
    EquipmentRarity,
    PlayerHouseElementType,
    ProductionBuildingType,
    Resource,
    Role,
    SceneryType,
    SkinTier,
    VillageType,
    WarResult,
    WarRound,
    WarState,
)
from .errors import (
    ClashOfClansException,
    Forbidden,
    GatewayError,
    HTTPException,
    InvalidArgument,
    InvalidCredentials,
    LoginError,
    Maintenance,
    NotFound,
    PrivateWarLog,
)
from .events import ClanEvents, ClientEvents, EventsClient, PlayerEvents, WarEvents
from .exporter import export_clans, export_players, to_csv, to_dict, to_json
from .formatters import (
    format_attack,
    format_builder_base_league,
    format_clan_brief,
    format_clan_detailed,
    format_league,
    format_member_brief,
    format_number,
    format_percentage,
    format_player_brief,
    format_raid_brief,
    format_role,
    format_th,
    format_trophies,
    format_war_result,
    format_war_score,
    format_war_state,
    town_hall_emoji,
)
from .game_data import AccountData, ArmyRecipe, Boosts, HeroLoadout, StaticData, Upgrade
from .hero import Equipment, Hero, Pet
from .http import BasicThrottler, BatchThrottler, HTTPClient
from .iterators import (
    ClanIterator,
    ClanWarIterator,
    CurrentWarIterator,
    LeagueWarIterator,
    PlayerIterator,
    SeasonIterator,
)
from .middleware import (
    Middleware,
    RequestMiddleware,
    ResponseMiddleware,
    middleware,
    request_logger,
    response_logger,
    timing_header,
)
from .miscmodels import (
    TID,
    Achievement,
    Badge,
    BaseLeague,
    CapitalDistrict,
    ChatLanguage,
    GoldPassSeason,
    Icon,
    Label,
    League,
    LeagueGroupClan,
    LeagueGroupInfo,
    LegendStatistics,
    LoadGameData,
    Location,
    PlayerHouseElement,
    Season,
    TimeDelta,
    Timestamp,
    Translation,
)
from .player_clan import PlayerClan
from .players import ClanMember, Player, RankedPlayer
from .raid import RaidAttack, RaidClan, RaidDistrict, RaidLogEntry, RaidMember
from .raid_analytics import (
    average_attack_destruction,
    best_raid_attack,
    clan_defensive_stats,
    clan_offensive_stats,
    count_missed_raid_attacks,
    district_attack_breakdown,
    get_inactive_raid_members,
    get_raid_cleanup_attacks,
    get_wasted_attacks,
    member_raid_contribution,
    raid_summary,
    total_member_attack_stars,
    total_member_destruction,
)
from .spell import Spell
from .troop import Troop
from .upgrade_tracker import (
    UpgradeCost,
    UpgradeSummary,
    estimate_upgrade_cost,
    estimate_upgrade_time,
    format_upgrade_summary,
    get_th_upgrade_summary,
)
from .utils import ASSETS_PREFIX, get_assets_dir
from .war_analytics import (
    best_attack_on,
    best_defense_on,
    count_missed_attacks,
    get_attack_order,
    get_cleanup_attacks,
    get_war_result,
    new_stars,
    previous_best_attack,
    total_attack_destruction,
    total_attack_stars,
)
from .war_attack import WarAttack
from .war_clans import ClanWarLeagueClan, WarClan
from .war_members import ClanWarLeagueClanMember, ClanWarMember
from .wars import ClanWar, ClanWarLeagueGroup, ClanWarLogEntry, ExtendedCWLGroup
