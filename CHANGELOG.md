# Changelog Ã¢Â€Â” GeniusLib







Todas as mudanÃƒÂ§as notÃƒÂ¡veis neste projeto.







---







## [5.6.0] — 2026-10-07

### Adicionado

- **Suíte de testes de superfície** — `tests/test_async_layers.py`, `tests/test_client_surface.py`, `tests/test_http_layer.py`, `tests/test_game_models.py` e `tests/test_export_and_reports.py` (total: 258 testes)

- **`scripts/download_assets.py`** — novo utilitário que resolve o tarball `geniuslib-assets-<versão>.tar.gz` via GitHub API e o extrai com segurança em `geniuslib/static/assets/`

- **`MANIFEST.in`** — mantém README, LICENÇA e stubs de tipos; exclui os 413 MB de `static/assets/` do sdist (wheel continua com ~1,1 MB)

- **`__all__` explícito** em `geniuslib/__init__.py` — 212 nomes públicos declarados

### Alterado

- **Limpeza total de lint** — `ruff check .` de 535 para 0 erros (E501, E741, F401, F403, W293) e `ruff format` nos arquivos tocados

- **`geniuslib/client.py`** — `inspect.iscoroutinefunction` no lugar de `asyncio.iscoroutinefunction` no dispatch assíncrono (prepara a remoção planejada)

- **`geniuslib/events.py`** — `_prepare_loop()` religa com segurança o event loop armazenado; `MAX_BACKOFF` limita a espera de operações agendadas

- **`.gitignore`** refeito e 50 artefatos rastreados removidos (`.coverage`, `.mypy_cache/`, `ruff.json`)

- **`pyproject.toml`** — `license = "MIT"` no formato PEP 639 (remove aviso de deprecação do setuptools)

### Corrigido

- **Aviso de deprecação `asyncio.iscoroutinefunction`** — removido o uso no dispatch de eventos

- **Extração segura de assets** — `scripts/download_assets.py` valida o host, limita o tamanho do download e verifica o SHA-256 publicado no GitHub antes de extrair (guard anti path-traversal; symlinks/hardlinks recusados)

- **`Retry-After` limitado** — backoff de rate-limit limitado a 60s, impedindo que um header servidor-controlado trave o client inteiro

- **Redirects de assets revalidados** — `get_data_from_url` segue redirecionamentos manualmente, revalidando cada hop contra a allowlist de hosts (anti-SSRF)

## [5.3.0] Ã¢Â€Â” 2026-07-15







### Adicionado



- **`get_assets_dir()`** Ã¢Â€Â” nova funÃƒÂ§ÃƒÂ£o em `utils.py` que retorna o caminho absoluto da pasta de assets bundled, facilitando servir os assets em qualquer framework web



- **`ASSETS_PREFIX`** Ã¢Â€Â” constante `"/assets"` configurÃƒÂ¡vel para o prefixo dos paths de assets



- **`asset_url` agora retorna paths absolutos** Ã¢Â€Â” ex: `/assets/troops/barbarian/icon.webp` (antes retornava `assets/troops/barbarian/icon.webp`)



- **DocumentaÃƒÂ§ÃƒÂ£o de assets** Ã¢Â€Â” seÃƒÂ§ÃƒÂ£o completa no README com exemplos para aiohttp, FastAPI e Flask







### Alterado



- `asset_path()` agora usa `ASSETS_PREFIX` como base



- VersÃƒÂ£o: `5.3.0`







---







## [5.5.0] Ã¢Â€Â” 2026-08-17







### Adicionado



- **PyPI publicado** Ã¢Â€Â” `pip install geniuslib` agora disponÃƒÂ­vel em https://pypi.org/project/geniuslib/5.5.0/



- **Assets no GitHub Release** Ã¢Â€Â” pacote `geniuslib-assets-5.5.0.tar.gz` com todas as imagens de jogo (~385 MB) disponÃƒÂ­vel como release asset (PyPI limita a 100 MB)



- **MkDocs** Ã¢Â€Â” documentaÃƒÂ§ÃƒÂ£o completa com Material theme em `mkdocs.yml` e pÃƒÂ¡ginas em `docs/`



- **Exemplos novos** Ã¢Â€Â” `examples/batch_fetch.py` (fetch paralelo com ClanIterator/PlayerIterator) e `examples/web_dashboard.py` (dashboard aiohttp)



- **`pyproject.toml`** Ã¢Â€Â” metadata completa para PyPI (classifiers, project URLs, optional deps, ruff config)







### Corrigido



- **`events.py`** Ã¢Â€Â” `_clans`, `_players`, `_wars` agora tÃƒÂªm max de 500 entradas com evicÃƒÂ§ÃƒÂ£o, impedindo crescimento indefinido de objetos do jogo em memÃƒÂ³ria



- **`events.py`** Ã¢Â€Â” `close()` agora cancela os 7 updater tasks (`_clan_updater`, `_player_updater`, `_war_updater`, `_maintenance_poller`, `_end_of_season_poller`, `_raid_poller`, `_clan_games_poller`) e limpa todos os caches e locks



- **`utils.py`** Ã¢Â€Â” `HTTPStats` agora tem `max_keys=1000` com evicÃƒÂ§ÃƒÂ£o de chaves antigas, impedindo crescimento indefinido com URLs ÃƒÂºnicas



- **`utils.py`** Ã¢Â€Â” `get_mixed_average()` otimizado para nÃƒÂ£o criar lista flatten temporÃƒÂ¡ria, reduzindo pico de memÃƒÂ³ria







### Alterado



- **`pyproject.toml`** Ã¢Â€Â” `include-package-data` alterado para `false`, assets excluÃƒÂ­dos do pacote PyPI (mantidos apenas no GitHub)



- **`README.md`** Ã¢Â€Â” reescrito com badges, tabela de comparaÃƒÂ§ÃƒÂ£o vs coc.py, quickstart, seÃƒÂ§ÃƒÂ£o de features



- **VersÃƒÂ£o:** `5.5.0`







---







## [5.4.0] Ã¢Â€Â” 2026-07-28







### Corrigido



- **BatchThrottler quebrado** Ã¢Â€Â” `process_time()` substituÃƒÂ­do por `monotonic()` em `http.py:120`, resolvendo `NameError` que impedia o uso do throttler em lote



- **`events.pyi` importando de `coc`** Ã¢Â€Â” corrigido para importar de `geniuslib`, tornando o type stub funcional



- **`__main__.py` vazio** Ã¢Â€Â” agora chama `cli.main()` via `asyncio.run()`, permitindo `python -m geniuslib`



- **Chave duplicada em `_MONTH_NAMES_PT`** Ã¢Â€Â” removida entrada duplicada `7: "Jul"` em `utils.py`



- **Tag de player hardcoded** Ã¢Â€Â” `_maintenance_poller` agora usa `self.maintenance_player_tag` configurÃƒÂ¡vel (default `#JY9J2Y99`)



- **Slots nÃƒÂ£o utilizados** Ã¢Â€Â” removidos `_troop_holder`, `_spell_holder`, `_hero_holder`, `_pet_holder`, `_equipment_holder` de `client.py`



- **Docstring truncada** Ã¢Â€Â” `ranke` corrigido para `ranked_cls` com documentaÃƒÂ§ÃƒÂ£o completa



- **`maybe_sort` sombreando `iter` builtin** Ã¢Â€Â” reescrita da funÃƒÂ§ÃƒÂ£o para clareza e seguranÃƒÂ§a







### Melhorado



- **Auto-retry para HTTP 429** Ã¢Â€Â” em vez de levantar exceÃƒÂ§ÃƒÂ£o imediata, agora faz atÃƒÂ© 5 tentativas com backoff exponencial (`(tries+1)*5` segundos)



- **`EventsClient.maintenance_player_tag`** Ã¢Â€Â” parÃƒÂ¢metro configurÃƒÂ¡vel no construtor para o tag usado no poller de manutenÃƒÂ§ÃƒÂ£o



- **AtualizaÃƒÂ§ÃƒÂ£o de versÃƒÂ£o:** `5.4.0`







### Adicionado



- **ClashKingAssets integrados** Ã¢Â€Â” mais de 3000 assets oficiais do Clash of Clans em WebP



  - `geniuslib/static/assets/` com troops, heroes, spells, equipment, pets, buildings, leagues e muito mais



  - FunÃƒÂ§ÃƒÂ£o `asset_path()` em `utils.py` para gerar caminhos relativos



  - FunÃƒÂ§ÃƒÂ£o `clean_asset_name()` em `utils.py` para normalizar nomes



  - Propriedade `asset_url` nos modelos: `Troop`, `Hero`, `Pet`, `Equipment`, `Spell`



  - `pyproject.toml` atualizado para incluir `static/assets/**/*` no pacote







### Alterado



- VersÃƒÂ£o: `5.2.0`







---







## [5.1.2] Ã¢Â€Â” 2025-07-14







### Alterado



- CorreÃƒÂ§ÃƒÂµes menores e estabilidade



---







## [5.5.4] Â— 2026-10-03







### Alterado



- Sincronizado __version__ em geniuslib/__init__.py com pyproject.toml (5.5.4)



- Adicionados feitiÃ§os sazonais faltantes em SPELL_ORDER: "Santa's Surprise", "Bag of Frostmites"







