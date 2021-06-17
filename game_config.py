'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com

This file consolidates constants from the core game classes, so that different 
variants can be quickly configured.

The variant described here is: 
    Name: Simplified
    
    Description: After various iterations of the rules, tested with simulations
    physical play, and virtual play, this variation on the rules was reached. 
    It emphasises simplicity of costs and rewards by keeping these to a few low 
    values, perhaps at the expense of balance.
'''
class BeginnerConfig:
    NUM_TILES = {"water":60}
    
    GAME_WINNING_DIFFERENCE = 15
    
    MAX_ADVENTURERS = 4
    MAX_AGENTS = 4
    
    VALUE_DISCOVER_WONDER = {"water":1}
    VALUE_TRADE = 1
    VALUE_AGENT_TRADE = 0
    VALUE_FILL_MAP_GAP = [[2 * land_edges + 2 * water_edges for land_edges in range(0,5)] for water_edges in range(0,5)] # These are the rewards for filling a gap with, 0,1,2,3, and 4 adjacent water tiles respectively, for each number of adjacent land tiles
    VALUE_COMPLETE_MAP = 10
    
    COST_ADVENTURER = 10
    COST_AGENT_EXPLORING = 1
    COST_AGENT_FROM_CITY = 3
    COST_AGENT_REST = 1
    
    MAX_EXPLORATION_ATTEMPTS = 1
    MAX_DOWNWIND_MOVES = 4
    MAX_LAND_MOVES = 2
    MAX_UPWIND_MOVES = 2

class RegularConfig:
    NUM_TILES = {"water":60, "land":40}

    VALUE_DISCOVER_WONDER = {"water":1, "land":1}
    VALUE_DISCOVER_CITY = 5
    VALUE_ARREST = 3
    VALUE_DISPOSSESS_AGENT = 1
    COST_AGENT_RESTORE = 1
    COST_REFRESH_MAPS = 1
    
    ATTACK_SUCCESS_PROB = 1.0/3.0
    DEFENCE_ROUNDS = 1
    
class AdvancedConfig:
    COST_TECH = 5
    NUM_CHEST_TILES = 2
    
    ATTACKS_ABANDON = False
    
    AGENT_ON_EXISTING = False
    TRANSFERS_TO_AGENTS = False
    
    CARD_TYPE_BUFFS = {"+agents":{"agent_on_existing":{"buff_type":"new", "buff_val":True}}
                        , "+attack":{"attack_success_prob":{"buff_type":"new", "buff_val":2.0/3.0}} 
                        , "+bank":{"transfers_to_agents":{"buff_type":"new", "buff_val":True}}
                        , "+damage":{"attacks_abandon":{"buff_type":"new", "buff_val":True}}
                        , "+defence":{"defence_rounds":{"buff_type":"boost", "buff_val":1}}
                        , "+downwind":{"max_downwind_moves":{"buff_type":"boost", "buff_val":1}}
                        , "+upwind":{"max_upwind_moves":{"buff_type":"boost", "buff_val":1}
                                            ,"max_land_moves":{"buff_type":"boost", "buff_val":1}}
                        , "+maps":{"num_chest_tiles":{"buff_type":"boost", "buff_val":1}}
                        }
    CHARACTER_CARDS = ["adv+agents"
             , "adv+attack"
             , "adv+bank"
             , "adv+damage"
             , "adv+defence", "adv+defence"
             , "adv+downwind", "adv+downwind"
             , "adv+upwind", "adv+upwind"
             , "adv+maps", "adv+maps"
             ]
    
    DISCOVERY_CARDS = ["dis+agents"
             , "dis+attack"
             , "dis+bank"
             , "dis+damage"
             , "dis+defence", "dis+defence"
             , "dis+downwind", "dis+downwind", "dis+downwind", "dis+downwind"
             , "dis+upwind", "dis+upwind", "dis+upwind", "dis+upwind"
             , "dis+maps", "dis+maps", "dis+maps", "dis+maps"
            ]