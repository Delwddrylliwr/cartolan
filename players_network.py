'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'players_network' is deprecated; use cartolan.players.network", DeprecationWarning, stacklevel=2)

from cartolan.players.network import PlayerHuman
