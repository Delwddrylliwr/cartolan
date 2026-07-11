'''Seeded full-game simulations per mode must complete without exception.

These are the characterization safety net for the refactor: they assert only
completion-level invariants that every stage must preserve, not rule details.
'''

import random

import pytest

from cartolan.editions.modes import GameBeginner, GameRegular, GameAdvanced
from cartolan.players.heuristical import (
    PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter,
    PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter, PlayerRegularPirate,
    PlayerAdvancedExplorer, PlayerAdvancedTrader, PlayerAdvancedRouter, PlayerAdvancedPirate,
)
from tests.helpers import build_game, run_to_completion

COLOURS = ["blue", "red", "yellow", "orange"]

MODES = {
    "Beginner": (GameBeginner, [PlayerBeginnerExplorer, PlayerBeginnerTrader,
                                PlayerBeginnerRouter, PlayerBeginnerTrader]),
    "Regular": (GameRegular, [PlayerRegularExplorer, PlayerRegularTrader,
                              PlayerRegularRouter, PlayerRegularPirate]),
    "Advanced": (GameAdvanced, [PlayerAdvancedExplorer, PlayerAdvancedTrader,
                                PlayerAdvancedRouter, PlayerAdvancedPirate]),
}


@pytest.mark.parametrize("mode", list(MODES))
@pytest.mark.parametrize("seed", range(5))
def test_full_game_completes(mode, seed):
    random.seed(seed)
    game_type, player_types = MODES[mode]
    num_players = 2 + (seed % 3)
    players = [player_types[i](COLOURS[i]) for i in range(num_players)]
    game = build_game(game_type, players)

    run_to_completion(game)

    assert game.game_over
    assert 0 < game.turn <= 1000
    assert game.win_type is not None
    for player in players:
        assert game.player_wealths[player] >= 0
    state = game.to_json()
    assert set(state["players"]) == {p.name for p in players}
