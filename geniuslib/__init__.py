# GeniusLib - Clash of Clans API wrapper
# Based on coc.py v4.0.0 (MIT License, copyright (c) 2019-2020 mathsman5133)
# (c) 2026 AkumaHalls / ClashGenius

__version__ = "5.0.1"

from .abc import BasePlayer, BaseClan
from .buildings import (
    Building,
    GearUp,
    MergeRequirement,
    SeasonalDefenseModule,
    SeasonalDefense,
    Supercharge,
    TownhallUnlock,
    TownhallWeapon,
    Trap,
)
from .characters import Guardian, Helper
from .clans import RankedClan, Clan
from .client import Client
from .constants import *
from .cosmetics import Skin, Scenery, Obstacle, Decoration, ClanCapitalHousePart
from .events import PlayerEvents, ClanEvents, WarEvents, EventsClient, ClientEvents
from .enums import (
    PlayerHouseElementType,
    Resource,
    Role,
    WarRound,
    WarState,
    BattleModifier,
    WarResult,
    ProductionBuildingType,
    BuildingType,
    VillageType,
    SceneryType,
    EquipmentRarity,
    SkinTier
)
from .errors import (
    ClashOfClansException,
    HTTPException,
    NotFound,
    InvalidArgument,
    InvalidCredentials,
    LoginError,
    Forbidden,
    Maintenance,
    GatewayError,
    PrivateWarLog,
)
from .game_data import AccountData, Upgrade, Boosts, ArmyRecipe, HeroLoadout, StaticData
from .hero import Equipment, Hero, Pet
from .http import BasicThrottler, BatchThrottler, HTTPClient
from .iterators import (
    ClanIterator,
    ClanWarIterator,
    PlayerIterator,
    LeagueWarIterator,
    CurrentWarIterator,
    SeasonIterator,
)
from .miscmodels import (
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
    Timestamp,
    TimeDelta,
    TID,
    Translation
)
from .players import Player, ClanMember, RankedPlayer
from .player_clan import PlayerClan
from .raid import RaidClan, RaidMember, RaidLogEntry, RaidDistrict, RaidAttack
from .spell import Spell
from .troop import Troop
from .war_clans import WarClan, ClanWarLeagueClan
from .war_attack import WarAttack
from .war_members import ClanWarLeagueClanMember, ClanWarMember
from .wars import ClanWar, ClanWarLogEntry, ClanWarLeagueGroup, ExtendedCWLGroup
from .war_analytics import (
    new_stars,
    previous_best_attack,
    best_attack_on,
    best_defense_on,
    total_attack_stars,
    total_attack_destruction,
    get_cleanup_attacks,
    count_missed_attacks,
    get_attack_order,
    get_war_result,
)
from .raid_analytics import (
    total_member_attack_stars,
    total_member_destruction,
    best_raid_attack,
    average_attack_destruction,
    count_missed_raid_attacks,
    get_inactive_raid_members,
    member_raid_contribution,
    district_attack_breakdown,
    get_raid_cleanup_attacks,
    get_wasted_attacks,
    clan_offensive_stats,
    clan_defensive_stats,
    raid_summary,
)
from .formatters import (
    town_hall_emoji,
    format_th,
    format_role,
    format_league,
    format_builder_base_league,
    format_trophies,
    format_player_brief,
    format_member_brief,
    format_clan_brief,
    format_clan_detailed,
    format_war_state,
    format_war_result,
    format_war_score,
    format_attack,
    format_percentage,
    format_number,
    format_raid_brief,
)
from .middleware import (
    Middleware,
    RequestMiddleware,
    ResponseMiddleware,
    request_logger,
    response_logger,
    timing_header,
    middleware,
)
from .upgrade_tracker import (
    UpgradeCost,
    UpgradeSummary,
    estimate_upgrade_cost,
    estimate_upgrade_time,
    get_th_upgrade_summary,
    format_upgrade_summary,
)
from .exporter import to_json, to_csv, to_dict, export_players, export_clans
from .comparer import compare_players, compare_clans
from . import utils
