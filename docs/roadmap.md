# Roadmap — GeniusLib

> **Versão atual:** v5.5.0
> **Repositório:** https://github.com/AkumaHalls/GeniusLib

---

## Análise Concorrencial

| Projeto | Stars | Status | Diferenciais deles |
|---------|-------|--------|-------------------|
| **coc.py** (mathsman5133) | 151 | v4.0.0 (Dez/2025) | Original, mais consolidado |
| **clashy.py** (ClashKingInc) | 5 | v26.6.2 (Ativo) | CI/CD, docs no ClashKing, 1.586 commits |
| **clash-of-clans-python-api** | 0 | v0.2.5 | Minimalista, PyPI |

## O que GeniusLib já tem de único

- ✅ **3000+ assets bundlados** — ícones WebP oficiais no pacote
- ✅ **War/Raid/BattleLog Analytics** — análise embedada (new_stars, best_attack, etc.)
- ✅ **Upgrade Tracker** — custo/tempo por TH
- ✅ **Middleware Pipeline** — interceptação request/response
- ✅ **CLI completo** — player, clan, war, raid, search, export, compare
- ✅ **Formatadores prontos para Discord** — emojis, TH, cargos, ligas
- ✅ **Cache TTL com sweeper de fundo**
- ✅ **Português 🇧🇷** — documentação e mensagens em PT-BR

---

## 🚀 Features Diferenciais Propostas

### 1. Pydantic v2 Models (Alta Prioridade)
**Problema:** Modelos atuais são dataclasses manuais sem serialização.
**Solução:** Adicionar modelos Pydantic v2 opcionais para `Player`, `Clan`, `War`, etc.
**Diferencial:** Geração de JSON Schema automática, validação de tipos, `model_dump()`/`model_validate()` — nenhum concorrente tem.

### 2. RoyaleAPI Proxy Integration (Média Prioridade)
**Problema:** Rate-limit da API oficial é agressivo (30 req/s por chave).
**Solução:** Suporte nativo ao proxy gratuito RoyaleAPI (usado pelo clashy.py alternativo).
**Diferencial:** Aumenta throughput em ~10x sem custo.

### 3. Discord.py Cogs Pré-construídos (Alta Prioridade)
**Problema:** Usuários do ClashGenius precisam reimplementar comandos básicos.
**Solução:** Pacote `geniuslib.ext.discord` com cogs prontos: `/player`, `/clan`, `/war`, `/raid`, `/compare`.
**Diferencial:** Integração plug-and-play com discord.py — zero concorrente oferece.

### 4. War Prediction / ML (Média Prioridade)
**Problema:** Nenhuma lib oferece análise preditiva.
**Solução:** Módulo `geniuslib.predictor` que estima chance de vitória baseado em TH, heróis, estrelas históricas.
**Diferencial:** Feature única no mercado — war outcome prediction.

### 5. Rich CLI / TUI (Baixa Prioridade)
**Problema:** CLI atual é texto plano.
**Solução:** Usar `rich`/`textual` para tabelas coloridas, spinners, dashboards interativos.
**Diferencial:** Visual profissional — `textual` permite TUI real-time.

### 6. Database Auto-Sync (Média Prioridade)
**Problema:** Dados da API não persistem entre execuções.
**Solução:** Módulo `geniuslib.store` com sync automático para SQLite/PostgreSQL via SQLAlchemy.
**Diferencial:** Cache permanente + consultas SQL — útil para bots que precisam de histórico.

### 7. Python 3.14 Async Features (Alta Prioridade)
**Problema:** Código usa `asyncio.gather` e loops manuais.
**Solução:** Migrar para `TaskGroup`, `ExceptionGroup`, `async with asyncio.TaskGroup()`.
**Diferencial:** Código mais limpo, tratamento de erros superior — disponível desde Python 3.11.

### 8. Webhook Push System (Média Prioridade)
**Problema:** EventsClient é pull-based (poller a cada 10s).
**Solução:** Webhooks HTTP reais — registre uma URL e receba POSTs quando algo mudar.
**Diferencial:** Única lib com webhook server embutido.

### 9. Endpoint Field Selection (Baixa Prioridade)
**Problema:** API sempre retorna objetos completos (~30KB por player).
**Solução:** `client.get_player("#TAG", fields=["name", "trophies", "town_hall"])` — filtra no cliente.
**Diferencial:** Economia de memória/banda — útil para bots com muitos jogadores.

---

## 🎯 Roadmap Sugerido (Prioritário)

| Fase | Feature | Esforço | Impacto |
|------|---------|---------|---------|
| **1** | Pydantic v2 models | 2-3 dias | ⭐⭐⭐⭐⭐ |
| **2** | Discord.py cogs | 1-2 dias | ⭐⭐⭐⭐⭐ |
| **3** | TaskGroup + Python 3.14 | 1 dia | ⭐⭐⭐⭐ |
| **4** | RoyaleAPI proxy | 2 dias | ⭐⭐⭐⭐ |
| **5** | Database auto-sync | 3 dias | ⭐⭐⭐ |
| **6** | War prediction | 3-5 dias | ⭐⭐⭐⭐⭐ |
| **7** | Rich CLI / TUI | 2 dias | ⭐⭐⭐ |
| **8** | Webhook push | 2 dias | ⭐⭐⭐ |
| **9** | Field selection | 1 dia | ⭐⭐ |

---

> Roadmap gerado em 28/07/2026.
