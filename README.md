# GeniusLib 🧠⚔️

**GeniusLib** é uma biblioteca Python assíncrona para consumir a API oficial do Clash of Clans. Projetada para bots Discord, análises de guerra, capital raids e scouting — com suporte nativo a `war_opted_in` e `clan_capital_contributions`.

## ✨ Funcionalidades

- 🔄 **Totalmente assíncrona** — baseada em `asyncio` + `aiohttp`
- 📡 **Eventos em tempo real** — detecte entrada/saída, doações, ataques, mudanças de cargo e opt in/out
- ⚔️ **Dados de guerra completos** — members, attacks, defenses, scouting, CWL
- 🏰 **Capital Raid** — logs de ataque, defesa, distritos e members
- 🔢 **Tag Encode/Decode** — converta tags base-14 para inteiros e vice-versa
- 📊 **War Analytics** — `new_stars`, `best_attack`, `best_defense`, `missed_attacks`, `cleanup_attacks`
- 🏆 **Calculadoras** — estimativa de troféus, medalhas de raid, troféus lendaliga
- 🕒 **Season Math** — season ID, start/end, league trophies
- 🧩 **Fácil integração** — funciona com `discord.py` e outros frameworks
- 🗃️ **Cache TTL** — cache com expiração automática e sweep de fundo

## 📦 Instalação

```sh
pip install git+https://github.com/AkumaHalls/GeniusLib.git
```

## 🚀 Exemplo rápido

```python
import geniuslib
import asyncio

client = geniuslib.Client()

async def main():
    await client.login('email@exemplo.com', 'senha')

    clan = await client.get_clan('#2PP')
    print(f'Clã: {clan.name} ({clan.tag})')

    for member in clan.members:
        status = '✅' if member.war_opted_in else '❌'
        print(f'{status} {member.name} (TH{member.town_hall})')

    await client.close()

asyncio.run(main())
```

## 🧰 Utilitários

### Tag Encode/Decode

```python
from geniuslib.utils import encode_tag, decode_tag

encode_tag('#2PP')     # 256
decode_tag(256)        # '#2PP'
```

### Season Math

```python
from geniuslib.utils import get_season_id, get_season_start, get_season_end

get_season_id()        # '2026-05'
get_season_start()     # datetime da última segunda-feira do mês às 5am UTC
get_season_end()       # datetime do início da próxima season
```

### War Analytics

```python
from geniuslib.war_analytics import *

new_stars(attack)                     # estrelas ganhas além do melhor ataque anterior
best_attack_on(member)                # melhor ataque do membro
best_defense_on(member)               # melhor defesa contra o membro
count_missed_attacks(war, tag)        # ataques não utilizados
get_cleanup_attacks(war, tag)         # ataques que não renderam estrelas novas
get_war_result(war, tag)              # 'win', 'lose', 'tie' ou 'ongoing'
```

### Raid Analytics (novo em v4.1.0)

```python
from geniuslib.raid_analytics import *

raid_summary(raid_entry)                        # visão completa: ofensivo, defensivo, ataques perdidos, inativos
clan_offensive_stats(raid_entry)                # total loot, ataques, distritos, eficiência
clan_defensive_stats(raid_entry)                # loot perdido, ataques recebidos, distritos perdidos
count_missed_raid_attacks(raid_entry, tag)      # ataques não utilizados no raid
get_inactive_raid_members(raid_entry)           # membros que não atacaram
get_raid_cleanup_attacks(raid_entry, tag)       # ataques em distritos já 100% destruídos
get_wasted_attacks(raid_entry, tag)             # ataques com 0 estrelas e <30% destruição
district_attack_breakdown(district)             # contagem de ataques por estrelas (3/2/1/0)
member_raid_contribution(member)               # % de contribuição do membro no loot total
best_raid_attack(member)                       # melhor ataque do membro (por estrelas + destruição)
average_attack_destruction(member)             # destruição média por ataque
```

### Formatters (novo em v4.1.0)

```python
from geniuslib.formatters import *

format_th(level)                    # "🔑 TH16" com emoji por nível (1-17)
format_trophies(trophies)           # "🏆 5.000" com separador de milhar
format_role(role)                   # "👑 Líder" traduzido (Líder, Colíder, Ancião, Membro)
format_player_brief(player)         # "Nome (#TAG) | 🔑 TH16 | 🏆 5.000"
format_member_brief(member)         # "👑 Nome | 🔑 TH16 | 🏆 5.000"
format_clan_brief(clan)            # "Nome (#TAG) | Nível 10 | 45/50"
format_clan_detailed(clan)         # multi-linha com troféus e VS
format_war_state(state)            # "⚔️ Em guerra" / "❌ Fora de guerra"
format_war_result(war, tag)        # "✅ Vitória" / "❌ Derrota" / "🏈 Empate"
format_war_score(war, tag)         # "45 ⭐ 30"
format_attack(stars, destruction)  # "⭐⭐☆ 85.3%"
format_percentage(value)           # "85.3%"
format_number(value)               # "15.000" (separador de milhar)
format_raid_brief(raid)            # resumo do raid em uma linha
```

### Cache TTL

```python
from geniuslib.utils import TTLCache

cache = TTLCache(ttl=300, maxsize=1000)
cache['chave'] = 'valor'
await cache.start_sweeper(interval=60)  # limpa expirados a cada 60s
cache.stop_sweeper()
```

### Calculadoras

```python
from geniuslib.utils import estimate_raid_medals, estimate_trophy_change, get_league_trophies

get_league_trophies(5200)                         # 300 (troféus lendaliga)
estimate_trophy_change(3, 100, 5000, 4900)         # estimativa de troféus ganhos
estimate_raid_medals(50000, 6, 4, 'Gold I')        # estimativa de medalhas de raid
```

### Atributos de Tropas & Feitiços

Nem todos os atributos estão disponíveis em todos os objetos. Por exemplo, `is_home_base` existe em `Troop`/`Hero`, mas **não** em `Spell`. Prefira usar `village` (disponível em todos):

```python
# ✅ Funciona em Troop, Spell, Hero, Pet, Equipment
t.village == coc.VillageType.home

# ❌ Pode falhar em Spell (não tem is_home_base)
t.is_home_base
```

A biblioteca trata graciosamente unidades desconhecidas (novas tropas/feitiços não incluídos no JSON de dados estáticos), definindo `is_super_troop`, `is_seasonal`, `is_siege_machine` como `False` por padrão.

### Enums Úteis

```python
from geniuslib.enums import VillageType, WarState, WarResult, Role, SeasonResult

WarState.war_ended         # 'warEnded'
VillageType.home           # 'home'
WarResult.win              # 'win'
```

### HTTP Health Stats (novo em v4.1.0)

```python
# Acesse as estatísticas de saúde da API via http.health_stats
stats = client.http.health_stats
# {
#   "total_requests": 1523,
#   "total_errors": 12,
#   "total_rate_limits": 3,
#   "total_retries": 8,
#   "avg_latency_ms": 245.6
# }
```

### Client Events (novo em v4.1.0)

O `EventsClient` agora aceita `raid_clan_tag` configurável (em vez do `#2PP` fixo):

```python
events = EventsClient(client, raid_clan_tag="#ABC123")
```

### Depreciação

`login_with_keys()` agora emite `DeprecationWarning` — use `login()` com email/senha.

---

## 🧠 Por que GeniusLib?

Diferente de outras bibliotecas, a GeniusLib já inclui **todos os campos da API** — sem precisar de `raw_attribute` pra acessar dados como `war_opted_in`. Além disso, oferece utilitários embutidos como calculadoras de troféus/medalhas, analytics de guerra e cache TTL — tudo pronto pra usar.

Foi feita sob medida para o ecossistema **ClashGenius**.

## 📄 Changelog

### v4.1.0 (atual)

- **Raid Analytics** — novo módulo `geniuslib.raid_analytics` com 15 funções para análise de Capital Raids
- **Formatters** — novo módulo `geniuslib.formatters` com 16 funções de formatação para Discord embeds
- **Health Stats** — propriedade `health_stats` em `HTTPClient` com contadores de requests, erros, rate limits, retries e latência
- **Raid Poller corrigido** — `EventsClient._raid_poller()` agora aceita `raid_clan_tag` em vez do `#2PP` hardcoded
- **Depreciação** — `login_with_keys()` agora emite `DeprecationWarning`

### v4.0.0

- Versão inicial baseada em coc.py v4.0.0
- War Analytics, calculadoras, cache TTL, enums

---

## 📄 Licença

MIT
