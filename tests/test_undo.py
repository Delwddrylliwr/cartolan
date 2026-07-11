'''Canary for the save/restore (undo) machinery.

The deepcopy + replace_references undo subsystem is the most fragile part of
the codebase and is not touched until the final refactor stage; this test
pins down the behaviour it must keep: a save/mutate/restore round-trip
returns the game to an identical serialized state while preserving the
object identity of adventurers (which UIs and players hold references to).
'''

import contextlib
import io
import json
import random

from cartolan.editions.modes import GameRegular
from cartolan.players.heuristical import PlayerRegularExplorer, PlayerRegularTrader
from tests.helpers import build_game


def snapshot(game):
    return json.dumps(game.to_json(), sort_keys=True, default=str)


def silent():
    return contextlib.redirect_stdout(io.StringIO())


def make_game(seed):
    random.seed(seed)
    players = [PlayerRegularExplorer("blue"), PlayerRegularTrader("red")]
    return build_game(GameRegular, players), players


def test_save_restore_round_trip_from_setup():
    game, players = make_game(123)
    with silent():
        game.save()
    before = snapshot(game)
    adventurer = game.adventurers[players[0]][0]

    adventurer.silks += 7
    game.vault_silks[players[0]] += 11
    with silent():
        tile = game.tile_piles["water"].tiles.pop()
        tile.place_tile(0, 2)
        game.restore()

    assert snapshot(game) == before
    # UIs and players hold direct references to adventurers across an undo
    assert game.adventurers[players[0]][0] is adventurer
    assert adventurer.silks == 0
    assert game.vault_silks[players[0]] == 0


def test_save_restore_round_trip_mid_game():
    game, players = make_game(321)
    with silent():
        game.game_started = True
        for _ in range(3):
            game.turn += 1
            game.play_round()
        game.save()
    before = snapshot(game)
    adventurer = game.adventurers[players[0]][0]

    with silent():
        game.turn += 1
        game.play_round()
        game.restore()

    assert snapshot(game) == before
    assert game.adventurers[players[0]][0] is adventurer
