# Changelog — GeniusLib

Todas as mudanças notáveis neste projeto.

---

## [5.3.0] — 2026-07-15

### Adicionado
- **`get_assets_dir()`** — nova função em `utils.py` que retorna o caminho absoluto da pasta de assets bundled, facilitando servir os assets em qualquer framework web
- **`ASSETS_PREFIX`** — constante `"/assets"` configurável para o prefixo dos paths de assets
- **`asset_url` agora retorna paths absolutos** — ex: `/assets/troops/barbarian/icon.webp` (antes retornava `assets/troops/barbarian/icon.webp`)
- **Documentação de assets** — seção completa no README com exemplos para aiohttp, FastAPI e Flask

### Alterado
- `asset_path()` agora usa `ASSETS_PREFIX` como base
- Versão: `5.3.0`

---

## [5.5.0] — 2026-08-17

### Corrigido
- **`events.py`** — `_clans`, `_players`, `_wars` agora têm max de 500 entradas com evicção, impedindo crescimento indefinido de objetos do jogo em memória
- **`events.py`** — `close()` agora cancela os 7 updater tasks (`_clan_updater`, `_player_updater`, `_war_updater`, `_maintenance_poller`, `_end_of_season_poller`, `_raid_poller`, `_clan_games_poller`) e limpa todos os caches e locks
- **`utils.py`** — `HTTPStats` agora tem `max_keys=1000` com evicção de chaves antigas, impedindo crescimento indefinido com URLs únicas
- **`utils.py`** — `get_mixed_average()` otimizado para não criar lista flatten temporária, reduzindo pico de memória

### Alterado
- **Versão:** `5.5.0`

---

## [5.4.0] — 2026-07-28

### Corrigido
- **BatchThrottler quebrado** — `process_time()` substituído por `monotonic()` em `http.py:120`, resolvendo `NameError` que impedia o uso do throttler em lote
- **`events.pyi` importando de `coc`** — corrigido para importar de `geniuslib`, tornando o type stub funcional
- **`__main__.py` vazio** — agora chama `cli.main()` via `asyncio.run()`, permitindo `python -m geniuslib`
- **Chave duplicada em `_MONTH_NAMES_PT`** — removida entrada duplicada `7: "Jul"` em `utils.py`
- **Tag de player hardcoded** — `_maintenance_poller` agora usa `self.maintenance_player_tag` configurável (default `#JY9J2Y99`)
- **Slots não utilizados** — removidos `_troop_holder`, `_spell_holder`, `_hero_holder`, `_pet_holder`, `_equipment_holder` de `client.py`
- **Docstring truncada** — `ranke` corrigido para `ranked_cls` com documentação completa
- **`maybe_sort` sombreando `iter` builtin** — reescrita da função para clareza e segurança

### Melhorado
- **Auto-retry para HTTP 429** — em vez de levantar exceção imediata, agora faz até 5 tentativas com backoff exponencial (`(tries+1)*5` segundos)
- **`EventsClient.maintenance_player_tag`** — parâmetro configurável no construtor para o tag usado no poller de manutenção
- **Atualização de versão:** `5.4.0`

### Adicionado
- **ClashKingAssets integrados** — mais de 3000 assets oficiais do Clash of Clans em WebP
  - `geniuslib/static/assets/` com troops, heroes, spells, equipment, pets, buildings, leagues e muito mais
  - Função `asset_path()` em `utils.py` para gerar caminhos relativos
  - Função `clean_asset_name()` em `utils.py` para normalizar nomes
  - Propriedade `asset_url` nos modelos: `Troop`, `Hero`, `Pet`, `Equipment`, `Spell`
  - `pyproject.toml` atualizado para incluir `static/assets/**/*` no pacote

### Alterado
- Versão: `5.2.0`

---

## [5.1.2] — 2025-07-14

### Alterado
- Correções menores e estabilidade
