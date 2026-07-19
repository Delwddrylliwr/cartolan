'''Canary for the save/restore (undo) machinery.

A save/mutate/restore round-trip must return the game to an identical
serialized state while preserving the object identity of the game, its
players, and its adventurers (which UIs and players hold references to).
The backup survives a restore, so repeated restores return to the same
save point.
'''

import contextlib
import io
import json
import random

from cartolan.editions import GameShadyRoutes
from cartolan.players.heuristical import PlayerExplorer, PlayerTrader
from tests.helpers import build_game


def snapshot(game):
    return json.dumps(game.to_json(), sort_keys=True, default=str)


def silent():
    return contextlib.redirect_stdout(io.StringIO())


def make_game(seed):
    random.seed(seed)
    players = [PlayerExplorer("blue"), PlayerTrader("red")]
    return build_game(GameShadyRoutes, players), players


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
    # players keep their identity too, including as dict keys
    assert game.players[0] is players[0]
    assert players[0] in game.vault_silks
    # the restored adventurer points into the restored play area
    tile = adventurer.current_tile
    assert game.play_area[tile.tile_position.longitude][tile.tile_position.latitude] is tile

    # the backup survives a restore: mutate and restore again
    adventurer.silks += 5
    with silent():
        game.restore()
    assert snapshot(game) == before
    assert adventurer.silks == 0


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
