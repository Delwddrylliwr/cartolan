'''Deprecated compatibility shim: import from the cartolan package instead.

The Beginner/Regular/Advanced modes were re-partitioned into the rulebook
editions LiteWinds/ShadyRoutes/SilkRoads; the old names alias their nearest
equivalents.
'''

import warnings

warnings.warn("importing from 'game' is deprecated; use cartolan.editions", DeprecationWarning, stacklevel=2)

from cartolan.editions import GameLiteWinds, GameShadyRoutes, GameSilkRoads
GameBeginner = GameLiteWinds
GameRegular = GameShadyRoutes
GameAdvanced = GameShadyRoutes
