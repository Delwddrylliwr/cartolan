'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'players_ann' is deprecated; use cartolan.players.ann", DeprecationWarning, stacklevel=2)

from cartolan.players.ann import PlayerFeedFwd
