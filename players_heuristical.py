'''Deprecated compatibility shim: import from the cartolan package instead.

The Beginner/Regular/Advanced modes were re-partitioned into the rulebook
editions LiteWinds/ShadyRoutes/SilkRoads; the old names alias their nearest
equivalents.
'''

import warnings

warnings.warn("importing from 'players_heuristical' is deprecated; use cartolan.players.heuristical", DeprecationWarning, stacklevel=2)

from cartolan.players.heuristical import (PlayerExplorer, PlayerTrader, PlayerRouter, PlayerPirate)
PlayerBeginnerExplorer = PlayerRegularExplorer = PlayerAdvancedExplorer = PlayerExplorer
PlayerBeginnerTrader = PlayerRegularTrader = PlayerAdvancedTrader = PlayerTrader
PlayerBeginnerRouter = PlayerRegularRouter = PlayerAdvancedRouter = PlayerRouter
PlayerRegularPirate = PlayerAdvancedPirate = PlayerPirate
