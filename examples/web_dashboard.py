"""Web Dashboard — minimal aiohttp dashboard with GeniusLib.

Displays clan info, current war, and recent raids on a single page.
Run: python web_dashboard.py
Visit: http://localhost:8080
"""

import asyncio
import os

from aiohttp import web

from geniuslib import Client
from geniuslib.formatters import format_war_score, format_war_result, format_clan_detailed
from geniuslib.raid_analytics import raid_summary

COC_EMAIL = os.environ.get("COC_EMAIL", "seu_email@exemplo.com")
COC_PASSWORD = os.environ.get("COC_PASSWORD", "sua_senha")
CLAN_TAG = os.environ.get("CLAN_TAG", "#2PP")

client = Client()


async def index(request: web.Request) -> web.Response:
    """Main dashboard page."""
    try:
        clan = await client.get_clan(CLAN_TAG)
    except Exception as e:
        return web.Response(text=f"Error fetching clan: {e}", status=500)

    war = None
    try:
        war = await client.get_current_war(CLAN_TAG)
    except Exception:
        pass

    raids = []
    try:
        raids = await client.get_raid_log(CLAN_TAG, limit=3)
    except Exception:
        pass

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{clan.name} Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #0f0f23; color: #e0e0e0; padding: 2rem; }}
        h1 {{ color: #ffd700; margin-bottom: 0.5rem; }}
        h2 {{ color: #4fc3f7; margin: 1.5rem 0 0.5rem; }}
        .clan-info {{ background: #1a1a2e; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; }}
        .war-info {{ background: #1a1a2e; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; }}
        .raid-card {{ background: #1a1a2e; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;
                      display: flex; justify-content: space-between; }}
        .stat {{ display: inline-block; margin-right: 2rem; }}
        .stat-value {{ font-size: 1.5rem; font-weight: bold; color: #ffd700; }}
        .stat-label {{ font-size: 0.8rem; color: #888; }}
        .no-data {{ color: #888; font-style: italic; }}
    </style>
</head>
<body>
    <h1>{clan.name}</h1>
    <p>{clan.tag} &mdash; Level {clan.level} &mdash; {clan.member_count}/50 members</p>

    <div class="clan-info">
        <span class="stat"><span class="stat-value">{clan.war_wins}W</span> <span class="stat-label">Wins</span></span>
        <span class="stat"><span class="stat-value">{clan.war_losses}L</span> <span class="stat-label">Losses</span></span>
        <span class="stat"><span class="stat-value">{clan.war_ties}T</span> <span class="stat-label">Ties</span></span>
        <span class="stat"><span class="stat-value">{clan.clan_points:,}</span> <span class="stat-label">Points</span></span>
        <span class="stat"><span class="stat-value">{clan.clan_capital_points:,}</span> <span class="stat-label">Capital</span></span>
    </div>

    <h2>Current War</h2>
    <div class="war-info">"""

    if war and war.state != "notInWar":
        html += f"""
        <p><strong>{war.clan.name}</strong> vs <strong>{war.opponent.name}</strong></p>
        <p>{format_war_score(war, CLAN_TAG)}</p>
        <p>Result: {format_war_result(war, CLAN_TAG)}</p>"""
    else:
        html += '<p class="no-data">Not currently in war</p>'

    html += """
    </div>

    <h2>Recent Raids</h2>"""

    if raids:
        for raid in raids:
            s = raid_summary(raid)
            html += f"""
    <div class="raid-card">
        <div>
            <strong>{raid.state}</strong>
            <br><small>{raid.start_time.strftime('%b %d')} — {raid.end_time.strftime('%b %d, %Y')}</small>
        </div>
        <div>
            <span class="stat"><span class="stat-value">{s['offensive']['total_loot']:,}</span> <span class="stat-label">Loot</span></span>
            <span class="stat"><span class="stat-value">{s['offensive']['total_attacks']}</span> <span class="stat-label">Attacks</span></span>
            <span class="stat"><span class="stat-value">{s['missed_attacks']}</span> <span class="stat-label">Missed</span></span>
        </div>
    </div>"""
    else:
        html += '<p class="no-data">No raid data available</p>'

    html += """
</body>
</html>"""

    return web.Response(text=html, content_type="text/html")


async def start_client(app: web.Application):
    await client.login(COC_EMAIL, COC_PASSWORD)
    app["client"] = client


async def cleanup_client(app: web.Application):
    await client.close()


def create_app() -> web.Application:
    app = web.Application()
    app.on_startup.append(start_client)
    app.on_cleanup.append(cleanup_client)
    app.router.add_get("/", index)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8080)
