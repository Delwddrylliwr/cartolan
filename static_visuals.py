'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'static_visuals' is deprecated; use cartolan.ui.static_visuals", DeprecationWarning, stacklevel=2)

from cartolan.ui.static_visuals import PlayAreaVisualisation, PlayStatsVisualisation
