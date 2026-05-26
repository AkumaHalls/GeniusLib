# GeniusLib - Clash of Clans API wrapper
# Based on coc.py v4.0.0 (MIT License, copyright (c) 2019-2020 mathsman5133)
# (c) 2026 AkumaHalls / ClashGenius

__version__ = "4.0.0"

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
from . import utils
