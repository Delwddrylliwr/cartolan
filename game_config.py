'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'game_config' is deprecated; use cartolan.rules.game_config", DeprecationWarning, stacklevel=2)

from cartolan.rules.game_config import BeginnerConfig, RegularConfig, AdvancedConfig
