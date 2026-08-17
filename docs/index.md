# GeniusLib

**The complete async Python SDK for the Clash of Clans API**

[![PyPI version](https://img.shields.io/pypi/v/geniuslib?color=blue)](https://pypi.org/project/geniuslib/)
[![Python versions](https://img.shields.io/pypi/pyversions/geniuslib)](https://pypi.org/project/geniuslib/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/AkumaHalls/GeniusLib/blob/main/LICENSE)

---

GeniusLib is a **fully async** Python wrapper for the official Clash of Clans API.
It covers all 35 API endpoints and includes built-in analytics, events, middleware, CLI, and 3000+ game assets.

## Installation

```sh
pip install geniuslib
```

## Quick Example

```python
import geniuslib, asyncio

async def main():
    async with geniuslib.Client() as client:
        await client.login("email", "password")
        player = await client.get_player("#TAG")
        print(f"{player.name} — TH{player.town_hall}")

asyncio.run(main())
```

## Key Features

- **35/35 API endpoints** — full coverage of the official Clash of Clans API
- **Real-time events** — clan joins/leaves, war attacks, donations, maintenance
- **War analytics** — new stars, best attacks, missed attacks, cleanup detection
- **Raid analytics** — offensive/defensive breakdown, inactive detection
- **Battle log analytics** — win rate, streaks, league progression
- **Middleware pipeline** — intercept and transform HTTP requests
- **3000+ game assets** — bundled WebP icons for troops, heroes, spells, equipment
- **CLI** — query players, clans, wars from the terminal
- **Upgrade tracker** — cost and time estimation per Town Hall level
- **Cache TTL** — automatic cache expiration with background sweep
- **Batch fetching** — parallel requests with iterators

## Links

- [GitHub](https://github.com/AkumaHalls/GeniusLib)
- [PyPI](https://pypi.org/project/geniuslib/)
- [API Reference](reference.md)
- [Examples](examples.md)
