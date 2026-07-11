'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import os

from cartolan.core.game import Game
from cartolan.core.tiles import Tile, TilePile, WindDirection, TileEdges
from cartolan.editions.beginner import AdventurerBeginner, AgentBeginner, CityTileBeginner, WonderTile, CapitalTileBeginner
from cartolan.editions.regular import AdventurerRegular, AgentRegular, CityTileRegular, DisasterTile, CapitalTileRegular, MythicalTileRegular
from cartolan.editions.advanced import AdventurerAdvanced, AgentAdvanced, CityTileAdvanced, CardAdvanced
import random
import csv
#bring in all the constants from the config file
from cartolan.rules.game_config import BeginnerConfig, RegularConfig, AdvancedConfig

import logging

logger = logging.getLogger(__name__)

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
    TILE_PREFIX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tile_distribution_")
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
        self.game_winning_vault = BeginnerConfig.GAME_WINNING_VAULT
        self.game_winning_difference = BeginnerConfig.GAME_WINNING_DIFFERENCE
        
        self.value_trade = BeginnerConfig.VALUE_TRADE
        self.value_complete_map = BeginnerConfig.VALUE_COMPLETE_MAP
        self.value_discover_wonder = BeginnerConfig.VALUE_DISCOVER_WONDER
        self.value_fill_map_gap = BeginnerConfig.VALUE_FILL_MAP_GAP
        self.value_fill_gap_manuscripts = BeginnerConfig.VALUE_FILL_GAP_MANUSCRIPTS
            
        self.cost_adventurer = BeginnerConfig.COST_ADVENTURER
        self.cost_agent_exploring = BeginnerConfig.COST_AGENT_EXPLORING
        self.cost_agent_from_city = BeginnerConfig.COST_AGENT_FROM_CITY
        self.cost_agent_rest = BeginnerConfig.COST_AGENT_REST
        self.agents_from_city = BeginnerConfig.AGENTS_FROM_CITY
        self.agent_on_existing = BeginnerConfig.AGENT_ON_EXISTING
        self.max_companions = BeginnerConfig.MAX_COMPANIONS
        self.cost_companion = BeginnerConfig.COST_COMPANION
        
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
        
        logger.debug("Built a " +tile_back+ " tile pile with " +str(len(self.tile_piles[tile_back].tiles))+ " tiles, and shuffled it")
    
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
            logger.debug("Have replaced the main tile pile with the discard pile, and shuffled it,"
                  +" so that now there are " +str(len(self.tile_piles))+ " tile piles.")
            #Start a new discard pile
            self.discard_piles.pop(discard_pile.tile_back)
            self.discard_piles[discard_pile.tile_back] = TilePile(discard_pile.tile_back, [])
#             self.discard_piles["water"] = TilePile("water",[])
            discard_pile = self.discard_piles[discard_pile.tile_back]
            logger.debug("Have started a new discard pile, so that now there are "
                 + str(len(self.discard_piles))+ " discard piles.")
            return True
        else:
            return False #both piles are exhausted; the game loop's win check will end the game
    
    def play_round(self):
        '''Carries out the sequence of play for one round of the game'''
        logger.debug("playing round "+str(self.turn)+" with a wealth difference of " +str(self.wealth_difference) 
             +" and a max wealth of " +str(self.max_wealth))
        for player in self.players:
            #some logging
            logger.debug(str(player.name)+ " player's turn, with " +str(len(self.adventurers[player])) 
                  +" Adventurers, and " +str(self.player_wealths[player])+ " wealth in the Vault")
#             if not player.adventurers[0] is None:
#                 adventurer = player.adventurers[0]
#                 adventurer_tile = adventurer.current_tile
#                 logger.debug("And their first Adventurer has " +str(adventurer.wealth)+ " wealth, and is on the " +adventurer_tile.tile_back+  " tile at position " +str(adventurer_tile.tile_position.latitude)+ "," +str(adventurer_tile.tile_position.longitude))
            
            # a more sophisticated simulation might need to let players choose their Adventurers' turn order first
            
            # let players move an adventurer so long as it still has valid moves
            for adventurer in self.adventurers[player]:
                if adventurer.turns_moved < self.turn:
                    adventurer.turn_route = [adventurer.current_tile]
                    player.continue_turn(adventurer)
                    logger.debug("") #to help log readability
                    
                    #check whether this adventurer's turn has won them the game
                    if self.check_win_conditions():
                        return True
        
        #log the numbers of tiles remaining in the game
        for tile_back in self.tile_piles.keys():
            tile_pile = self.tile_piles[tile_back]
            discard_pile = self.discard_piles[tile_back]
            logger.debug(str(len(tile_pile.tiles))+" "+tile_back+" tiles left in the main pile and " +str(len(discard_pile.tiles))+" left in the discard pile")
            logger.debug("") #to help log readability
            
    
    def run_city_visit(self, adventurer, city, abandoned=False):
        '''Initiates all the possible actions when a city is visited

        Arguments:
        Cartolan.Adventurer the Adventurer arriving on the City tile
        Cartolan.CityTile the city being visited
        Boolean abandoned prevents hiring option if the Adventurer has aborted their expedition, making it harder to replace opponents' Agents.
        '''
        #record that this is the latest city visited
        adventurer.latest_city = city

        self.bank_wealth(adventurer)

        if self.winning_condition() is None and not abandoned:
            self.offer_purchases(adventurer, city)

        #End the Adventurer's turn and reset their moves
        adventurer.end_turn()

        return True

    def bank_wealth(self, adventurer):
        '''Offers a player to move wealth from their Adventurer's Chest into their Vault

        Arguments:
        Cartolan.Adventurer the Adventurer that has arrived at the City
        '''
        #check whether and how much the player wants to bank
        wealth_to_bank = adventurer.player.check_deposit(adventurer, adventurer.wealth, self.player_wealths[adventurer.player])
        #record the decision about how much wealth will be banked
        adventurer.banked = wealth_to_bank

        #check if wealth is available and move it from the adventurer's Chest to their Vault
        if adventurer.wealth >= wealth_to_bank:
            adventurer.wealth -= wealth_to_bank
            self.player_wealths[adventurer.player] += wealth_to_bank
            logger.debug(adventurer.player.name+ " has banked " +str(wealth_to_bank)+ " in their Vault")
            return True
        else:
            return False

    def buy_adventurers(self, adventurer, city):
        '''Offers the Player of an Adventurer arriving at the City Tile to buy another Adventurer

        Arguments:
        Cartolan.Adventurer the Adventurer arriving at the City
        Cartolan.CityTile the city where the new Adventurer would be placed
        '''
        #record the decision to buy an adventurer this turn
        adventurer.bought_adventurer += 1

        #keep checking whether the player has enough wealth and wants to buy another adventurer until they refuse
        while (len(self.adventurers[adventurer.player]) < self.MAX_ADVENTURERS
                and self.player_wealths[adventurer.player] >= adventurer.cost_adventurer):
            if adventurer.player.check_buy_adventurer(adventurer):
                #take payment of wealth from their Vault
                self.player_wealths[adventurer.player] -= adventurer.cost_adventurer
                #place another Adventurer for this Player on the City tile
                new_adventurer = self.ADVENTURER_TYPE(self, adventurer.player, city)
                city.move_onto_tile(new_adventurer)
                new_adventurer.turns_moved = self.turn # This new Adventurer will play from the next turn
                logger.debug(adventurer.player.name+ " has bought an adventurer from the city at "
                      +str(city.tile_position.longitude)+","+str(city.tile_position.latitude))
            else:
                return False
        return True

    def buy_agents(self, adventurer, city):
        '''Offers the Player of an Adventurer arriving at the City Tile to buy another Agent and place it on any unclaimed tile

        Arguments:
        Cartolan.Adventurer the Adventurer arriving at the City, if None, then the Player will no longer be prompted
        Cartolan.CityTile the city selling the agent
        '''
        #Record the decision to buy an agent this move
        adventurer.bought_agent += 1

        #keep checking whether the player can afford another Adventurer and wants one until they refuse
        while self.player_wealths[adventurer.player] >= adventurer.cost_agent_from_city:
            tile = adventurer.player.check_buy_agent(adventurer, report="Do you want to place an agent, and where?")
            if not tile:
                return False

            #check whether the tile already has an active Agent
            if not adventurer.check_tile_available(tile):
                continue
            else:
                #pick up an existing Agent from its tile if there are no other agents available
                #otherwise get a new agent
                if len(self.agents[adventurer.player]) >= self.MAX_AGENTS:
                    agent = adventurer.player.check_move_agent(adventurer)
                    if not agent is None:
                        logger.debug(adventurer.player.name+ " is recalling their agent from the tile at "
                          +str(agent.current_tile.tile_position.longitude)
                              +","+str(agent.current_tile.tile_position.latitude))
                        agent.current_tile.move_off_tile(agent)
                        #place the Agent on that tile
                        tile.move_onto_tile(agent)
                    else:
                        logger.debug(adventurer.player.name+ " did not want to move any existing Agents, so moving on.")
                        return False
                else:
                    agent = self.AGENT_TYPE(self, adventurer.player, tile)

                #take payment from the Player's Vault
                self.player_wealths[adventurer.player] -= adventurer.cost_agent_from_city
                logger.debug(adventurer.player.name+ " has hired an agent from the city at "
                  +str(city.tile_position.longitude)+","+str(city.tile_position.latitude)
                     +" and sent them to the tile at "
                     +str(tile.tile_position.longitude)+","+str(tile.tile_position.latitude))
        return True

    def hire_companion(self, adventurer):
        '''Offers the visiting Adventurer the chance to hire a Companion, scaling future trade and rest costs.

        Args:
            adventurer: the visiting Adventurer
        '''
        while (adventurer.num_companions < adventurer.max_companions
               and self.player_wealths[adventurer.player] >= adventurer.cost_companion):
            if adventurer.player.check_hire_companion(adventurer):
                self.player_wealths[adventurer.player] -= adventurer.cost_companion
                adventurer.num_companions += 1
                logger.debug(adventurer.player.name + " hired a Companion (now "
                      + str(adventurer.num_companions) + " companions, "
                      + str(adventurer.num_characters) + " characters total)")
            else:
                return False
        return True

    def offer_purchases(self, adventurer, city):
        '''Manages the sequence of purchasing options for players when their Adventurer reaches a city.

        Args:
            adventurer: the visiting Adventurer
            city: the city being visited
        '''
        self.buy_adventurers(adventurer, city)
        if self.agents_from_city:
            self.buy_agents(adventurer, city)
        self.hire_companion(adventurer)

    def update_standings(self):
        '''Recomputes max_wealth, wealth_difference, and totals from current vault wealth.

        wealth_difference is the gap between the leading player's vault wealth and the
        next-closest player's vault wealth.  It is always updated regardless of which
        win condition is active, so it can be used as a performance metric independently.
        '''
        self.max_wealth = 0
        self.total_vault_wealth = 0
        self.total_chest_wealth = 0
        self.wealth_difference = 0
        for player in self.players:
            self.total_vault_wealth += self.player_wealths[player]
            for adventurer in self.adventurers[player]:
                self.total_chest_wealth += adventurer.wealth
            if self.player_wealths[player] > self.max_wealth:
                self.wealth_difference = self.player_wealths[player] - self.max_wealth
                self.max_wealth = self.player_wealths[player]
                self.winning_player = player
            elif self.max_wealth - self.player_wealths[player] < self.wealth_difference:
                self.wealth_difference = self.max_wealth - self.player_wealths[player]

    def winning_condition(self):
        '''Checks whether any win condition is currently satisfied, without changing game state.

        Returns the win type string, or None. Callers that need to end the game must go
        through check_win_conditions, which only the game loop should invoke.
        '''
        self.update_standings()

        if self.game_winning_vault is not None and self.max_wealth >= self.game_winning_vault:
            return "vault threshold"

        if self.game_winning_difference is not None and self.wealth_difference > self.game_winning_difference:
            return "wealth difference"

        for tile_pile in self.tile_piles.values():
            if not tile_pile.tiles and not self.discard_piles[tile_pile.tile_back].tiles:
                if self.winning_player:
                    return "exhausted " +tile_pile.tile_back+ " tiles"
                return "tiles exhausted but no player banked wealth"

        return None

    def check_win_conditions(self):
        '''Applies any satisfied win condition, ending the game.

        The game loop (play_round) is the only authority that ends the game; game logic
        elsewhere may query winning_condition but must not end the game itself.
        '''
        win_type = self.winning_condition()
        if win_type is None:
            return False
        logger.debug("won by " + win_type)
        self.win_type = win_type
        if win_type == "tiles exhausted but no player banked wealth":
            max_chest_wealth = 0
            for player in self.players:
                for adventurer in self.adventurers[player]:
                    if adventurer.wealth > max_chest_wealth:
                        self.winning_player = player
                        max_chest_wealth = adventurer.wealth
        self.game_over = True
        return True

    def to_json(self):
        play_area = {}
        for lon in self.play_area:
            play_area[str(lon)] = {}
            for lat in self.play_area[lon]:
                play_area[str(lon)][str(lat)] = self.play_area[lon][lat].to_json()
        return {
            "game_mode": "Beginner",
            "turn": self.turn,
            "winning_player": self.winning_player.name if self.winning_player else None,
            "wealth_difference": self.wealth_difference,
            "play_area": play_area,
            "players": [p.name for p in self.players],
            "player_wealths": {p.name: w for p, w in self.player_wealths.items()},
            "adventurers": {p.name: [a.to_json() for a in advs] for p, advs in self.adventurers.items()},
            "agents": {p.name: [a.to_json() for a in agts] for p, agts in self.agents.items()},
            "tile_piles": {back: pile.to_json() for back, pile in self.tile_piles.items()},
            "discard_piles": {back: pile.to_json() for back, pile in self.discard_piles.items()},
            "num_tiles": self.NUM_TILES,
        }


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
        self.num_tile_choices = {}
        for player in players:
            self.num_tile_choices[player] = RegularConfig.NUM_TILE_CHOICES
        
        # a land tile pile is now needed
        self.tile_piles["land"] = TilePile("land",[])
        self.discard_piles["land"] = TilePile("land",[])
        
        # keep track of some information centrally for players' decisions
        self.dropped_wealth = 0
        self.disaster_tiles = []
    
    def run_city_visit(self, adventurer, city, abandoned=False):
        '''Extends to redeem pirates, replenish Chest Tiles, and offer purchase of refreshed chest tiles
        '''
        #Cities provide the Adventurer with civilised clothes so they can be redeemed from piracy
        if adventurer.pirate_token:
            adventurer.pirate_token = False

        #Top up any missing chest tiles from the bags
        adventurer.replenish_chest_tiles()

        return super().run_city_visit(adventurer, city, abandoned)

    def buy_maps(self, adventurer):
        '''Lets the Adventurer choose to refresh all their Chest maps.

        Args:
            adventurer: the visiting Adventurer
        '''
        # Offer the chance to pay and completely swap out chest tiles
        while (self.player_wealths[adventurer.player] >= self.cost_refresh_maps
               and adventurer.player.check_buy_maps(adventurer)):
            self.player_wealths[adventurer.player] -= self.cost_refresh_maps
            adventurer.rechoose_chest_tiles()

    def offer_purchases(self, adventurer, city):
        '''Manages the sequence of purchasing options for players when their Adventurer reaches a city.

        Args:
            adventurer: the visiting Adventurer
            city: the city being visited
        '''
        self.buy_adventurers(adventurer, city)
        self.hire_companion(adventurer)
        if self.agents_from_city:
            self.buy_agents(adventurer, city)
        self.buy_maps(adventurer)

    def winning_condition(self):
        self.dropped_wealth = 0
        for tile in self.disaster_tiles:
            self.dropped_wealth += tile.dropped_wealth

        return super().winning_condition()

    def to_json(self):
        d = super().to_json()
        d["game_mode"] = "Regular"
        return d


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
        
        #Get config variables to act as masters of Adventurer traits in case of modification
        self.card_type_buffs = AdvancedConfig.CARD_TYPE_BUFFS
        
        self.cost_tech = AdvancedConfig.COST_TECH
        
        self.attacks_abandon = AdvancedConfig.ATTACKS_ABANDON
        self.agent_on_existing = AdvancedConfig.AGENT_ON_EXISTING
        self.rest_after_placing = AdvancedConfig.REST_AFTER_PLACING
        self.transfers_to_agents = AdvancedConfig.TRANSFERS_TO_AGENTS
        self.num_free_rests = AdvancedConfig.NUM_FREE_RESTS
        
        #Set up the decks of cards
        self.card_count = 0
        self.cadre_cards = [self.CARD_TYPE(self, card_type) for card_type in AdvancedConfig.CADRE_CARDS] #a copy that can be modified independent of the config file
        self.character_cards = [self.CARD_TYPE(self, card_type) for card_type in AdvancedConfig.CHARACTER_CARDS] #a copy that can be modified independent of the config file
        self.discovery_cards = [self.CARD_TYPE(self, card_type) for card_type in AdvancedConfig.MANUSCRIPT_CARDS] #a copy that can be modified independent of the config file
        
        super().__init__(players, movement_rules='initial', exploration_rules='continuous')
        
    def hire_companion(self, adventurer):
        '''Extends base hire to also draw a character card for the new Companion.
        '''
        companions_before = adventurer.num_companions
        super().hire_companion(adventurer)
        for _ in range(adventurer.num_companions - companions_before):
            adventurer.add_companion_card()
        return adventurer.num_companions > companions_before

    def buy_manuscripts(self, adventurer):
        '''Offers the visiting Adventurer the chance to upgrade themselves.

        Args:
            adventurer: the visiting adventurer
        '''
        logger.debug(
            "Offering " + adventurer.player.name + "'s adventurer the chance to upgrade the Adventurer with a Discovery/Manuscript card")
        while (self.discovery_cards
               and self.player_wealths[adventurer.player] >= self.cost_tech
               and adventurer.player.check_buy_tech(adventurer)):
            logger.debug(adventurer.player.name + "'s has chosen to buy a Manuscript card")
            if adventurer._offer_manuscript_choice():
                self.player_wealths[adventurer.player] -= self.cost_tech

    def buy_maps(self, adventurer):
        '''Extends the parent with the potential for a free refresh of maps.

        Args:
            adventurer: the visiting Adventurer
        '''
        # If they have the perk, let them have one swap of maps for free
        if adventurer.rechoose_at_agents:
            cost_refresh_maps = self.cost_refresh_maps
            self.cost_refresh_maps = 0
            if adventurer.player.check_buy_maps(adventurer):
                adventurer.rechoose_chest_tiles()
            self.cost_refresh_maps = cost_refresh_maps
        super().buy_maps(adventurer)

    def offer_purchases(self, adventurer, city):
        '''Extends to allow rule changes from cards
        '''
        self.buy_adventurers(adventurer, city)
        self.hire_companion(adventurer)
        if self.agents_from_city:
            self.buy_agents(adventurer, city)
        self.buy_manuscripts(adventurer)
        self.buy_maps(adventurer)

    def choose_cadre(self, player):
        '''Lets the player choose a character card from a random subset
        '''
        cadre_cards = self.cadre_cards
        card_options = random.sample(cadre_cards, k=self.num_cadre_choices)
        logger.debug("Offering a selection of Cadre cards:")
        for card in card_options:
            logger.debug(card.card_type)
        self.assigned_cadres[player] = player.choose_card(self.adventurers[player][0], card_options)
        cadre_cards.remove(self.assigned_cadres[player])
        #Take on the changes to rules based on the Character card
        self.assigned_cadres[player].apply_buffs(player) #for all Adventurers and Agents created after this point
        for adventurer in self.adventurers[player]: #For all existing Adventurers
            self.assigned_cadres[player].apply_buffs(adventurer)

    def to_json(self):
        d = super().to_json()
        d["game_mode"] = "Advanced"
        d["assigned_cadres"] = {
            p.name: card.to_json()
            for p, card in self.assigned_cadres.items()
            if card is not None
        }
        return d

#    def __init__(self, players, movement_rules = 'initial', exploration_rules = 'continuous'):
#        super().__init__(players, movement_rules, exploration_rules)
