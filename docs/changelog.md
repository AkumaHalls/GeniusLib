# Changelog

All notable changes to GeniusLib.

See [GitHub Releases](https://github.com/AkumaHalls/GeniusLib/releases) for detailed release notes.

## [5.5.0] — 2026-08-17

### Fixed
- **`events.py`** — `_clans`, `_players`, `_wars` bounded at 500 entries with eviction, preventing unbounded memory growth
- **`events.py`** — `close()` now cancels all 7 updater tasks and clears caches and locks
- **`utils.py`** — `HTTPStats` bounded at 1000 keys with eviction of stale entries
- **`utils.py`** — `get_mixed_average()` optimized to avoid temporary flatten list

## [5.4.0] — 2026-07-28

### Fixed
- **BatchThrottler** — `process_time()` replaced with `monotonic()`, resolving `NameError`
- **Type stub** — `events.pyi` imports from `geniuslib` instead of `coc`
- **`__main__.py`** — now calls `cli.main()`, enabling `python -m geniuslib`
- **Duplicate key** — removed duplicate entry in `_MONTH_NAMES_PT`

## [5.3.0] — 2026-07-15

### Added
- **ClashKingAssets** — 3000+ official WebP assets (troops, heroes, spells, equipment, pets, buildings, leagues)
- `asset_url` property on `Troop`, `Hero`, `Pet`, `Equipment`, `Spell` models
- `get_assets_dir()` and `ASSETS_PREFIX` utilities

## [5.1.0] — 2026-06-20

### Added
- **Battle log models** — `BattleLogEntry`, `LeagueHistoryEntry`, `LeagueTierGroup`
- **Battle log analytics** — 15 analysis functions: win rate, streaks, consistency, league progression
- **Army share code decoder** — `decode_army_code()` for in-game army links
- **Season formatter** — `format_season_id()` for human-readable season dates

## [5.0.0] — 2026-05-15

### Changed
- Added missing league endpoints, fixed naming conventions
- 70+ bug fixes across 12 files

## [4.3.0] — 2026-04-10

### Added
- **TH18 support** — full Town Hall 18 in Upgrade Tracker
- New hero: Dragon Duke, New troop: Ruin Witch, New pet: Greedy Raven
- 35/35 API endpoints covered

## [4.2.0] — 2026-03-01

### Added
- **Test suite** — 80 pytest tests
- **Middleware pipeline** — request/response interceptors
- **CLI** — terminal commands for players, clans, wars, raids
- **Upgrade tracker** — cost/time estimation per TH level
- **Exporter** — JSON/CSV export
- **Comparer** — player/clan comparison
- **Sphinx docs** — full API reference

## [4.1.0] — 2026-02-01

### Added
- **Raid analytics** — offensive/defensive breakdown
- **Formatters** — TH, trophies, roles, wars, raids
- **HTTP health stats** — API monitoring
- **Events client** — real-time clan/war events
- **TTL cache** — automatic expiration with background sweep
