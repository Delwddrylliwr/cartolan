'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

from base import Game, TilePile
from beginner import AdventurerBeginner, AgentBeginner, CityTileBeginner, WonderTile, CapitalTileBeginner
from regular import AdventurerRegular, AgentRegular, CityTileRegular, DisasterTile, CapitalTileRegular, MythicalTileRegular
from advanced import AdventurerAdvanced, AgentAdvanced, CityTileAdvanced, CardAdvanced
from base import Tile, WindDirection, TileEdges
import random
import csv
#bring in all the constants from the config file
from game_config import BeginnerConfig, RegularConfig, AdvancedConfig

class GameBeginner(Game):
    '''Executes the sequence of play for the Beginner mode of the board game Cartolan - Trade Winds
    
    Beginner mode involves only water tiles being placed as Adventurer tokens are moved around the play area 
    collecting wealth from discovering and trading at wonder tiles. 
    
    Agent tokens can be placed as tiles are visited to confer wealth and movement bonuses to Adventurers.
    
    Methods:
    __init__ takes a List of Cartolan.Players and two Strings
    start_game
    refresh_pile takes two Cartolan.TilePile objects
    play_round
    check_win_conditions
    '''
    #Set non-configurable class level constants
    TILE_PREFIX = "tile_distribution_"
    TILE_EXT = ".csv"
    TILE_TYPE_COLS = {"wonder":1}
    TILE_TYPES = {"plain":Tile, "capital":CapitalTileBeginner, "wonder":WonderTile}
    ADVENTURER_TYPE = AdventurerBeginner
    AGENT_TYPE = AgentBeginner
    CITY_TYPE = CityTileBeginner
    
    #Inherit class level constants from config file
    NUM_TILES = BeginnerConfig.NUM_TILES
    
    MAX_ADVENTURERS = BeginnerConfig.MAX_ADVENTURERS
    MAX_AGENTS = BeginnerConfig.MAX_AGENTS
    
    
    def __init__(self, players, movement_rules = 'initial', exploration_rules = 'continuous'):
        
        super().__init__(players)
        
        if movement_rules in ["initial", "budgetted"]:
            self.movement_rules = movement_rules
        else: raise Exception("Invalid movement rules specified")
        
        if exploration_rules in ["clockwise", "continuous"]:
            self.exploration_rules = exploration_rules
        else: raise Exception("Invalid exploration rules specfied")
        
        self.cities = []

        self.tile_piles = {"water":TilePile("water",[])}
        self.discard_piles = {"water":TilePile("water",[])}
        
        #Inherit instance level constants from config
        self.game_winning_difference = BeginnerConfig.GAME_WINNING_DIFFERENCE
        
        self.value_trade = BeginnerConfig.VALUE_TRADE
        self.value_complete_map = BeginnerConfig.VALUE_COMPLETE_MAP
        self.value_discover_wonder = BeginnerConfig.VALUE_DISCOVER_WONDER
        self.value_fill_map_gap = BeginnerConfig.VALUE_FILL_MAP_GAP
            
        self.cost_adventurer = BeginnerConfig.COST_ADVENTURER
        self.cost_agent_exploring = BeginnerConfig.COST_AGENT_EXPLORING
        self.cost_agent_from_city = BeginnerConfig.COST_AGENT_FROM_CITY
        self.cost_agent_rest = BeginnerConfig.COST_AGENT_REST
        
        self.max_exploration_attempts = BeginnerConfig.MAX_EXPLORATION_ATTEMPTS
        self.max_downwind_moves = BeginnerConfig.MAX_DOWNWIND_MOVES
        self.max_land_moves = BeginnerConfig.MAX_LAND_MOVES
        self.max_upwind_moves = BeginnerConfig.MAX_UPWIND_MOVES
        
        self.exploration_attempts = 0
        self.win_type = None
        self.game_over = False
    
    def setup_tile_pile(self, tile_back):
        '''Part of game setup for Cartolan, this creates a tile of shuffled water-backed tiles ready for play
        
        Arguments:
        tile_back a string designating the type of tile and so its distribution of edge combinations
        '''
        total_distribution = []
        special_distributions = {} # for wonder/disaster
        for tile_type in self.TILE_TYPE_COLS:
            special_distributions[tile_type] = []
        
        tile_filename = self.TILE_PREFIX + tile_back + self.TILE_EXT
        with open(tile_filename) as csvfile:
            readCSV = csv.reader(csvfile)
            for row in readCSV:
                total_distribution.append(int(row[0]))
                for tile_type in self.TILE_TYPE_COLS:
                    special_distributions[tile_type].append(int(row[self.TILE_TYPE_COLS[tile_type]]))
        
        #construct the tile deck
        row_count = 0
        tiles = []
        for uc_water in [True, False]:
            for ua_water in [True, False]:
                for dc_water in [True, False]:
                    for da_water in [True, False]:
                        #for this combination of tile edges create tiles of each special type and plain ones
                        special_tile_num = 0
                        for tile_type in special_distributions:
                            for tile_num in range(0, int(special_distributions[tile_type][row_count])):
                                wind_direction = WindDirection(north = True, east = True)
                                tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
                                tiles.append(self.TILE_TYPES[tile_type](self, tile_back, wind_direction, tile_edges))
                                special_tile_num += 1
                        for tile_num in range(0, int(total_distribution[row_count]) - special_tile_num):
                            wind_direction = WindDirection(north = True, east = True)
                            tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
                            tiles.append(Tile(self, tile_back, wind_direction, tile_edges, False))
                        row_count += 1
        
        #draw a suitable number of tiles from the deck for a pile
    #     num_tiles = len(players)*game.WATER_TILES_PER_PLAYER
        num_tiles = self.NUM_TILES[tile_back]
        tile_pile = self.tile_piles[tile_back]
        for tile in random.sample(tiles, num_tiles):
            tile_pile.add_tile(tile)
        
        tile_pile.shuffle_tiles()
        
        print("Built a " +tile_back+ " tile pile with " +str(len(self.tile_piles[tile_back].tiles))+ " tiles, and shuffled it")
    
    def start_game(self):
        '''Begins the sequence of play, under the assumption that the play area has been set up'''
        self.game_started = True
        self.game_over = False
        while not self.game_over:
            self.turn += 1
            self.game_over = self.play_round()
        
        #report game conclusion to caller
        return True
    
    
    def refresh_pile(self, tile_pile, discard_pile):
        '''Swaps the discard pile of tiles for the active pile, shuffling it
        
        Arguments:
        Cartolan.TilePile the pile to replace
        Cartolan.TilePile the discard pile to put into play
        '''
        #check whether the discard pile is empty too
        if discard_pile.tiles:
            self.tile_piles.pop(tile_pile.tile_back)
            self.tile_piles[tile_pile.tile_back] = discard_pile
            tile_pile = self.tile_piles[tile_pile.tile_back]
            discard_pile.shuffle_tiles()
            print("Have replaced the main tile pile with the discard pile, and shuffled it,"
                  +" so that now there are " +str(len(self.tile_piles))+ " tile piles.")
            #Start a new discard pile
            self.discard_piles.pop(discard_pile.tile_back)
            self.discard_piles[discard_pile.tile_back] = TilePile(discard_pile.tile_back, [])
#             self.discard_piles["water"] = TilePile("water",[])
            discard_pile = self.discard_piles[discard_pile.tile_back]
            print("Have started a new discard pile, so that now there are "
                 + str(len(self.discard_piles))+ " discard piles.")
            return True
        else:
            self.game_over = self.check_win_conditions() #try and exit here if so
            return False
    
    def play_round(self):
        '''Carries out the sequence of play for one round of the game'''
        print("playing round "+str(self.turn)+" with a wealth difference of " +str(self.wealth_difference) 
             +" and a max wealth of " +str(self.max_wealth))
        for player in self.players:
            #some logging
            print(str(player.name)+ " player's turn, with " +str(len(self.adventurers[player])) 
                  +" Adventurers, and " +str(self.player_wealths[player])+ " wealth in the Vault")
#             if not player.adventurers[0] is None:
#                 adventurer = player.adventurers[0]
#                 adventurer_tile = adventurer.current_tile
#                 print("And their first Adventurer has " +str(adventurer.wealth)+ " wealth, and is on the " +adventurer_tile.tile_back+  " tile at position " +str(adventurer_tile.tile_position.latitude)+ "," +str(adventurer_tile.tile_position.longitude))
            
            # a more sophisticated simulation might need to let players choose their Adventurers' turn order first
            
            # let players move an adventurer so long as it still has valid moves
            for adventurer in self.adventurers[player]:
                if adventurer.turns_moved < self.turn:
                    adventurer.turn_route = [adventurer.current_tile]
                    player.continue_turn(adventurer)
                    print() #to help log readability
                    
                    #check whether this adventurer's turn has won them the game
                    if self.check_win_conditions():
                        return True
        
        #log the numbers of tiles remaining in the game
        for tile_back in self.tile_piles.keys():
            tile_pile = self.tile_piles[tile_back]
            discard_pile = self.discard_piles[tile_back]
            print(str(len(tile_pile.tiles))+" "+tile_back+" tiles left in the main pile and " +str(len(discard_pile.tiles))+" left in the discard pile")
            print() #to help log readability
            
    
    def check_win_conditions(self):
        '''Checks whether the win conditions have been satisfied so that the game should end'''
        #the end conditions for a game are one player having a certain margin more wealth in their Vault, or one of the tile piles being emptied
        self.max_wealth = 0
        self.total_vault_wealth = 0
        self.total_chest_wealth = 0
        self.wealth_difference = 0
        for player in self.players:
            self.total_vault_wealth += self.player_wealths[player]
            for adventurer in self.adventurers[player]:
                self.total_chest_wealth += adventurer.wealth
            # is this player wealthier than the wealthiest player checked so far?
            if self.player_wealths[player] > self.max_wealth:
                self.wealth_difference = self.player_wealths[player] - self.max_wealth
                self.max_wealth = self.player_wealths[player]
                self.winning_player = player
            # if this player is behind in wealth, are they still closer than anyone else?
            elif self.max_wealth - self.player_wealths[player] < self.wealth_difference:
                    self.wealth_difference = self.max_wealth - self.player_wealths[player]
        
        if self.wealth_difference > self.game_winning_difference:
            print("won by wealth difference")
            self.win_type = "wealth difference"
            self.game_over = True
            return True

        for tile_pile in self.tile_piles.values():
            if not tile_pile.tiles and not self.discard_piles[tile_pile.tile_back].tiles:
                print("won by running out of tiles")
                if self.winning_player:
                    self.win_type = "exhausted " +tile_pile.tile_back+ " tiles"
                else:
                    self.win_type = "tiles exhausted but no player banked wealth"
                    max_chest_wealth = 0
                    for player in self.players:
                        for adventurer in self.adventurers[player]:
                            if adventurer.wealth > max_chest_wealth:
                                self.winning_player = player
                                max_chest_wealth = adventurer.wealth
                self.game_over = True
                return True
        
        return False


class GameRegular(GameBeginner):
    '''Extends the GameBeginner class to include extra features of the Regular mode of Cartolan - Trade Winds
    
    In Regular mode agents can be dispossessed and restored through Adventurers committing piracy, with rewards and costs.
    
    Methods:
    __init__ takes a List of Cartolan.Player objects and two Strings
    check_win_conditions
    '''
    #Set class constants that can't be configured
    TILE_TYPE_COLS = {"wonder":1, "disaster":2}
    TILE_TYPES = {"plain":Tile, "capital":CapitalTileRegular, "mythical":MythicalTileRegular, "wonder":WonderTile, "disaster":DisasterTile}    
    ADVENTURER_TYPE = AdventurerRegular
    AGENT_TYPE = AgentRegular
    CITY_TYPE = CityTileRegular #no extra functionality needed until Advanced mode

    #Inherit configurable class constants from config file
    NUM_TILES = RegularConfig.NUM_TILES

    def __init__(self, players, movement_rules = 'initial', exploration_rules = 'continuous'):
        super().__init__(players, movement_rules, exploration_rules)
        #Inherit some instance constants from the config file
        self.value_discover_wonder = RegularConfig.VALUE_DISCOVER_WONDER
        self.value_discover_city = RegularConfig.VALUE_DISCOVER_CITY
        self.value_arrest = RegularConfig.VALUE_ARREST
        self.value_dispossess_agent = RegularConfig.VALUE_DISPOSSESS_AGENT
        self.cost_agent_restore = RegularConfig.COST_AGENT_RESTORE
        self.cost_refresh_maps = RegularConfig.COST_REFRESH_MAPS
        
        self.attack_success_prob = RegularConfig.ATTACK_SUCCESS_PROB
        self.defence_rounds = RegularConfig.DEFENCE_ROUNDS
        
        #Chest tiles will now be carried
        self.num_chest_tiles = RegularConfig.NUM_CHEST_TILES
        
        # a land tile pile is now needed
        self.tile_piles["land"] = TilePile("land",[])
        self.discard_piles["land"] = TilePile("land",[])
        
        # keep track of some information centrally for players' decisions
        self.dropped_wealth = 0
        self.disaster_tiles = []
    
    def check_win_conditions(self):
        self.dropped_wealth = 0
        for tile in self.disaster_tiles:
            self.dropped_wealth += tile.dropped_wealth
        
        return super().check_win_conditions()


class GameAdvanced(GameRegular):
    '''Extends the GameRegular class to include extra features of the Adventurer mode of Cartolan - Trade Winds
    
    Advanced mode allows each Adventurer to carry a small complement of Map Tiles.
    In future, Advanced mode will have tech cards held by Adventurers, to confer advantages, while each adventurer will have a character card giving them starting equipment.
    
    Methods:
    __init__ takes a List of Cartolan.Player objects and two Strings
    '''
    ADVENTURER_TYPE = AdventurerAdvanced
    AGENT_TYPE = AgentAdvanced
    CITY_TYPE = CityTileAdvanced #no extra functionality needed until Advanced mode
    CARD_TYPE = CardAdvanced

#    COST_BUY_TECH = 5
    def __init__(self, players, movement_rules='initial', exploration_rules='continuous'):
        #Get game level config variables
        self.num_cadre_choices = AdvancedConfig.NUM_CADRE_CHOICES
        #Get player level config variables
        self.num_character_choices = {}
        self.num_discovery_choices = {}
        self.value_agent_trade = {}
        self.rest_with_adventurers = {}
        self.transfer_agent_earnings = {}
        self.agents_arrest = {}
        self.confiscate_treasure = {}
        self.resting_refurnishes = {}
        self.pool_maps = {}
        self.rechoose_at_agents = {}
        #And a placeholder for players to choose a Cadre/Company
        self.assigned_cadres = {}
        for player in players:
            self.num_character_choices[player] = AdvancedConfig.NUM_CHARACTER_CHOICES
            self.num_discovery_choices[player] = AdvancedConfig.NUM_DISCOVERY_CHOICES
            self.value_agent_trade[player] = AdvancedConfig.VALUE_AGENT_TRADE
            self.rest_with_adventurers[player] = AdvancedConfig.REST_WITH_ADVENTURERS 
            self.transfer_agent_earnings[player] = AdvancedConfig.TRANSFER_AGENT_EARNINGS
            self.agents_arrest[player] = AdvancedConfig.AGENTS_ARREST
            self.confiscate_treasure[player] = AdvancedConfig.CONFISCATE_TREASURE
            self.resting_refurnishes[player] = AdvancedConfig.RESTING_REFURNISHES
            self.pool_maps[player] = AdvancedConfig.POOL_MAPS
            self.rechoose_at_agents[player] = AdvancedConfig.RECHOOSE_AT_AGENTS
            #And a placeholder for players to choose a Cadre/Company
            self.assigned_cadres[player] = None
        
        #Get config variables to act as masters in case of modification
        self.card_type_buffs = AdvancedConfig.CARD_TYPE_BUFFS
        
        self.cost_tech = AdvancedConfig.COST_TECH
        
        self.attacks_abandon = AdvancedConfig.ATTACKS_ABANDON
        self.agent_on_existing = AdvancedConfig.AGENT_ON_EXISTING
        self.rest_after_placing = AdvancedConfig.REST_AFTER_PLACING
        self.transfers_to_agents = AdvancedConfig.TRANSFERS_TO_AGENTS
        
        #Set up the decks of cards
        self.cadre_cards = [self.CARD_TYPE(self, card_type) for card_type in AdvancedConfig.CADRE_CARDS] #a copy that can be modified independent of the config file
        self.character_cards = [self.CARD_TYPE(self, card_type) for card_type in AdvancedConfig.CHARACTER_CARDS] #a copy that can be modified independent of the config file
        self.discovery_cards = [self.CARD_TYPE(self, card_type) for card_type in AdvancedConfig.MANUSCRIPT_CARDS] #a copy that can be modified independent of the config file
        
        super().__init__(players, movement_rules='initial', exploration_rules='continuous')
        
    def choose_cadre(self, player):
        '''Lets the player choose a character card from a random subset
        '''
        cadre_cards = self.cadre_cards
        card_options = random.sample(cadre_cards, k=self.num_cadre_choices)
        print("Offering a selection of Cadre cards:")
        for card in card_options:
            print(card.card_type)
        self.assigned_cadres[player] = player.choose_card(self.adventurers[player][0], card_options)
        cadre_cards.remove(self.assigned_cadres[player])
        #Take on the changes to rules based on the Character card
        self.assigned_cadres[player].apply_buffs(player) #for all Adventurers and Agents created after this point
        for adventurer in self.adventurers[player]: #For all existing Adventurers
            self.assigned_cadres[player].apply_buffs(adventurer)
        
#    def __init__(self, players, movement_rules = 'initial', exploration_rules = 'continuous'):
#        super().__init__(players, movement_rules, exploration_rules)
