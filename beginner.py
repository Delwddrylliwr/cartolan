'''Deprecated compatibility shim: import from the cartolan package instead.

The Beginner/Regular/Advanced modes were re-partitioned into the rulebook
editions LiteWinds/ShadyRoutes/SilkRoads; the old names alias their nearest
equivalents.
'''

import warnings

warnings.warn("importing from 'beginner' is deprecated; use cartolan.editions.lite_winds", DeprecationWarning, stacklevel=2)

from cartolan.editions.lite_winds import (GameLiteWinds, AdventurerLiteWinds, InnLiteWinds,
                                          CityTileLiteWinds, HomeCityTileLiteWinds,
                                          MythicalCityTileLiteWinds, TradePortTile, ModifierCard)
AdventurerBeginner = AdventurerLiteWinds
InnBeginner = InnLiteWinds
CityTileBeginner = CityTileLiteWinds
HomeCityTileBeginner = HomeCityTileLiteWinds
