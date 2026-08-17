# Examples

Ready-to-run example scripts in the [`examples/`](https://github.com/AkumaHalls/GeniusLib/tree/main/examples) folder.

## Discord Bot

Full-featured Discord bot with slash commands and real-time events.

```sh
export DISCORD_TOKEN="your-token"
export COC_EMAIL="your-email"
export COC_PASSWORD="your-password"
python examples/discord_bot.py
```

Features:
- `/player <tag>` — player info with embed
- `/clan <tag>` — clan info with embed
- `/war <tag>` — current war status
- `/raid <tag>` — latest raid summary
- `/compare <tag1> <tag2>` — side-by-side comparison
- Real-time clan events (join/leave/donations)

## War Analyzer

Generates a detailed war performance report.

```sh
export COC_EMAIL="your-email"
export COC_PASSWORD="your-password"
python examples/war_analyzer.py
```

Output includes:
- War result and score
- Top attackers by stars
- Best defenses
- Missed attacks
- Cleanup (wasted) attacks

## Raid Reporter

Capital Raid report with offensive and defensive stats.

```sh
python examples/raid_reporter.py
```

Output includes:
- Total loot stolen and lost
- Attacks used vs missed
- Inactive members
- Wasted attacks (0 stars, <30% destruction)
- Top attacker

## Export Data

Export player or clan data to JSON or CSV.

```sh
python examples/export_data.py "#TAG" --format json
python examples/export_data.py "#TAG" --type clan --format csv
```

## Batch Fetch

Fetch multiple clans and players in parallel.

```sh
python examples/batch_fetch.py
```

Demonstrates:
- `ClanIterator` for batch clan lookups
- `PlayerIterator` for batch player lookups
- `asyncio.gather` for mixed parallel requests

## Web Dashboard

Minimal web dashboard with aiohttp.

```sh
export CLAN_TAG="#2PP"
python examples/web_dashboard.py
# Visit http://localhost:8080
```

Displays:
- Clan stats (wins, losses, points)
- Current war status
- Recent raid summaries
