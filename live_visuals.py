'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'live_visuals' is deprecated; use cartolan.ui.live_visuals / cartolan.ui.web_visuals", DeprecationWarning, stacklevel=2)

from cartolan.ui.live_visuals import GameVisualisation
from cartolan.ui.web_visuals import WebServerVisualisation
