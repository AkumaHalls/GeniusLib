# Quick Start

## Installation

```sh
pip install geniuslib
```

Or from source:

```sh
pip install git+https://github.com/AkumaHalls/GeniusLib.git
```

## Authentication

GeniusLib supports two authentication methods:

### Email/Password (recommended)

This method automatically manages API keys and handles rate limiting.

```python
import geniuslib, asyncio

async def main():
    client = geniuslib.Client()
    await client.login("your-email@example.com", "your-password")

    # Use the client...
    clan = await client.get_clan("#2PP")
    print(clan.name)

    await client.close()

asyncio.run(main())
```

### API Token

Use this if you have a developer API key from [developer.clashofclans.com](https://developer.clashofclans.com/).

```python
await client.login_with_tokens("your-api-token")
```

## Context Manager

GeniusLib clients support the `async with` pattern for automatic cleanup:

```python
async with geniuslib.Client() as client:
    await client.login("email", "password")
    player = await client.get_player("#TAG")
    print(player.name, player.town_hall)
# Client is automatically closed
```

## Fetching Data

### Single requests

```python
player = await client.get_player("#PQU80VUJ")
clan = await client.get_clan("#2PP")
war = await client.get_current_war("#2PP")
logs = await client.get_raid_log("#2PP", limit=5)
battlelog = await client.get_player_battlelog("#PQU80VUJ")
```

### Parallel requests

```python
import asyncio

# Fetch multiple players at once
players = await asyncio.gather(*[
    client.get_player(tag) for tag in ["#P1", "#P2", "#P3"]
])
```

### Batch iterators

```python
from geniuslib import ClanIterator

async for clan in ClanIterator(client, ["#TAG1", "#TAG2", "#TAG3"]):
    print(clan.name, clan.level)
```

## Error Handling

```python
import geniuslib

try:
    player = await client.get_player("#INVALID")
except geniuslib.NotFound:
    print("Player not found")
except geniuslib.PrivateWarLog:
    print("War log is private")
except geniuslib.Maintenance:
    print("API is under maintenance")
except geniuslib.HTTPException as e:
    print(f"HTTP error: {e.status}")
```

## Next Steps

- [Examples](examples.md) — ready-to-run scripts
- [API Reference](reference.md) — complete API documentation
