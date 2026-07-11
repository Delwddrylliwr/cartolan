'''Serialization contract: the exact key sets the web client (live_visuals.js) reads.

If a key set changes here, cartolan_web/public_html/live_visuals.js must change in
the same commit, and tests/state_contract.json regenerated to match.
'''

import json
import os
import random

import pytest

from cartolan.editions import GameLiteWinds, GameShadyRoutes, GameSilkRoads
from cartolan.players.heuristical import PlayerExplorer, PlayerTrader
from tests.helpers import build_game, run_to_completion

CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "state_contract.json")

MODES = {
    "LiteWinds": (GameLiteWinds, [PlayerExplorer, PlayerTrader]),
    "ShadyRoutes": (GameShadyRoutes, [PlayerExplorer, PlayerTrader]),
    "SilkRoads": (GameSilkRoads, [PlayerExplorer, PlayerTrader]),
}


@pytest.mark.parametrize("mode", list(MODES))
def test_state_keys_match_contract(mode):
    with open(CONTRACT_PATH) as f:
        contract = json.load(f)[mode]

    game_type, player_types = MODES[mode]
    random.seed(1)
    players = [player_types[0]("blue"), player_types[1]("red")]
    game = run_to_completion(build_game(game_type, players))
    state = json.loads(json.dumps(game.to_json(), default=str))

    assert sorted(state.keys()) == contract["game"]
    adventurer = next(iter(state["adventurers"].values()))[0]
    assert sorted(adventurer.keys()) == contract["adventurer"]
    inns = [i for lst in state["inns"].values() for i in lst]
    if contract["inn"]:
        assert inns, "contract expects inns but none were placed"
        assert sorted(inns[0].keys()) == contract["inn"]
    tile = next(iter(next(iter(state["play_area"].values())).values()))
    assert sorted(tile.keys()) == contract["tile"]
