"""Raid Reporter — relatório completo de Capital Raid.

Gera relatório detalhado do último raid com estatísticas
ofensivas, defensivas, desempenho individual e muito mais.
"""

import asyncio
import os
from datetime import datetime

from geniuslib import Client
from geniuslib.raid_analytics import (
    raid_summary, clan_offensive_stats, clan_defensive_stats,
    get_inactive_raid_members, count_missed_raid_attacks,
    get_wasted_attacks, get_raid_cleanup_attacks,
)

COC_EMAIL = os.environ.get("COC_EMAIL", "seu_email@exemplo.com")
COC_PASSWORD = os.environ.get("COC_PASSWORD", "sua_senha")


async def generate_raid_report(clan_tag: str) -> str:
    """Gera relatório completo do último raid."""
    async with Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)
        logs = await client.get_raid_log(clan_tag, limit=1)
        if not logs:
            return "Nenhum raid encontrado."

        [entry] = logs
        summary = raid_summary(entry)
        off = summary["offensive"]
        deff = summary["defensive"]

        lines = []
        lines.append(f"{'='*50}")
        lines.append(f"🏰 RELATÓRIO DE RAID")
        lines.append(f"{'='*50}")
        lines.append(f"Estado: {summary['state']}")
        lines.append(f"Início: {summary['start_time']}")
        lines.append(f"Fim: {summary['end_time']}")

        lines.append(f"\n📈 OFENSIVO:")
        lines.append(f"  🪙 Saqueado: {off['total_loot']:,}")
        lines.append(f"  ⚔️ Ataques: {off['total_attacks']}")
        lines.append(f"  🏘️ Distritos: {off['total_districts']}")
        lines.append(f"  💥 Destruídos: {off['districts_destroyed']}")
        lines.append(f"  📊 Eficiência: {off['efficiency']}%")

        lines.append(f"\n📉 DEFENSIVO:")
        lines.append(f"  💸 Saque perdido: {deff['total_loot_lost']:,}")
        lines.append(f"  ⚔️ Ataques recebidos: {deff['attacks_received']}")
        lines.append(f"  💥 Distritos perdidos: {deff['districts_lost']}")

        missed = count_missed_raid_attacks(entry, clan_tag)
        lines.append(f"\n🔴 Ataques perdidos: {missed}")

        inactive = get_inactive_raid_members(entry)
        if inactive:
            lines.append(f"\n😴 MEMBROS INATIVOS:")
            for m in inactive:
                lines.append(f"  • {m.name} ({m.tag})")

        wasted = get_wasted_attacks(entry, clan_tag)
        if wasted:
            lines.append(f"\n💩 ATAQUES DESPERDIÇADOS (0⭐ <30%): {len(wasted)}")
            for a in wasted[:5]:
                lines.append(f"  • {a.attacker_tag} → {a.district.name}: {a.destruction:.1f}%")

        cleanup = get_raid_cleanup_attacks(entry, clan_tag)
        if cleanup:
            lines.append(f"\n🧹 ATAQUES EM DISTRITOS JÁ DESTRUÍDOS: {len(cleanup)}")

        if summary["top_attacker"]:
            lines.append(f"\n🏆 TOP ATACANTE: {summary['top_attacker']} ({summary['top_attacker_loot']:,} saqueado)")

        lines.append(f"\n{'='*50}")
        lines.append(f"Gerado em: {datetime.now():%d/%m/%Y %H:%M}")
        return "\n".join(lines)


async def main():
    tag = input("Tag do clã: ")
    report = await generate_raid_report(tag)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
