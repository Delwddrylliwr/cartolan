'''Canonical game setup for Cartolan.

Replaces the setup_tiles/setup_adventurers/setup_simulation trios that were
duplicated between the local-game and simulation entry points.
'''

import logging

from cartolan.core.tiles import Tile, WindDirection, TileEdges

logger = logging.getLogger(__name__)


def create_game(game_type, players, mythical_city=True, rng=None):
    '''Builds a ready-to-play game: initial tiles, Adventurers, tile piles, and starting maps.

    Arguments:
    game_type: the Game subclass for the edition being played
    players: list of Cartolan.Player
    mythical_city: whether to shuffle the Mythical City into the land pile
    rng: optional seeded random.Random; defaults to the global random module
    '''
    game = game_type(players, rng=rng)

    if getattr(game_type, "SOLO_MYTHICAL_SETUP", False):
        #Silk Roads B.1: place the Mythical City tile alone
        game.CITY_TYPE(game, WindDirection(True, True), TileEdges(False, False, False, False),
                       False, True).place_tile(0, 0)
        mythical_city = False  #the Mythical City is already on the board
    else:
        #place the Home City with a water tile on each of its four sides, sharing the same wind
        game.CITY_TYPE(game, WindDirection(True, True), TileEdges(True, True, True, True),
                       True, True).place_tile(0, 0)
        for longitude, latitude in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            Tile(game, "water", WindDirection(True, True), TileEdges(True, True, True, True),
                 False).place_tile(longitude, latitude)

    #place a starting Adventurer for each player
    for player in players:
        game.ADVENTURER_TYPE(game, player, game.cities[0])
    logger.debug("Placed the Capital tile, surrounding water tiles, and starting Adventurers")

    #build the shuffled tile piles
    game.setup_tile_pile("water")
    if "land" in game.tile_piles:
        game.setup_tile_pile("land")
        if mythical_city:
            #the Mythical City hides among the green-backed maps (Lite Winds C.9)
            game.tile_piles["land"].tiles.append(
                game.CITY_TYPE(game, WindDirection(True, True),
                               TileEdges(False, False, False, False), False, True))
            game.tile_piles["land"].shuffle_tiles(game.rng)

    #deal each Adventurer their starting hand of maps, alternating between the piles
    #(Lite Winds B.6: blue then green; Silk Roads B.6: green then blue)
    deal_order = getattr(game_type, "SETUP_MAP_ORDER", ("water", "land"))
    for player in players:
        for adventurer in game.adventurers[player]:
            for map_num in range(adventurer.num_chest_maps):
                pile = game.tile_piles[deal_order[map_num % len(deal_order)]]
                tile = pile.draw_tile()
                if tile is not None:
                    adventurer.chest_maps.append(tile)
                    adventurer.chest_map_offsets.append(0)

    return game
