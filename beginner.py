'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'beginner' is deprecated; use cartolan.editions.beginner", DeprecationWarning, stacklevel=2)

from cartolan.editions.beginner import (AdventurerBeginner, InnBeginner, CityTileBeginner,
                                        HomeCityTileBeginner, TradePortTile)
