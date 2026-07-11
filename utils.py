'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'utils' is deprecated; use cartolan.core.utils", DeprecationWarning, stacklevel=2)

from cartolan.core.utils import replace_references
