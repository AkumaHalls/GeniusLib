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

## 🧠 Por que GeniusLib?

Diferente de outras bibliotecas, a GeniusLib já inclui **todos os campos da API** — sem precisar de `raw_attribute` pra acessar dados como `war_opted_in`. Além disso, oferece utilitários embutidos como calculadoras de troféus/medalhas, analytics de guerra e cache TTL — tudo pronto pra usar.

Foi feita sob medida para o ecossistema **ClashGenius**.

## 📄 Licença

MIT
