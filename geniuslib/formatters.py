# GeniusLib - Clash of Clans API wrapper
# (c) 2026 AkumaHalls / ClashGenius

from datetime import datetime
from enum import Enum
from typing import Optional

from .enums import Role, WarState, WarResult
from .players import Player, ClanMember
from .clans import Clan
from .wars import ClanWar
from .miscmodels import League, BaseLeague
from .raid import RaidLogEntry
from . import utils


TH_EMOJIS = {
    1: "\u0031\uFE0F\u20E3", 2: "\u0032\uFE0F\u20E3", 3: "\u0033\uFE0F\u20E3",
    4: "\u0034\uFE0F\u20E3", 5: "\u0035\uFE0F\u20E3", 6: "\u0036\uFE0F\u20E3",
    7: "\u0037\uFE0F\u20E3", 8: "\u0038\uFE0F\u20E3", 9: "\u0039\uFE0F\u20E3",
    10: "\U0001F51F", 11: "\U0001F4AF", 12: "\U0001F51C", 13: "\U0001F525",
    14: "\U0001F308", 15: "\U0001F31F", 16: "\U0001F451", 17: "\U0001F480",
}


def town_hall_emoji(level: int) -> str:
    return TH_EMOJIS.get(level, "\u2753")


def format_th(level: int) -> str:
    return f"{town_hall_emoji(level)} TH{level}"


def format_role(role: Role) -> str:
    role_str = role.value if isinstance(role, Enum) else str(role)
    lookup = {
        "leader": "\U0001F451 L\u00edder",
        "coLeader": "\U0001F4A0 Col\u00edder",
        "elder": "\U0001F4A1 Anci\u00e3o",
        "member": "\U0001F4CB Membro",
    }
    return lookup.get(role_str, str(role))


def format_league(league: Optional[League]) -> str:
    if league is None:
        return "Sem Liga"
    return f"{league.name}"


def format_builder_base_league(league: Optional[BaseLeague]) -> str:
    if league is None:
        return "Sem Liga"
    return league.name


def format_trophies(trophies: int) -> str:
    return f"\U0001F3C6 {trophies:,}".replace(",", ".")


def format_player_brief(player: Player) -> str:
    return (
        f"{player.name} ({player.tag})"
        f" | {format_th(player.town_hall)}"
        f" | {format_trophies(player.trophies)}"
    )


def format_member_brief(member: ClanMember) -> str:
    role_str = format_role(member.role) if member.role else ""
    return (
        f"{role_str} {member.name}"
        f" | {format_th(member.town_hall)}"
        f" | {format_trophies(member.trophies)}"
    )


def format_clan_brief(clan: Clan) -> str:
    return (
        f"{clan.name} ({clan.tag})"
        f" | N\u00edvel {clan.level}"
        f" | {clan.member_count}/50"
    )


def format_clan_detailed(clan: Clan) -> str:
    return (
        f"{clan.name} ({clan.tag})\n"
        f"N\u00edvel: {clan.level} | Membros: {clan.member_count}/50\n"
        f"Trof\u00e9us: {format_trophies(clan.points)}"
        f" | VS: {format_trophies(clan.versus_points)}"
    )


def format_war_state(state: WarState) -> str:
    state_str = state.value if isinstance(state, Enum) else str(state)
    lookup = {
        "notInWar": "\u274C Fora de guerra",
        "preparation": "\u23F3 Preparação",
        "inWar": "\u2694\uFE0F Em guerra",
        "warEnded": "\U0001F3C6 Guerra encerrada",
    }
    return lookup.get(state_str, str(state))


def format_war_result(war: ClanWar, clan_tag: str) -> str:
    tag = utils.correct_tag(clan_tag)
    clan = war.clan if war.clan.tag == tag else war.opponent
    other = war.opponent if war.clan.tag == tag else war.clan

    if war.state != "warEnded":
        return format_war_state(war.state)

    if clan.stars > other.stars:
        return "\u2705 Vit\u00f3ria"
    if clan.stars == other.stars:
        if clan.destruction > other.destruction:
            return "\u2705 Vit\u00f3ria (desempate)"
        if clan.destruction == other.destruction:
            return "\U0001F3C8 Empate"
    return "\u274C Derrota"


def format_war_score(war: ClanWar, clan_tag: str) -> str:
    tag = utils.correct_tag(clan_tag)
    clan = war.clan if war.clan.tag == tag else war.opponent
    other = war.opponent if war.clan.tag == tag else war.clan
    return f"{clan.stars} \u2B50 {other.stars}"


def format_attack(stars: int, destruction: float) -> str:
    stars_str = "\u2B50" * stars + "\u2606" * (3 - stars)
    return f"{stars_str} {destruction:.1f}%"


def format_percentage(value: float) -> str:
    return f"{value:.1f}%"


def format_number(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def format_raid_brief(raid: RaidLogEntry) -> str:
    off_loot = sum(rc.looted for rc in raid.attack_log)
    def_loot = sum(rc.looted for rc in raid.defense_log)
    return (
        f"\U0001F3F0\uFE0F Raid: {format_number(off_loot)} saqueado"
        f" | {format_number(def_loot)} perdido"
        f" | {raid.completed_raid_count} ataques"
    )
