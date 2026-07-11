'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'players_heuristical' is deprecated; use cartolan.players.heuristical", DeprecationWarning, stacklevel=2)

from cartolan.players.heuristical import (
    PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter,
    PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter, PlayerRegularPirate,
    PlayerAdvancedExplorer, PlayerAdvancedTrader, PlayerAdvancedRouter, PlayerAdvancedPirate)
