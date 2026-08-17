<div align="center">

# GeniusLib

**The complete async Python SDK for the Clash of Clans API**

[![PyPI version](https://img.shields.io/pypi/v/geniuslib?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/geniuslib/)
[![Python versions](https://img.shields.io/pypi/pyversions/geniuslib?logo=python&logoColor=white)](https://pypi.org/project/geniuslib/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/AkumaHalls/GeniusLib/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/geniuslib?color=orange&logo=pypi&logoColor=white)](https://pypi.org/project/geniuslib/)
[![Tests](https://img.shields.io/badge/tests-110%20passed-brightgreen.svg)](https://github.com/AkumaHalls/GeniusLib)
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
| **API Coverage** | 35/35 endpoints | 30/35 endpoints |
| **Events System** | Real-time clan/war/player events | Not included |
| **War Analytics** | new_stars, best_attack, missed, cleanup | Basic only |
| **Raid Analytics** | Full offensive/defensive breakdown | Not included |
| **Battle Log Analytics** | Win rate, streaks, league progression | Not included |
| **Middleware Pipeline** | Request/response interceptors | Not included |
| **Game Assets** | 3000+ bundled WebP icons | Not included |
| **CLI** | Built-in (`python -m geniuslib`) | Not included |
| **Upgrade Tracker** | Cost/time estimation per TH level | Not included |
| **Cache TTL** | Auto-expiring cache with background sweep | Not included |
| **Maintenance Polling** | Auto-detects Supercell maintenance | Not included |
| **Army Link Parser** | Decode in-game army share codes | Not included |
| **Test Suite** | 110 pytest tests | Minimal |

---

## Quick Start

### Installation

```sh
# From PyPI (recommended)
pip install geniuslib

# From source
pip install git+https://github.com/AkumaHalls/GeniusLib.git
```

### Authentication

```python
import geniuslib, asyncio

async def main():
    client = geniuslib.Client()

    # Option 1: Email/password (recommended for bots)
    await client.login("email@example.com", "password")

    # Option 2: Direct API token
    await client.login_with_tokens("your-api-token")

    # Now use the client...
    clan = await client.get_clan("#2PP")
    print(f"{clan.name} — Level {clan.level}")

    await client.close()

asyncio.run(main())
```

### Using as context manager

```python
async with geniuslib.Client() as client:
    await client.login("email", "password")
    player = await client.get_player("#TAG")
    print(player.name, player.town_hall)
```

---

## Features

### All 35 Official API Endpoints

GeniusLib covers every endpoint in the Clash of Clans API:

**Clans** — search, info, members, war log, current war, CWL group, capital raids
**Players** — info, battle log, league history, token verification
**Leagues** — all leagues, seasons, rankings, tiers
**Locations** — rankings for clans, players, builder base, capital
**War Leagues** — search, info, individual wars
**Capital Leagues** — search, info
**Builder Base Leagues** — search, info
**Labels** — clan labels, player labels
**Gold Pass** — current season info

### Real-Time Events

```python
from geniuslib import EventsClient, ClanEvents, WarEvents, PlayerEvents, ClientEvents

events = EventsClient(client, clan_tags=["#TAG1", "#TAG2"])

@ClanEvents.member_join()
async def on_join(member, clan):
    print(f"{member.name} joined {clan.name}")

@WarEvents.war_attack()
async def on_attack(member, attack):
    print(f"{member.name}: {attack.stars} stars!")

@ClientEvents.maintenance_start
async def on_maintenance():
    print("Supercell maintenance started")

await events.start()
```

### War Analytics

```python
from geniuslib.war_analytics import *

war = await client.get_current_war("#TAG")

count_missed_attacks(war, "#TAG")     # 2
best_attack_on(member)                 # WarAttack object
get_cleanup_attacks(war, "#TAG")      # list of wasted attacks
get_war_result(war, "#TAG")           # 'win', 'lose', 'tie'
```

### Raid Analytics

```python
from geniuslib.raid_analytics import *

logs = await client.get_raid_log("#TAG", limit=1)
summary = raid_summary(logs[0])

summary["offensive"]["total_loot"]     # 45000
summary["missed_attacks"]              # 3
summary["inactive_members"]            # ['Player1', 'Player2']
```

### Batch Fetching

```python
from geniuslib import Client, ClanIterator

async with Client() as client:
    await client.login("email", "password")

    # Fetch multiple clans in parallel
    tags = ["#TAG1", "#TAG2", "#TAG3", "#TAG4", "#TAG5"]
    async for clan in ClanIterator(client, tags):
        print(f"{clan.name}: {clan.level}")

    # Or use gather for specific fetches
    import asyncio
    players = await asyncio.gather(*[
        client.get_player(tag) for tag in ["#P1", "#P2", "#P3"]
    ])
```

### Middleware Pipeline

```python
from geniuslib.middleware import middleware, request_logger

# Built-in request logging
client.http.add_middleware(request_logger)

# Custom middleware
@middleware("response")
async def cache_buster(resp):
    resp.data["cached"] = False
    return resp

client.http.add_middleware(cache_buster)
```

### Game Assets (3000+ icons)

```python
player = await client.get_player("#TAG")

for troop in player.troops:
    print(f"{troop.name}: {troop.asset_url}")
    # "Barbarian": "/assets/troops/barbarian/icon.webp"

for hero in player.heroes:
    print(f"{hero.name}: {hero.asset_url}")
    for eq in hero.equipment:
        print(f"  {eq.name}: {eq.asset_url}")
```

Serve them with any framework:

```python
# aiohttp
from geniuslib.utils import get_assets_dir
app.router.add_static('/assets/', get_assets_dir())

# FastAPI
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
from geniuslib.utils import encode_tag, decode_tag, get_season_id
from geniuslib.formatters import format_th, format_trophies, format_role
from geniuslib.exporter import to_json, to_csv
from geniuslib.comparer import compare_players, compare_clans
from geniuslib.upgrade_tracker import get_th_upgrade_summary

# Tag encoding
encode_tag("#2PP")                    # 256

# Season math
get_season_id()                       # "2026-07"

# Formatters
format_th(16)                         # "🔑 TH16"
format_trophies(5000)                 # "🏆 5,000"

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
pip install pytest pytest-asyncio
pytest tests/ -v
```

110 tests covering utils, war analytics, raid analytics, battle log analytics, formatters, middleware, exporters, and comparers.

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Run tests (`pytest tests/ -v`)
4. Submit a pull request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Credits

Built by [AkumaHalls](https://github.com/AkumaHalls) for the [ClashGenius](https://github.com/AkumaHalls/ClashGenius) project.
Based on the original [coc.py](https://github.com/mathsman5133/coc.py) by mathsman5133.