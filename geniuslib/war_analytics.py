# GeniusLib - Clash of Clans API wrapper
# (c) 2026 AkumaHalls / ClashGenius
from typing import List, Optional

from .wars import ClanWar
from .war_attack import WarAttack
from .war_members import ClanWarMember


def new_stars(attack: WarAttack) -> int:
    """Calculate the new stars gained from this attack beyond the defender's best defense.

    For example, if the defender already had a 2-star defense (60%),
    and this attack scores 3 stars (100%), then ``new_stars`` is 1.

    Parameters
    ----------
    attack: :class:`WarAttack`
        The attack to evaluate.

    Returns
    -------
    :class:`int`
        The number of new stars gained (0-3).
    """
    defender = attack.defender
    if not defender.defenses:
        return attack.stars

    previous_best = max(d.stars for d in defender.defenses if d.order != attack.order)
    return max(0, attack.stars - previous_best)


def previous_best_attack(member: ClanWarMember, target_tag: str) -> Optional[WarAttack]:
    """Find the best previous attack on a defender by a given attacker.

    Parameters
    ----------
    member: :class:`ClanWarMember`
        The attacker whose attacks to search.
    target_tag: :class:`str`
        The defender's tag.

    Returns
    -------
    Optional[:class:`WarAttack`]
        The best previous attack, or ``None`` if no prior attack exists.
    """
    prior = [a for a in member.attacks if a.defender_tag == target_tag]
    if not prior:
        return None
    return max(prior, key=lambda a: (a.stars, a.destruction))


def best_attack_on(member: ClanWarMember) -> Optional[WarAttack]:
    """Get the best attack performed by a member in this war.

    Parameters
    ----------
    member: :class:`ClanWarMember`
        The clan war member.

    Returns
    -------
    Optional[:class:`WarAttack`]
        The attack with the highest stars (then destruction), or ``None``.
    """
    if not member.attacks:
        return None
    return max(member.attacks, key=lambda a: (a.stars, a.destruction))


def best_defense_on(member: ClanWarMember) -> Optional[WarAttack]:
    """Get the best (highest stars) defense against this member.

    Parameters
    ----------
    member: :class:`ClanWarMember`
        The defender.

    Returns
    -------
    Optional[:class:`WarAttack`]
        The attack with the highest stars on this defender, or ``None``.
    """
    if not member.defenses:
        return None
    return max(member.defenses, key=lambda a: (a.stars, a.destruction))


def total_attack_stars(member: ClanWarMember) -> int:
    """Sum of stars from all attacks by this member.

    Parameters
    ----------
    member: :class:`ClanWarMember`
        The clan war member.

    Returns
    -------
    :class:`int`
        Total stars.
    """
    return sum(a.stars for a in member.attacks)


def total_attack_destruction(member: ClanWarMember) -> float:
    """Sum of destruction from all attacks by this member.

    Parameters
    ----------
    member: :class:`ClanWarMember`
        The clan war member.

    Returns
    -------
    :class:`float`
        Total destruction percentage.
    """
    return sum(a.destruction for a in member.attacks)


def get_cleanup_attacks(war: ClanWar, clan_tag: str) -> List[WarAttack]:
    """Get attacks that did not gain new stars (cleanup attacks).

    Parameters
    ----------
    war: :class:`ClanWar`
        The war.
    clan_tag: :class:`str`
        Tag of the clan to analyze.

    Returns
    -------
    List[:class:`WarAttack`]
        List of attacks that scored 0 new stars.
    """
    clan = war.clan if war.clan.tag == clan_tag else war.opponent
    return [a for m in clan.members for a in m.attacks if new_stars(a) == 0]


def count_missed_attacks(war: ClanWar, clan_tag: str) -> int:
    """Count the number of missed attacks (members who didn't use all their attacks).

    Parameters
    ----------
    war: :class:`ClanWar`
        The war.
    clan_tag: :class:`str`
        Tag of the clan to analyze.

    Returns
    -------
    :class:`int`
        Number of unused attacks.
    """
    clan = war.clan if war.clan.tag == clan_tag else war.opponent
    total = war.attacks_per_member * len(clan.members)
    used = len(clan.attacks)
    return total - used


def get_attack_order(member: ClanWarMember, defender_tag: str) -> int:
    """Get the order index (1-based) of an attack on a defender.

    For a fresh attack this returns 1, for a second attack it returns 2, etc.

    Parameters
    ----------
    member: :class:`ClanWarMember`
        The attacker.
    defender_tag: :class:`str`
        The defender's tag.

    Returns
    -------
    :class:`int`
        Attack number (1-based). Returns 0 if no attack on this defender.
    """
    attacks = sorted(
        [a for a in member.attacks if a.defender_tag == defender_tag],
        key=lambda a: a.order
    )
    return len(attacks)


def get_war_result(war: ClanWar, clan_tag: str) -> str:
    """Return a human-readable war result for the given clan.

    Parameters
    ----------
    war: :class:`ClanWar`
        The war.
    clan_tag: :class:`str`
        The clan's tag.

    Returns
    -------
    :class:`str`
        ``"win"``, ``"lose"``, ``"tie"``, or ``"ongoing"``.
    """
    if war.state not in ("warEnded",):
        return "ongoing"

    clan = war.clan if war.clan.tag == clan_tag else war.opponent
    other = war.opponent if war.clan.tag == clan_tag else war.clan

    if clan.stars > other.stars:
        return "win"
    if clan.stars == other.stars:
        if clan.destruction > other.destruction:
            return "win"
        if clan.destruction == other.destruction:
            return "tie"
    return "lose"
