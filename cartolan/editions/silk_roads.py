'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com

Cartolan - Silk Roads: the roads expansion on Lite Winds / Shady Routes.

Adventurers can build Roads between tiles, letting even tired Adventurers keep
moving along them, and exploration changes: EITHER place a carried Chest map in
any orientation, OR draw blind from the pile matching the crossed edge with
wind-matched placement. Setup starts from the Mythical City alone.

The Road and blind-draw mechanics land with the Silk Roads implementation
stage; this module currently provides the edition chain and rule values.
'''

from cartolan.rules.ruleset import SILK_ROADS
from cartolan.editions.shady_routes import (GameShadyRoutes, AdventurerShadyRoutes,
                                            InnShadyRoutes, CityTileShadyRoutes)


class AdventurerSilkRoads(AdventurerShadyRoutes):
    '''Extends the Shady Routes Adventurer with Road building and blind-draw exploration.'''


class InnSilkRoads(InnShadyRoutes):
    '''An Inn in the Silk Roads expansion, collecting Road tolls as well as rest fees.'''


class CityTileSilkRoads(CityTileShadyRoutes):
    '''City tile for Silk Roads: behaviour lives on GameSilkRoads.'''


class GameSilkRoads(GameShadyRoutes):
    '''Extends the Shady Routes game with Roads and blind-draw exploration.'''
    ADVENTURER_TYPE = AdventurerSilkRoads
    INN_TYPE = InnSilkRoads
    CITY_TYPE = CityTileSilkRoads

    RULESET = SILK_ROADS

    def to_json(self):
        d = super().to_json()
        d["game_mode"] = "SilkRoads"
        return d
