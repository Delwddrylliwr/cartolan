'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'game' is deprecated; use cartolan.editions.modes", DeprecationWarning, stacklevel=2)

from cartolan.editions.modes import GameBeginner, GameRegular, GameAdvanced
