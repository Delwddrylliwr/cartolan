'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com

This file consolidates constants from the core game classes, so that different
variants can be quickly configured.

The variant described here is:
    Name: Light Winds

    Description: Costs and rewards matched to the Cartolan – Light Winds rulebook.
    One Adventurer per player (companions hired at cities scale trade and rest costs).
    First player to bank 100 Vault Silks wins.
'''
class BeginnerConfig:
    NUM_TILES = {"water":60}

    GAME_WINNING_VAULT = 100
    GAME_WINNING_DIFFERENCE = None

    MAX_ADVENTURERS = 1
    MAX_AGENTS = 4
    MAX_COMPANIONS = 3

    COST_COMPANION = 15

    #Values earned
    VALUE_DISCOVER_WONDER = {"water":0}  # no separate bonus for revealing a wonder tile
    VALUE_TRADE = 1                       # per character, on first visit to a port each turn
    VALUE_FILL_MAP_GAP = [[3 * land_edges + 3 * water_edges for land_edges in range(0,5)] for water_edges in range(0,5)]  # +3 per adjoining old tile, up to 9
    VALUE_FILL_GAP_MANUSCRIPTS = [0, 0, 1, 2]  # manuscripts awarded indexed by OTHER adjacents (0-3, excluding moved-from tile)
    VALUE_COMPLETE_MAP = 0                # no bonus for exhausting the tile pile

    #Costs of buying
    COST_ADVENTURER = 15
    COST_AGENT_EXPLORING = 0  # free to hire an Inn on a newly placed tile
    COST_AGENT_FROM_CITY = 5  # 5 Silks to hire an Inn on an existing tile
    COST_AGENT_REST = 1       # per character, when resting at an opponent's Inn
    
    #Agent hiring config
    AGENTS_FROM_CITY = False        # whether adventurers can hire agents remotely from cities
    AGENT_ON_EXISTING = True      # whether adventurers can hire agents on already-explored tiles as they visit

    #Movement config
    MAX_EXPLORATION_ATTEMPTS = 1
    MAX_DOWNWIND_MOVES = 4
    MAX_LAND_MOVES = 2
    MAX_UPWIND_MOVES = 2
    
    #AI behaviour config
    RETURN_CITY_ATTR = "cost_adventurer" #The Adventurer cost attribute against which CPU Adventurers will compare their current Chest wealth, when deciding whether to head back for the Capital
    P_DEVIATE = 0.1 #The probability that CPU players will randomly deviate from their heuristic
    P_BUY_ADVENTURER = 0.5 #The probability that CPU players will spend their Vault wealth on further Adventurers, if they can afford it

class RegularConfig:
    NUM_TILES = {"water":60, "land":30}
    
    NUM_CHEST_TILES = 2
    VALUE_DISCOVER_WONDER = {"water":1, "land":1}
    VALUE_DISCOVER_CITY = 5
    VALUE_ARREST = 5
    VALUE_DISPOSSESS_AGENT = 1
    COST_AGENT_RESTORE = 1
    COST_REFRESH_MAPS = 1

    NUM_TILE_CHOICES = 2
    
    ATTACK_SUCCESS_PROB = 1.0/3.0
    DEFENCE_ROUNDS = 1
    
class AdvancedConfig:
    COST_TECH = 5
    
    NUM_CADRE_CHOICES = 2
    NUM_CHARACTER_CHOICES = 2
    NUM_DISCOVERY_CHOICES = 2
    
    #AI behaviour config
    RETURN_CITY_ATTR = "cost_tech" #The Adventurer cost attribute against which CPU Adventurers will compare their current Chest wealth, when deciding whether to head back for the Capital
    P_BUY_TECH = 0.25 #The probability that CPU players will spend their Vault wealth on Manuscript cards, if they can afford it
    
    #Config relating to card buffs
    VALUE_AGENT_TRADE = 0
    ATTACKS_ABANDON = False
    AGENT_ON_EXISTING = False
    REST_AFTER_PLACING = False
    TRANSFERS_TO_AGENTS = False
    NUM_FREE_RESTS = 0
    
    REST_WITH_ADVENTURERS = False
    TRANSFER_AGENT_EARNINGS = False
    AGENTS_ARREST = False
    CONFISCATE_TREASURE = False
    RESTING_REFURNISHES = False
    POOL_MAPS = False
    RECHOOSE_AT_AGENTS = False
    
    CARD_TYPE_BUFFS = {"+agents":{"agent_on_existing":{"buff_type":"new", "buff_val":True}
                                        , "rest_after_placing":{"buff_type":"new", "buff_val":True}}
                        , "+attack":{"attack_success_prob":{"buff_type":"new", "buff_val":2.0/3.0}} 
                        , "+bank":{"transfers_to_agents":{"buff_type":"new", "buff_val":True}}
                        , "+damage":{"attacks_abandon":{"buff_type":"new", "buff_val":True}}
                        , "+defence":{"defence_rounds":{"buff_type":"boost", "buff_val":1}}
                        , "+downwind":{"max_downwind_moves":{"buff_type":"boost", "buff_val":1}}
                        , "+upwind":{"max_upwind_moves":{"buff_type":"boost", "buff_val":1}
                                            ,"max_land_moves":{"buff_type":"boost", "buff_val":1}}
                        , "+maps":{"num_chest_tiles":{"buff_type":"boost", "buff_val":1}}
                        , "+freerests":{"num_free_rests":{"buff_type":"boost", "buff_val":1}}
                        , "+rewards":{"value_fill_map_gap":{"buff_type":"boost", "buff_val":[[land_edges + water_edges for land_edges in range(0,5)] for water_edges in range(0,5)]}}
                        , "+rests":{"rest_with_adventurers":{"buff_type":"new", "buff_val":True}
                                            # , "num_character_choices":{"buff_type":"new", "buff_val":3}
                                    }
                        , "+transfers":{"transfer_agent_earnings":{"buff_type":"new", "buff_val":True}
                                            # , "num_discovery_choices":{"buff_type":"new", "buff_val":3}
                                        }
                        , "+earning":{"value_agent_trade":{"buff_type":"new", "buff_val":1}
                                            # , "num_discovery_choices":{"buff_type":"new", "buff_val":3}
                                      }
                        , "+arrest":{"agents_arrest":{"buff_type":"new", "buff_val":True}
                                            # , "confiscate_stolen":{"buff_type":"new", "buff_val":True}
                                            # , "num_character_choices":{"buff_type":"new", "buff_val":3}
                                     }
                        , "+refurnish":{"resting_refurnishes":{"buff_type":"new", "buff_val":True}
                                            # , "num_character_choices":{"buff_type":"new", "buff_val":3}
                                        }
                        , "+pool":{"rechoose_at_agents":{"buff_type":"new", "buff_val":True}
                                           # , "pool_maps":{"buff_type":"new", "buff_val":True}
                                           #  , "num_discovery_choices":{"buff_type":"new", "buff_val":3}
                                   }
                        }
    CHARACTER_CARDS = ["adv+agents"
             , "adv+attack"
             , "adv+bank"
             , "adv+damage"
             , "adv+defence", "adv+defence"
             , "adv+downwind", "adv+downwind"
             , "adv+upwind", "adv+upwind"
             , "adv+maps", "adv+maps", "adv+rewards", "adv+freerests"
             ]
    
    MANUSCRIPT_CARDS = ["dis+agents"
             , "dis+attack"
             , "dis+bank"
             , "dis+damage"
             , "dis+defence", "dis+defence"
             , "dis+downwind", "dis+downwind", "dis+downwind", "dis+downwind"
             , "dis+upwind", "dis+upwind", "dis+upwind", "dis+upwind"
             , "dis+maps", "dis+maps", "dis+maps", "dis+maps", "dis+rewards", "dis+freerests"
            ]

    CADRE_CARDS = ["com+rests"
            , "com+transfers"
            , "com+earning"
            , "com+arrest"
            , "com+refurnish"
            , "com+pool"
            ]