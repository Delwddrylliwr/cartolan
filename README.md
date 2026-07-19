# Cartolan - Trade Winds

A digital implementation of the board game [Cartolan - Trade Winds](https://docs.google.com/document/d/1LuAe_V7xUiPdksBD5XowbvPdK9tO_SFwECsiqNrPXLY/edit), for playtesting over the web and for running large numbers of simulated games with virtual players.

The code follows the three official guidebooks, and each edition is playable as written:

- **Lite Winds** — the base game: trade-wind movement (fresh/tired/exhausted), exploration by placing carried Chest maps, Trade Ports, Inns, Cities, Character cards and Companions. Win by banking 100 Silks in your Vault.
- **Shady Routes** — the piracy expansion: attacks resolved by die roll, pirate tokens, ransacking and restoring Inns, arrests, Manuscript cards and Culture cards.
- **Silk Roads** — the roads expansion: buildable Roads that even tired Adventurers can follow (with tolls past other players' Inns), blind-draw exploration placed by the trade winds, and an alternate setup starting from the Mythical City alone.

The expansions stack: `GameSilkRoads` includes the Shady Routes rules, matching the guidebooks' "expanding on" framing.

## Package layout

```
cartolan/
  core/       game loop, tiles, tokens, movement engine, roads, setup, events
  rules/      Ruleset dataclass (single source of rule values) + card data
  editions/   lite_winds.py, shady_routes.py, silk_roads.py
  players/    Player interface, heuristic CPUs, local human (pygame), ANN (stale)
  ui/         pygame and web visualisations
  apps/       local_game and simulation entry points
  server/     WebSocket game server
  data/       tile distribution CSVs
cartolan_web/ JS browser client
tests/        pytest suite keyed to guidebook clauses
```

## Getting started

Install the package (Python 3.9+):

```
pip install -e .            # core: simulations only
pip install -e .[ui]        # + pygame/matplotlib for local play and stats
pip install -e .[dev]       # + pytest
```

### Play in a browser

The server also needs `SimpleWebSocketServer` (its old sdist can fail to build under modern setuptools; installing from source or vendoring the module works).

```
python web_server.py        # or: python -m cartolan.server.websocket_server
```

Then serve `cartolan_web/public_html/` over HTTP and open `index.html`. The client prompts for the edition (LiteWinds, ShadyRoutes or SilkRoads), the number of local human players, and the number of CPU players.

### Play locally with pygame

```
python main_game.py
```

### Run simulations

```
python main_sim.py
```

Heuristic virtual players (`PlayerExplorer`, `PlayerTrader`, `PlayerRouter`, `PlayerPirate` in `cartolan/players/heuristical.py`) play any edition. Programmatic use:

```python
import random
from cartolan.core.setup import create_game
from cartolan.editions import GameSilkRoads
from cartolan.players.heuristical import PlayerExplorer, PlayerPirate

random.seed(42)
game = create_game(GameSilkRoads, [PlayerExplorer("red"), PlayerPirate("blue")])
game.start_game()
```

## Configuring rules

All rule values live in the frozen `Ruleset` dataclass in `cartolan/rules/ruleset.py`, with one instance per edition (`LITE_WINDS`, `SHADY_ROUTES`, `SILK_ROADS`). Variants are made with `dataclasses.replace(...)` on those instances; card effects are declared as data in `cartolan/rules/cards_data.py`.

## Running the tests

```
pytest
```

`tests/test_rulebook.py` pins mechanics to specific guidebook clauses; `tests/test_smoke.py` runs seeded full games per edition; `tests/test_undo.py` covers save/restore; `tests/test_serialization.py` pins the JSON keys the web client relies on.

## Stale components

- `cartolan/players/ann.py` and the weights in `ann_models/` predate the rulebook alignment: they import and run, but were trained against the old rules and need retraining (see `ann_models/STALE.md`).
- The Jupyter notebook in the root predates the refactor and its cells reference the old module layout.
- `attic/` holds unwired legacy code kept for reference.

## Contributing

If you'd like to contribute to this project then please contact Tom Wilkinson @ delwddrylliwr@gmail.com

## Authors

* **Tom Wilkinson** - *Creator of the Cartolan board game, and developer of this project.*

## License

This project is licensed under the CC-BY-NC, Creative Commons Attribution Non-Commercial license.

## Acknowledgments

* Thanks to the [podsixnet tutorial](https://www.raywenderlich.com/2613-multiplayer-game-programming-for-teens-with-python-part-2) of Julian Meyer.
* Thanks to the [deep Q-learning tutorial](https://keras.io/examples/rl/deep_q_network_breakout/) of Jacob Chapman and Mathias Lechner
