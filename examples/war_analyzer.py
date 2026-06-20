"""War Analyzer — análise detalhada de guerra.

Gera relatório completo de desempenho de guerra para um clã,
incluindo melhores ataques, defesas, ataques perdidos, limpeza, etc.
"""

import asyncio
import os
from datetime import datetime

from geniuslib import Client
from geniuslib.war_analytics import (
    best_attack_on, best_defense_on, total_attack_stars,
    total_attack_destruction, get_cleanup_attacks, count_missed_attacks,
    get_war_result, new_stars,
)
from geniuslib.formatters import format_attack, format_number, format_percentage

COC_EMAIL = os.environ.get("COC_EMAIL", "seu_email@exemplo.com")
COC_PASSWORD = os.environ.get("COC_PASSWORD", "sua_senha")


async def analyze_war(clan_tag: str) -> str:
    """Gera relatório de análise de guerra."""
    async with Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)
        war = await client.get_current_war(clan_tag)
        if war is None:
            return "Clã não está em guerra no momento."

        tag = clan_tag
        clan = war.clan if war.clan.tag == tag else war.opponent
        opponent = war.opponent if war.clan.tag == tag else war.clan

        lines = []
        lines.append(f"{"="*50}")
        lines.append(f"📊 RELATÓRIO DE GUERRA")
        lines.append(f"{clan.name} vs {opponent.name}")
        lines.append(f"{'='*50}")

        # Resultado
        result = get_war_result(war, tag)
        result_emoji = {"win": "✅ Vitória", "lose": "❌ Derrota", "tie": "🤝 Empate", "ongoing": "⏳ Em andamento"}
        lines.append(f"\nResultado: {result_emoji.get(result, result)}")
        lines.append(f"Placar: {clan.stars} ⭐ x {opponent.stars} ⭐")
        lines.append(f"Destruição: {clan.destruction:.1f}% x {opponent.destruction:.1f}%")

        # Ataques perdidos
        missed = count_missed_attacks(war, tag)
        lines.append(f"\n🔴 Ataques perdidos: {missed}")

        # Melhores atacantes
        lines.append(f"\n🏆 TOP ATACANTES:")
        sorted_members = sorted(clan.members, key=total_attack_stars, reverse=True)
        for i, m in enumerate(sorted_members[:5], 1):
            stars = total_attack_stars(m)
            dest = total_attack_destruction(m)
            best = best_attack_on(m)
            best_str = format_attack(best.stars, best.destruction) if best else "N/A"
            lines.append(f"  {i}. {m.name} — {stars}⭐ {dest:.1f}% | Melhor: {best_str}")

        # Melhores defesas
        lines.append(f"\n🛡️ MELHORES DEFESAS:")
        sorted_def = sorted(clan.members, key=lambda m: best_defense_on(m).stars if m.defenses else 0, reverse=True)
        for i, m in enumerate(sorted_def[:5], 1):
            bd = best_defense_on(m)
            if bd:
                lines.append(f"  {i}. {m.name} — defendeu {format_attack(bd.stars, bd.destruction)}")

        # Ataques de limpeza
        cleanup = get_cleanup_attacks(war, tag)
        if cleanup:
            lines.append(f"\n🧹 ATAQUES DE LIMPEZA (0 novas estrelas): {len(cleanup)}")
            for a in cleanup[:5]:
                lines.append(f"  {a.attacker.name} → {a.defender.name}: {format_attack(a.stars, a.destruction)}")

        lines.append(f"\n{'='*50}")
        lines.append(f"Gerado em: {datetime.now():%d/%m/%Y %H:%M}")
        return "\n".join(lines)


async def main():
    tag = input("Tag do clã: ")
    report = await analyze_war(tag)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
