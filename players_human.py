'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'players_human' is deprecated; use cartolan.players.human_local", DeprecationWarning, stacklevel=2)

from cartolan.players.human_local import PlayerLocalHuman
PlayerHuman = PlayerLocalHuman
