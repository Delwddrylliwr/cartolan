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
    
    GAME_WINNING_DIFFERENCE = 30
    
    MAX_ADVENTURERS = 3
    MAX_AGENTS = 4
    
    VALUE_DISCOVER_WONDER = {"water":2}
    VALUE_TRADE = 2
    VALUE_AGENT_TRADE = 0
    VALUE_FILL_MAP_GAP = [[6 * land_edges + 4 * water_edges for land_edges in range(0,5)] for water_edges in range(0,5)] # These are the rewards for filling a gap with, 0,1,2,3, and 4 adjacent water tiles respectively, for each number of adjacent land tiles
    
    COST_ADVENTURER = 20
    COST_AGENT_EXPLORING = 2
    COST_AGENT_FROM_CITY = 6
    COST_AGENT_REST = 1
    
    EXPLORATION_ATTEMPTS = 1
    MAX_DOWNWIND_MOVES = 4
    MAX_LAND_MOVES = 2
    MAX_UPWIND_MOVES = 2

class RegularConfig:
    NUM_TILES = {"water":60, "land":40}

    VALUE_DISCOVER_WONDER = {"water":2, "land":2}
    VALUE_ARREST = 10
    VALUE_DISPOSSESS_AGENT = 2
    COST_AGENT_RESTORE = 2
    
    ATTACK_SUCCESS_PROB = 1.0/3.0
    
class AdvancedConfig:
    COST_BUY_EQUIPMENT = 20

