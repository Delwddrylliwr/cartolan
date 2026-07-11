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
    num_pile_tiles: dict = field(default_factory=lambda: {"water": 60})

    #Token counts and prices
    max_adventurers: int = 1
    max_inns: int = 4
    max_companions: int = 3
    cost_adventurer: int = 15
    cost_companion: int = 15

    #Values earned
    value_discover_port: dict = field(default_factory=lambda: {"water": 0})
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

    #Movement
    max_exploration_attempts: int = 1
    max_downwind_moves: int = 4
    max_land_moves: int = 2
    max_upwind_moves: int = 2

    #--- Regular-mode (piracy) rules ---
    num_chest_maps: int = 2
    num_tile_choices: int = 2
    value_discover_city: int = 5
    value_arrest: int = 5
    value_ransack_inn: int = 1
    cost_inn_restore: int = 1
    cost_refresh_maps: int = 1
    attack_success_prob: float = 1.0 / 3.0
    defence_rounds: int = 1

    #--- Advanced-mode (cards) rules ---
    cost_manuscript: int = 5
    num_culture_choices: int = 2
    num_character_choices: int = 2
    num_manuscript_choices: int = 2
    #Baseline values for traits that cards can modify
    value_inn_trade: int = 0
    attacks_abandon: bool = False
    rest_after_placing: bool = False
    transfers_to_inns: bool = False
    num_free_rests: int = 0
    rest_with_adventurers: bool = False
    transfer_inn_earnings: bool = False
    inns_arrest: bool = False
    confiscate_silks: bool = False
    resting_refurnishes: bool = False
    pool_maps: bool = False
    rechoose_at_inns: bool = False

    #Card decks and their rule modifiers
    card_modifiers: dict = field(default_factory=lambda: dict(CARD_MODIFIERS))
    character_cards: tuple = CHARACTER_CARDS
    manuscript_cards: tuple = MANUSCRIPT_CARDS
    culture_cards: tuple = CULTURE_CARDS


BEGINNER = Ruleset(edition="Beginner")

REGULAR = replace(
    BEGINNER,
    edition="Regular",
    num_pile_tiles={"water": 60, "land": 30},
    value_discover_port={"water": 1, "land": 1},
)

#Note: the pre-refactor Advanced config declared inn_on_existing=False, but its
#init order meant the Beginner value (True) always won; the effective rule is kept.
ADVANCED = replace(
    REGULAR,
    edition="Advanced",
)
