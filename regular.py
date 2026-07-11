'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'regular' is deprecated; use cartolan.editions.regular", DeprecationWarning, stacklevel=2)

from cartolan.editions.regular import (AdventurerRegular, AgentRegular, CityTileRegular,
                                       CapitalTileRegular, MythicalTileRegular, DisasterTile)
