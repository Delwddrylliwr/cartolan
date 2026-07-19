'''Single source of truth for rule values, per edition.

A Ruleset is a frozen dataclass: game instances mirror its fields onto mutable
instance attributes at construction (so per-token card modifiers keep working),
but the values themselves are defined only here.

The current variant is Light Winds: costs and rewards matched to the
Cartolan - Light Winds rulebook. First player to bank 100 Vault Silks wins.
'''

from dataclasses import dataclass, field, replace
from typing import Optional

from cartolan.rules.cards_data import (CARD_MODIFIERS, CHARACTER_CARDS,
                                       MANUSCRIPT_CARDS, CULTURE_CARDS)


@dataclass(frozen=True)
class Ruleset:
    edition: str

    #Win conditions
    winning_vault_silks: Optional[int] = 100
    winning_silks_difference: Optional[int] = None

    #Board composition
    num_pile_tiles: dict = field(default_factory=lambda: {"water": 60, "land": 30})

    #Token counts and prices
    max_adventurers: int = 1
    max_inns: int = 4
    max_companions: int = 3
    cost_adventurer: int = 15
    cost_companion: int = 15

    #Values earned
    value_discover_port: dict = field(default_factory=lambda: {"water": 1, "land": 1})
    value_trade: int = 1                # per character, on first visit to a port each turn
    value_fill_map_gap: list = field(default_factory=lambda: [
        [3 * land_edges + 3 * water_edges for land_edges in range(0, 5)]
        for water_edges in range(0, 5)])  # +3 per adjoining old tile, up to 9
    value_fill_gap_manuscripts: list = field(default_factory=lambda: [0, 0, 1, 2])
    value_complete_map: int = 0         # no bonus for exhausting the tile pile

    #Inn hiring
    cost_inn_exploring: int = 0         # free to hire an Inn on a newly placed tile
    cost_inn_from_city: int = 5         # 5 Silks to hire an Inn on an existing tile
    cost_inn_rest: int = 1              # per character, when resting at an opponent's Inn
    inns_from_city: bool = False        # whether Inns can be hired remotely from cities
    inn_on_existing: bool = True        # whether Inns can be hired on already-explored tiles

    #Movement: fresh Adventurers move in any direction, tired ones ride the wind
    fresh_move_budget: int = 2
    tired_move_budget: int = 2

    #--- Shady Routes (piracy) rules ---
    num_chest_maps: int = 3             # Chest map hand capacity (Silk Roads: 2)
    value_discover_city: int = 5
    value_arrest: int = 5
    value_ransack_inn: int = 1
    cost_inn_restore: int = 1
    cost_refresh_maps: int = 1
    #Attacks resolve like a die roll: 1-2 loss, 3-4 draw, 5-6 win; only a WIN succeeds
    attack_die_bonus: int = 0
    defence_die_bonus: int = 0

    #--- Card-modified rules ---
    cost_manuscript: int = 5
    num_culture_choices: int = 2
    num_character_choices: int = 2
    num_manuscript_choices: int = 2
    #Baseline values for traits that cards can modify
    value_inn_trade: int = 0
    rest_after_placing: bool = False
    transfer_inn_earnings: bool = False

    #--- Silk Roads (roads) rules ---
    max_roads: int = 4
    cost_road_new_tile: int = 0         # build a Road on a tile newly laid this move
    cost_road_existing: int = 5         # build a Road between existing tiles
    road_toll_per_character: int = 1    # toll when moving a Road past another player's Inn

    #Card decks and their rule modifiers
    card_modifiers: dict = field(default_factory=lambda: dict(CARD_MODIFIERS))
    character_cards: tuple = CHARACTER_CARDS
    manuscript_cards: tuple = MANUSCRIPT_CARDS
    culture_cards: tuple = CULTURE_CARDS


#Character cards referring to piracy (attack, damage, defence) are removed for
#Lite Winds, per its rulebook's card-filtering note.
LITE_WINDS_CHARACTER_CARDS = tuple(
    card for card in CHARACTER_CARDS
    if card not in ("chr+attack", "chr+damage", "chr+defence"))

LITE_WINDS = Ruleset(
    edition="LiteWinds",
    num_pile_tiles={"water": 60, "land": 30},
    value_discover_port={"water": 1, "land": 1},
    character_cards=LITE_WINDS_CHARACTER_CARDS,
)

SHADY_ROUTES = replace(
    LITE_WINDS,
    edition="ShadyRoutes",
    character_cards=CHARACTER_CARDS,
)

#Road building, blind-draw exploration, and the alternate setup arrive with the
#Silk Roads implementation stage; the edition currently plays as Shady Routes.
SILK_ROADS = replace(
    SHADY_ROUTES,
    edition="SilkRoads",
    num_chest_maps=2,  # Silk Roads B.6: each Adventurer's Chest holds 2 maps
)
