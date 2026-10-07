<div align="center">

# GeniusLib

**The complete async Python SDK for the Clash of Clans API**

[![PyPI version](https://img.shields.io/pypi/v/geniuslib?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/geniuslib/)
[![Python versions](https://img.shields.io/pypi/pyversions/geniuslib?logo=python&logoColor=white)](https://pypi.org/project/geniuslib/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/AkumaHalls/GeniusLib/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/geniuslib?color=orange&logo=pypi&logoColor=white)](https://pypi.org/project/geniuslib/)
[![Tests](https://img.shields.io/badge/tests-258%20passed-brightgreen.svg)](https://github.com/AkumaHalls/GeniusLib)
[![Docs](https://img.shields.io/badge/docs-readthedocs-blue.svg)](https://geniuslib.readthedocs.io)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-black.svg)](https://github.com/astral-sh/ruff)

---

GeniusLib is a **fully async** Python wrapper for the official [Clash of Clans API](https://developer.clashofclans.com/).
Built for Discord bots, war trackers, capital raid analyzers, and anything that needs fast, reliable CoC data.

```sh
pip install geniuslib
```

```python
import geniuslib, asyncio

async def main():
    async with geniuslib.Client() as client:
        await client.login("email", "password")
        player = await client.get_player("#TAG")
        print(f"{player.name} — TH{player.town_hall} — {player.trophies} trophies")

asyncio.run(main())
```

</div>

---

## Why GeniusLib?

| Feature | GeniusLib | coc.py |
|---------|-----------|--------|
| **Async/await** | Native async throughout | Partial (sync wrappers) |
| **API Coverage** | All official endpoints (47 client methods) | Most |
| **Events System** | Real-time clan/war/player events | Not included |
| **War Analytics** | new_stars, best_attack, missed, cleanup, war_result | Basic only |
| **Raid Analytics** | Full offensive/defensive breakdown | Not included |
| **Battle Log Analytics** | Win rate, streaks, league progression, army-code decode | Not included |
| **Middleware Pipeline** | Request/response interceptors | Not included |
| **Game Assets** | 3000+ bundled icons (shipped as release asset) | Not included |
| **CLI** | Built-in (`python -m geniuslib`) | Not included |
| **Upgrade Tracker** | Cost/time estimation per TH level | Not included |
| **Cache TTL** | Auto-expiring cache with background sweep | Not included |
| **Maintenance Polling** | Auto-detects Supercell maintenance | Not included |
| **Army Link Parser** | Decode in-game army share codes | Not included |
| **Test Suite** | 258 pytest tests | Minimal |

---

## Quick Start

### Installation

```sh
# From PyPI (recommended)
pip install geniuslib

# From source
pip install git+https://github.com/AkumaHalls/GeniusLib.git

# Development (tests + lint gates)
pip install -e .[dev]
```

### Authentication

```python
import geniuslib, asyncio

async def main():
    client = geniuslib.Client()

    # Option 1: Email/password (recommended for bots). GeniusLib will fetch and
    # rotate API keys for you, and re-authenticates once if the API answers
    # "accessDenied.invalidIp".
    await client.login("email@example.com", "password")

    # Option 2: A raw API key from the developer site
    await client.login_with_tokens("your-api-token")

    clan = await client.get_clan("#2PP")
    print(f"{clan.name} — Level {clan.level}")

    await client.close()

asyncio.run(main())
```

### Using as a context manager

```python
async with geniuslib.Client() as client:
    await client.login("email", "password")
    player = await client.get_player("#TAG")
    print(player.name, player.town_hall)
```

---

## Features

### All Official API Endpoints

GeniusLib covers every endpoint of the Clash of Clans API:

**Clans** — `search_clans`, `get_clan`, `get_members`, `get_war_log`, `get_raid_log`, `get_clan_war`, `get_current_war`, `get_league_group`, `get_league_war`
**Players** — `get_player`, `verify_player_token`, `get_player_battlelog`, `get_player_league_history`
**Leagues** — `search_leagues`, `get_league`, `get_league_named`, `get_seasons`, `get_season_rankings`, `search_league_tiers`, `get_league_tier`
**Locations** — `search_locations`, `get_location`, and rankings for clans, players, capital raids, and builder base
**War Leagues** — `search_war_leagues`, `get_war_league`, plus `_named` lookups
**Capital Leagues** — `search_capital_leagues`, `get_capital_league`, plus `_named` lookups
**Builder Base Leagues** — `search_builder_base_leagues`, `get_builder_base_league`, plus `_named` lookups
**Labels** — `get_clan_labels`, `get_player_labels`
**Gold Pass** — `get_current_goldpass_season`

### Real-Time Events

`EventsClient` polls the API in the background and fires typed events when game state changes:

```python
import asyncio
from geniuslib import EventsClient, ClanEvents, WarEvents, PlayerEvents

async def main():
    events = EventsClient()
    await events.login("email", "password")

    events.add_clan_updates("#TAG1", "#TAG2")
    events.add_war_updates("#TAG1", "#TAG2")

    @events.event
    @ClanEvents.member_join()
    async def on_join(player, clan):
        print(f"{player.name} joined {clan.name}")

    @events.event
    @WarEvents.war_attack()
    async def on_attack(member, attack):
        print(f"{member.name}: {attack.stars} stars")

    @events.event
    @PlayerEvents.troop_change()
    async def on_troop(player, troop):
        print(f"{player.name} changed {troop.name}")

    # run the pollers as background tasks alongside the rest of your app
    loop_task = asyncio.create_task(events.run_forever())
    await loop_task

asyncio.run(main())
```

The runnable event decorators are grouped into four classes: `ClanEvents` (`member_join`, `member_leave`), `WarEvents` (`war_attack`, `new_war`), `PlayerEvents` (`troop_change`, `hero_change`, `equipment_change`, `achievement_change`, `joined_clan`, `left_clan`, `clan_name`, `clan_badge`, …), and `ClientEvents` (maintenance start/end, season/raid-weekend resets). For a script whose only job is to follow events, `EventsClient.run_forever()` runs a blocking main loop.

### War Analytics

`war_analytics` helpers: `get_war_result(war, tag)`, `count_missed_attacks(war, tag)`, `get_cleanup_attacks(war, tag)`, `new_stars(attack)`, `previous_best_attack`, `best_attack_on`, `best_defense_on`, `total_attack_stars`, `get_attack_order`, and more:

```python
from geniuslib.war_analytics import get_war_result, count_missed_attacks

war = await client.get_current_war("#TAG")
print(get_war_result(war, "#TAG"))       # 'win' | 'lose' | 'tie'
print(count_missed_attacks(war, "#TAG")) # how many attacks were not used
```

### Raid Analytics

```python
from geniuslib.raid_analytics import (
    raid_summary, get_inactive_raid_members,
    district_attack_breakdown, get_attack_log, get_defense_log,
)

logs = await client.get_raid_log("#TAG", limit=1)
summary = raid_summary(logs[0])

summary["offensive"]["total_loot"]    # total loot from offence
summary["inactive_members"]           # ['Player1', 'Player2']
summary["missed_attacks"]             # total unused attacks
```

Also available: `clan_offensive_stats`, `clan_defensive_stats`, `member_raid_contribution`, `best_raid_attack`, `get_raid_cleanup_attacks`, `get_wasted_attacks`, `average_attack_destruction`.

### Battle Log Analytics (and army-code decoder)

```python
from geniuslib.battlelog_analytics import (
    battle_win_rate, battle_streak, battle_attack_stats,
    league_history_progression, decode_army_code,
)

battles = await client.get_player_battlelog("#TAG")
print(battle_win_rate(battles))               # 0.62
print(battle_streak(battles))                 # 4 consecutive wins

# Decode an in-game army share link/code from the "Copy army" button
army = decode_army_code("YOUR-ARMY-CODE")
print([t.name for t in army["troops"]])
```

Other helpers: `battle_defense_stats`, `battle_loot_summary`, `battle_consistency_score`, `battle_daily_summary`, `battle_period_summary`, `league_season_stats`, `league_tier_distribution`, `tier_group_member_stats`.

### Batch Fetching

```python
from geniuslib import Client, ClanIterator

async with Client() as client:
    await client.login("email", "password")

    tags = ["#TAG1", "#TAG2", "#TAG3", "#TAG4", "#TAG5"]
    async for clan in ClanIterator(client, tags):
        print(f"{clan.name}: {clan.level}")

    # Or fan out individual fetches
    import asyncio
    players = await asyncio.gather(*[client.get_player(t) for t in ["#P1", "#P2"]])
```

### Middleware Pipeline

```python
from geniuslib.middleware import middleware, request_logger

# Built-in request logging
client.http.add_middleware(request_logger)

# Custom response middleware
@middleware("response")
async def cache_buster(resp):
    resp.data["cached"] = False
    return resp

client.http.add_middleware(cache_buster)
```

### Game Assets (3000+ icons)

Models expose `asset_url` as an absolute path (e.g. `/assets/troops/barbarian/icon.webp`). The full ~413&nbsp;MB icon bundle ships separately as `geniuslib-assets-<version>.tar.gz` on [GitHub Releases](https://github.com/AkumaHalls/GeniusLib/releases) — it stays **out of the PyPI wheel** so installs are ~1&nbsp;MB. Fetch it with:

```sh
python scripts/download_assets.py --version 5.6.0   # verifies SHA-256 before extracting
```

Then serve the icons from any web framework:

```python
from geniuslib.utils import get_assets_dir

# aiohttp
app.router.add_static('/assets/', get_assets_dir())

# FastAPI (starlette)
from starlette.staticfiles import StaticFiles
app.mount('/assets/', StaticFiles(directory=get_assets_dir()))
```

### CLI

```sh
python -m geniuslib player #TAG
python -m geniuslib clan #TAG
python -m geniuslib war #TAG
python -m geniuslib raid #TAG
python -m geniuslib search "clan name"
python -m geniuslib export #TAG --format json
python -m geniuslib compare player #TAG1 #TAG2
```

### Utilities

```python
from geniuslib.utils import encode_tag, decode_tag, get_season_id, asset_path
from geniuslib.formatters import format_th, format_trophies, format_role
from geniuslib.exporter import to_json, to_csv, export_players, export_clans
from geniuslib.comparer import compare_players, compare_clans
from geniuslib.upgrade_tracker import get_th_upgrade_summary

# Tag encoding
encode_tag("#2PP")                # 256 (see also decode_tag)

# Season math
get_season_id()                   # '2026-10'

# Formatters
format_th(16)                     # '🔑 TH16'
format_trophies(5000)             # '🏆 5,000'

# Upgrade cost estimation
summary = get_th_upgrade_summary(16)
print(f"Total time: {summary.total_time_days} days")
```

---

## Examples

The [`examples/`](https://github.com/AkumaHalls/GeniusLib/tree/main/examples) folder contains ready-to-run scripts:

| Example | Description |
|---------|-------------|
| [`discord_bot.py`](examples/discord_bot.py) | Full Discord bot with /player, /clan, /war, /raid commands + real-time events |
| [`war_analyzer.py`](examples/war_analyzer.py) | Detailed war performance report with top attackers, defense, cleanup |
| [`raid_reporter.py`](examples/raid_reporter.py) | Capital Raid report with offensive/defensive stats and inactive detection |
| [`export_data.py`](examples/export_data.py) | Export player/clan data to JSON or CSV |
| [`batch_fetch.py`](examples/batch_fetch.py) | Fetch multiple clans/players in parallel |
| [`web_dashboard.py`](examples/web_dashboard.py) | Minimal web dashboard with aiohttp |

---

## Documentation

Full documentation is available at **[geniuslib.readthedocs.io](https://geniuslib.readthedocs.io)**.

### Building docs locally

```sh
pip install mkdocs mkdocs-material mkdocstrings[python]
mkdocs serve
```

---

## Testing

```sh
pip install -e .[dev]
ruff check .          # zero errors allowed (configured: E, F, I, W, line-length 120)
pytest tests/ -q      # 258 tests
```

The test suite covers utils, war analytics, raid analytics, battle log analytics, formatters, middleware, exporters, comparers, HTTP layer, async layers, and the client surface.

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Keep the gates green: `ruff check .` and `pytest tests/ -q`
4. Submit a pull request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Credits

Built by [AkumaHalls](https://github.com/AkumaHalls) for the [ClashGenius](https://github.com/AkumaHalls/ClashGenius) project.
Based on the original [coc.py](https://github.com/mathsman5133/coc.py) by mathsman5133.