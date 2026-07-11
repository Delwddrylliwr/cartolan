'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'advanced' is deprecated; use cartolan.editions.advanced", DeprecationWarning, stacklevel=2)

from cartolan.editions.advanced import (AdventurerAdvanced, InnAdvanced, CityTileAdvanced,
                                        CardAdvanced)
