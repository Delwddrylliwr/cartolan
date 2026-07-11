'''Headless game construction for tests, mirroring the setup in main_game/main_sim.'''

import contextlib
import io

from base import Tile, WindDirection, TileEdges
from game import GameRegular


def build_game(game_type, players, movement_rules="initial",
               exploration_rules="continuous", mythical_city=True):
    game = game_type(players, movement_rules, exploration_rules)
    game.CITY_TYPE(game, WindDirection(True, True), TileEdges(True, True, True, True),
                   True, True).place_tile(0, 0)
    for lon, lat in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        Tile(game, "water", WindDirection(True, True), TileEdges(True, True, True, True),
             False).place_tile(lon, lat)
    for player in players:
        game.ADVENTURER_TYPE(game, player, game.cities[0])
    game.setup_tile_pile("water")
    if isinstance(game, GameRegular):
        game.setup_tile_pile("land")
        if mythical_city:
            game.tile_piles["land"].tiles.append(
                game.CITY_TYPE(game, WindDirection(True, True),
                               TileEdges(False, False, False, False), False, True))
    return game


def run_to_completion(game):
    with contextlib.redirect_stdout(io.StringIO()):
        game.start_game()
    return game
