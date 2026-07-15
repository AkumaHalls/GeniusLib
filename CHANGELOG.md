# Changelog — GeniusLib

Todas as mudanças notáveis neste projeto.

---

## [5.2.0] — 2026-07-15

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
