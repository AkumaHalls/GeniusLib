# GeniusLib - Clash of Clans API wrapper
# (c) 2026 AkumaHalls / ClashGenius

from typing import List, Optional

from .raid import RaidLogEntry, RaidMember, RaidAttack, RaidClan, RaidDistrict


def total_member_attack_stars(member: RaidMember) -> int:
    member_attacks = member.attacks
    if not member_attacks:
        return 0
    return sum(a.stars for a in member_attacks)


def total_member_destruction(member: RaidMember) -> float:
    member_attacks = member.attacks
    if not member_attacks:
        return 0.0
    return sum(a.destruction for a in member_attacks)


def best_raid_attack(member: RaidMember) -> Optional[RaidAttack]:
    if not member.attacks:
        return None
    return max(member.attacks, key=lambda a: (a.stars, a.destruction))


def average_attack_destruction(member: RaidMember) -> float:
    member_attacks = member.attacks
    if not member_attacks:
        return 0.0
    return sum(a.destruction for a in member_attacks) / len(member_attacks)


def count_missed_raid_attacks(raid_entry: RaidLogEntry, clan_tag: str) -> int:
    clan_members = [m for m in raid_entry.members]
    total_possible = sum(m.attack_limit + m.bonus_attack_limit for m in clan_members)
    total_used = sum(m.attack_count for m in clan_members)
    return total_possible - total_used


def get_inactive_raid_members(raid_entry: RaidLogEntry) -> List[RaidMember]:
    return [m for m in raid_entry.members if m.attack_count == 0]


def member_raid_contribution(member: RaidMember) -> float:
    if not member.raid_log_entry.total_loot:
        return 0.0
    return (member.capital_resources_looted / member.raid_log_entry.total_loot) * 100


def district_attack_breakdown(district: RaidDistrict) -> dict:
    stars_3 = sum(1 for a in district.attacks if a.stars == 3)
    stars_2 = sum(1 for a in district.attacks if a.stars == 2)
    stars_1 = sum(1 for a in district.attacks if a.stars == 1)
    stars_0 = sum(1 for a in district.attacks if a.stars == 0)
    return {"3_stars": stars_3, "2_stars": stars_2, "1_star": stars_1, "0_stars": stars_0}


def get_raid_cleanup_attacks(raid_entry: RaidLogEntry, clan_tag: str) -> List[RaidAttack]:
    cleanup = []
    for raid_clan in raid_entry.attack_log:
        for district in raid_clan.districts:
            if district.destruction >= 100:
                cleanup.extend(district.attacks)
    return cleanup


def get_wasted_attacks(raid_entry: RaidLogEntry, clan_tag: str) -> List[RaidAttack]:
    wasted = []
    for raid_clan in raid_entry.attack_log:
        for district in raid_clan.districts:
            for attack in district.attacks:
                if attack.stars == 0 and attack.destruction < 30:
                    wasted.append(attack)
    return wasted


def clan_offensive_stats(raid_entry: RaidLogEntry) -> dict:
    total_loot = sum(rc.looted for rc in raid_entry.attack_log)
    total_attacks = sum(rc.attack_count for rc in raid_entry.attack_log)
    total_districts = sum(rc.district_count for rc in raid_entry.attack_log)
    total_destroyed = sum(rc.destroyed_district_count for rc in raid_entry.attack_log)
    return {
        "total_loot": total_loot,
        "total_attacks": total_attacks,
        "total_districts": total_districts,
        "districts_destroyed": total_destroyed,
        "efficiency": round((total_destroyed / total_districts * 100), 1) if total_districts else 0,
    }


def clan_defensive_stats(raid_entry: RaidLogEntry) -> dict:
    total_loot_lost = sum(rc.looted for rc in raid_entry.defense_log)
    total_attacks_received = sum(rc.attack_count for rc in raid_entry.defense_log)
    total_districts_lost = sum(rc.destroyed_district_count for rc in raid_entry.defense_log)
    return {
        "total_loot_lost": total_loot_lost,
        "attacks_received": total_attacks_received,
        "districts_lost": total_districts_lost,
    }


def raid_summary(raid_entry: RaidLogEntry) -> dict:
    off = clan_offensive_stats(raid_entry)
    deff = clan_defensive_stats(raid_entry)
    missed = count_missed_raid_attacks(raid_entry, raid_entry.clan_tag)
    inactive = get_inactive_raid_members(raid_entry)
    top_attacker = max(raid_entry.members, key=lambda m: m.capital_resources_looted) if raid_entry.members else None
    return {
        "state": raid_entry.state,
        "start_time": raid_entry.start_time,
        "end_time": raid_entry.end_time,
        "offensive": off,
        "defensive": deff,
        "members_raided": len(raid_entry.members),
        "missed_attacks": missed,
        "inactive_members": [m.name for m in inactive],
        "top_attacker": top_attacker.name if top_attacker else None,
        "top_attacker_loot": top_attacker.capital_resources_looted if top_attacker else 0,
    }


def get_attack_log(raid_entry: RaidLogEntry) -> List[RaidClan]:
    return list(raid_entry.attack_log)


def get_defense_log(raid_entry: RaidLogEntry) -> List[RaidClan]:
    return list(raid_entry.defense_log)
