'''Deprecated compatibility shim: import from the cartolan package instead.

The Beginner/Regular/Advanced modes were re-partitioned into the rulebook
editions LiteWinds/ShadyRoutes/SilkRoads; the old names alias their nearest
equivalents.
'''

import warnings

warnings.warn("importing from 'regular' is deprecated; use cartolan.editions.shady_routes", DeprecationWarning, stacklevel=2)

from cartolan.editions.shady_routes import (GameShadyRoutes, AdventurerShadyRoutes,
                                            InnShadyRoutes, CityTileShadyRoutes,
                                            HomeCityTileShadyRoutes, MythicalCityTileShadyRoutes)
AdventurerRegular = AdventurerShadyRoutes
InnRegular = InnShadyRoutes
CityTileRegular = CityTileShadyRoutes
HomeCityTileRegular = HomeCityTileShadyRoutes
MythicalCityTileRegular = MythicalCityTileShadyRoutes
