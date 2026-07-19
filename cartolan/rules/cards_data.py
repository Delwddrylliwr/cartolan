'''Card definitions as data: deck compositions and the rule modifiers each card type applies.

Card types are prefixed by their deck: chr+ (Character), man+ (Manuscript), cul+ (Culture).
Modifier entries are keyed by the rule attribute they change; "new" sets the value,
"boost" adds to it (elementwise for reward matrices).
'''

CARD_MODIFIERS = {
    "+inns": {"rest_after_placing": {"buff_type": "new", "buff_val": True}},
    "+attack": {"attack_die_bonus": {"buff_type": "boost", "buff_val": 1}},
    "+defence": {"defence_die_bonus": {"buff_type": "boost", "buff_val": 1}},
    "+damage": {"value_ransack_inn": {"buff_type": "boost", "buff_val": 1}},
    "+bank": {"cost_companion": {"buff_type": "new", "buff_val": 10}},
    "+downwind": {"tired_move_budget": {"buff_type": "boost", "buff_val": 1}},
    "+upwind": {"fresh_move_budget": {"buff_type": "boost", "buff_val": 1}},
    "+maps": {"num_chest_maps": {"buff_type": "boost", "buff_val": 1}},
    "+freerests": {"cost_inn_from_city": {"buff_type": "new", "buff_val": 2}},
    "+rewards": {"value_fill_map_gap": {"buff_type": "boost",
                                        "buff_val": [[land_edges + water_edges
                                                      for land_edges in range(0, 5)]
                                                     for water_edges in range(0, 5)]}},
    "+rests": {"cost_inn_rest": {"buff_type": "new", "buff_val": 0}},
    "+transfers": {"transfer_inn_earnings": {"buff_type": "new", "buff_val": True}},
    "+earning": {"value_inn_trade": {"buff_type": "new", "buff_val": 1}},
    "+arrest": {"value_arrest": {"buff_type": "boost", "buff_val": 3}},
    "+refurnish": {"cost_inn_restore": {"buff_type": "new", "buff_val": 0}},
    "+pool": {"cost_refresh_maps": {"buff_type": "new", "buff_val": 0}},
}

CHARACTER_CARDS = (
    "chr+inns",
    "chr+attack",
    "chr+bank",
    "chr+damage",
    "chr+defence", "chr+defence",
    "chr+downwind", "chr+downwind",
    "chr+upwind", "chr+upwind",
    "chr+maps", "chr+maps", "chr+rewards", "chr+freerests",
)

MANUSCRIPT_CARDS = (
    "man+inns",
    "man+attack",
    "man+bank",
    "man+damage",
    "man+defence", "man+defence",
    "man+downwind", "man+downwind", "man+downwind", "man+downwind",
    "man+upwind", "man+upwind", "man+upwind", "man+upwind",
    "man+maps", "man+maps", "man+maps", "man+maps", "man+rewards", "man+freerests",
)

CULTURE_CARDS = (
    "cul+rests",
    "cul+transfers",
    "cul+earning",
    "cul+arrest",
    "cul+refurnish",
    "cul+pool",
)
