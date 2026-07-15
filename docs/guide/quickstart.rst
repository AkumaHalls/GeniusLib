Quickstart
==========

Instalação
----------

.. code-block:: bash

   pip install geniuslib

Uso básico
----------

.. code-block:: python

   import asyncio
   from geniuslib import Client

   async def main():
       async with Client() as client:
           await client.login("email@example.com", "password")
           player = await client.get_player("#TAG")

           print(f"{player.name} — TH{player.town_hall}")
           print(f"Trofeus: {player.trophies}")
           print(f"Cla: {player.clan.name if player.clan else 'Nenhum'}")

   asyncio.run(main())

Login com variáveis de ambiente
-------------------------------

.. code-block:: bash

   export COC_EMAIL="seu_email@exemplo.com"
   export COC_PASSWORD="sua_senha"

.. code-block:: python

   import os
   from geniuslib import Client

   async def main():
       async with Client() as client:
           await client.login(os.environ["COC_EMAIL"], os.environ["COC_PASSWORD"])
           # ...
