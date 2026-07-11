'''Deprecated compatibility shim: import from the cartolan package instead.'''

import warnings

warnings.warn("importing from 'base' is deprecated; use cartolan.core / cartolan.players.base", DeprecationWarning, stacklevel=2)

from cartolan.core.game import Game
from cartolan.core.tokens import Token, Adventurer, Inn
from cartolan.core.tiles import TilePosition, WindDirection, TileEdges, Tile, TilePile, CityTile
from cartolan.core.cards import Card
from cartolan.players.base import Player
