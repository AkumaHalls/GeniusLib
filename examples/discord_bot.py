"""Discord bot example using GeniusLib + discord.py.

Features:
- /player <tag> — mostra informações do jogador
- /clan <tag> — mostra informações do clã
- /war <tag> — mostra status da guerra atual
- /raid <tag> — mostra resumo do último raid
- Eventos de clã em tempo real (join/leave/donations)
"""

import asyncio
import logging
import os

import discord
from discord.ext import commands

import geniuslib
from geniuslib.formatters import (
    format_player_brief, format_clan_detailed, format_war_result,
    format_war_score, format_raid_brief,
)
from geniuslib.war_analytics import count_missed_attacks
from geniuslib.raid_analytics import raid_summary

logging.basicConfig(level=logging.INFO)

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "seu_token_aqui")
COC_EMAIL = os.environ.get("COC_EMAIL", "seu_email@exemplo.com")
COC_PASSWORD = os.environ.get("COC_PASSWORD", "sua_senha")
MONITOR_CLAN_TAGS = os.environ.get("MONITOR_CLANS", "").split(",")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot logado como {bot.user}")


@bot.hybrid_command(name="player", description="Mostra informações de um jogador")
async def cmd_player(ctx: commands.Context, tag: str):
    async with geniuslib.Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)
        try:
            player = await client.get_player(tag)
            embed = discord.Embed(
                title=player.name,
                description=format_player_brief(player),
                color=discord.Color.blue(),
            )
            embed.add_field(name="Nível", value=str(player.exp_level), inline=True)
            embed.add_field(name="Estrelas de Guerra", value=str(player.war_stars), inline=True)
            embed.add_field(name="Clã", value=player.clan.name if player.clan else "Nenhum", inline=True)
            if hasattr(player, "attack_wins"):
                embed.add_field(name="Ataques Vitoriosos", value=str(player.attack_wins), inline=True)
            if hasattr(player, "defense_wins"):
                embed.add_field(name="Defesas Vitoriosas", value=str(player.defense_wins), inline=True)
            embed.set_footer(text=player.tag)
            await ctx.send(embed=embed)
        except geniuslib.NotFound:
            await ctx.send(f"Jogador {tag} não encontrado.")


@bot.hybrid_command(name="clan", description="Mostra informações de um clã")
async def cmd_clan(ctx: commands.Context, tag: str):
    async with geniuslib.Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)
        try:
            clan = await client.get_clan(tag)
            lines = format_clan_detailed(clan).split("\n")
            embed = discord.Embed(
                title=clan.name,
                description=f"{lines[1]}",
                color=discord.Color.green(),
            )
            embed.add_field(name="Descrição", value=(clan.description or "N/A")[:200], inline=False)
            embed.add_field(name="Liga", value=clan.war_league.name if clan.war_league else "N/A", inline=True)
            embed.set_footer(text=clan.tag)
            await ctx.send(embed=embed)
        except geniuslib.NotFound:
            await ctx.send(f"Clã {tag} não encontrado.")


@bot.hybrid_command(name="war", description="Mostra status da guerra atual")
async def cmd_war(ctx: commands.Context, tag: str):
    async with geniuslib.Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)
        try:
            war = await client.get_current_war(tag)
            if war is None:
                await ctx.send("Clã não está em guerra no momento.")
                return
            embed = discord.Embed(
                title=f"⚔️ Guerra: {war.clan.name} vs {war.opponent.name}",
                description=format_war_score(war, tag),
                color=discord.Color.orange(),
            )
            embed.add_field(name="Resultado", value=format_war_result(war, tag), inline=True)
            embed.add_field(name="Ataques perdidos", value=str(count_missed_attacks(war, tag)), inline=True)
            embed.add_field(name="Time", value=war.clan.name if war.clan.tag == tag else war.opponent.name, inline=True)
            await ctx.send(embed=embed)
        except geniuslib.PrivateWarLog:
            await ctx.send("O registro de guerra deste clã é privado.")
        except geniuslib.NotFound:
            await ctx.send(f"Clã {tag} não encontrado.")


@bot.hybrid_command(name="raid", description="Mostra resumo do último raid")
async def cmd_raid(ctx: commands.Context, tag: str):
    async with geniuslib.Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)
        try:
            logs = await client.get_raid_log(tag, limit=1)
            if not logs:
                await ctx.send("Nenhum raid encontrado.")
                return
            [entry] = logs
            summary = raid_summary(entry)
            embed = discord.Embed(
                title="🏰 Resumo do Raid",
                color=discord.Color.purple(),
            )
            off = summary["offensive"]
            deff = summary["defensive"]
            embed.add_field(name="Saqueado", value=f"{off['total_loot']:,}", inline=True)
            embed.add_field(name="Perdido", value=f"{deff['total_loot_lost']:,}", inline=True)
            embed.add_field(name="Ataques perdidos", value=str(summary["missed_attacks"]), inline=True)
            embed.add_field(name="Inativos", value=", ".join(summary["inactive_members"]) or "Nenhum", inline=False)
            embed.add_field(name="Top Atacante", value=summary["top_attacker"] or "N/A", inline=True)
            embed.set_footer(text=f"Membros: {summary['members_raided']}")
            await ctx.send(embed=embed)
        except geniuslib.NotFound:
            await ctx.send(f"Clã {tag} não encontrado.")


@bot.hybrid_command(name="compare", description="Compara dois jogadores")
async def cmd_compare(ctx: commands.Context, tag1: str, tag2: str):
    async with geniuslib.Client() as client:
        await client.login(COC_EMAIL, COC_PASSWORD)
        try:
            p1, p2 = await asyncio.gather(
                client.get_player(tag1),
                client.get_player(tag2),
            )
            embed = discord.Embed(
                title="⚔️ Comparação de Jogadores",
                color=discord.Color.gold(),
            )
            embed.add_field(name="", value=f"**{p1.name}**\nTH{p1.town_hall}\n{p1.trophies} 🏆\nNível {p1.exp_level}", inline=True)
            embed.add_field(name="", value=f"**{p2.name}**\nTH{p2.town_hall}\n{p2.trophies} 🏆\nNível {p2.exp_level}", inline=True)
            await ctx.send(embed=embed)
        except geniuslib.NotFound:
            await ctx.send("Um dos jogadores não foi encontrado.")


async def setup_events():
    """Configura eventos em tempo real para clãs monitorados."""
    client = geniuslib.EventsClient()
    await client.login(COC_EMAIL, COC_PASSWORD)

    @client.event
    @geniuslib.ClanEvents.member_join()
    async def on_member_join(player, clan):
        print(f"{player.name} entrou no clã {clan.name}")

    @client.event
    @geniuslib.ClanEvents.member_leave()
    async def on_member_leave(player, clan):
        print(f"{player.name} saiu do clã {clan.name}")

    @client.event
    @geniuslib.ClanEvents.member_donations(tags=MONITOR_CLAN_TAGS)
    async def on_donations(old_member, member):
        donated = member.donations - old_member.donations
        print(f"{member.name} doou {donated} tropas")

    client.add_clan_updates(*MONITOR_CLAN_TAGS)
    return client


async def main():
    if COC_EMAIL and COC_PASSWORD:
        events_client = await setup_events()
        asyncio.create_task(events_client.run_forever())
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
