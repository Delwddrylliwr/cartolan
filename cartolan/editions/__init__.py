'''Game editions and their rule layers.

The editions mirror the rulebooks: Lite Winds is the base game, Shady Routes
adds piracy, Manuscripts and Cultures, and Silk Roads adds Roads and
blind-draw exploration.
'''

from cartolan.editions.lite_winds import GameLiteWinds
from cartolan.editions.shady_routes import GameShadyRoutes
from cartolan.editions.silk_roads import GameSilkRoads

EDITIONS = {
    "LiteWinds": GameLiteWinds,
    "ShadyRoutes": GameShadyRoutes,
    "SilkRoads": GameSilkRoads,
}
