import asyncio
from geniuslib import Client
from geniuslib.war_analytics import get_war_result, get_best_attack, get_average_stars


async def main():
    async with Client() as client:
        clan_tag = "#ABC"
        war = await client.get_current_war(clan_tag)
        clan = war.clan if war.clan.tag == clan_tag else war.opponent
        opponent = war.opponent if war.clan.tag == clan_tag else war.clan

        lines = []
        lines.append("=" * 50)
        lines.append("RELATORIO DE GUERRA")
        lines.append(f"{clan.name} vs {opponent.name}")
        lines.append("=" * 50)

        # Resultado
        result = get_war_result(war, clan_tag)
        lines.append(f"Resultado: {result}")
        lines.append(f"Estrelas: {clan.stars} x {opponent.stars}")
        lines.append(f"Destruicao: {clan.destruction_percentage}% x {opponent.destruction_percentage}%")
        lines.append("=" * 50)

        # Melhor ataque
        best = get_best_attack(war)
        if best:
            lines.append(
                f"Melhor ataque: {best.attacker.name} vs {best.defender.name} - {best.stars} estrelas ({best.destruction_percentage}%)"
            )

        # Media de estrelas
        avg = get_average_stars(war, clan_tag)
        lines.append(f"Media de estrelas ({clan.name}): {avg:.2f}")
        lines.append("=" * 50)

        print("\n".join(lines))


if __name__ == "__main__":
    asyncio.run(main())
