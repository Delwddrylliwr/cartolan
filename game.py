from base import Game, TilePile
from beginner import AdventurerBeginner, AgentBeginner, CityTileBeginner
from regular import AdventurerRegular, AgentRegular, CityTileRegular

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
    GAME_WINNING_DIFFERENCE = 15
    
    MAX_ADVENTURERS = 3
    MAX_AGENTS = 5
    
#     WATER_TILES_PER_PLAYER = 30
    NUM_WATER_TILES = 60
    
    VALUE_DISCOVER_WONDER = {"water":1}
    VALUE_TRADE = 1
    VALUE_AGENT_TRADE = 0
    VALUE_FILL_MAP_GAP = [[3 * land_edges + 2 * water_edges for land_edges in range(0,5)] for water_edges in range(0,5)] # These are the rewards for filling a gap with, 0,1,2,3, and 4 adjacent water tiles respectively, for each number of adjacent land tiles
    
    COST_ADVENTURER = GAME_WINNING_DIFFERENCE
    COST_AGENT_EXPLORING = 1
    COST_AGENT_FROM_CITY = 3
    COST_AGENT_REST = 1
    
    EXPLORATION_ATTEMPTS = 1
    MAX_DOWNWIND_MOVES = 4
    MAX_LAND_MOVES = 2
    MAX_UPWIND_MOVES = 2  
    
#     CITY_DOMAIN_RADIUS = MAX_DOWNWIND_MOVES
    CITY_DOMAIN_RADIUS = 0
    MYTHICAL_LATITUDE = 10
    MYTHICAL_LONGITUDE = 0
    
    ADVENTURER_TYPE = AdventurerBeginner
    AGENT_TYPE = AgentBeginner
    CITY_TYPE = CityTileBeginner
    
    def __init__(self, players, movement_rules = 'initial', exploration_rules = 'clockwise'):
        
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
        
        self.exploration_attempts = 0
        self.win_type = None
        self.game_over = False
        
    
    def start_game(self):
        '''Begins the sequence of play, under the assumption that the play area has been set up'''
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
            print(str(player.colour)+ " player's turn, with " +str(len(player.adventurers)) 
                  +" Adventurers, and " +str(player.vault_wealth)+ " wealth in the Vault")
#             if not player.adventurers[0] is None:
#                 adventurer = player.adventurers[0]
#                 adventurer_tile = adventurer.current_tile
#                 print("And their first Adventurer has " +str(adventurer.wealth)+ " wealth, and is on the " +adventurer_tile.tile_back+  " tile at position " +str(adventurer_tile.tile_position.latitude)+ "," +str(adventurer_tile.tile_position.longitude))
            
            # a more sophisticated simulation might need to let players choose their Adventurers' turn order first
            
            # let players move an adventurer so long as it still has valid moves
            for adventurer in player.adventurers:
                if adventurer.turns_moved < self.turn:
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
            self.total_vault_wealth += player.vault_wealth
            for adventurer in player.adventurers:
                self.total_chest_wealth += adventurer.wealth
            # is this player wealthier than the wealthiest player checked so far?
            if player.vault_wealth > self.max_wealth:
                self.wealth_difference = player.vault_wealth - self.max_wealth
                self.max_wealth = player.vault_wealth
                self.winning_player = player
            # if this player is behind in wealth, are they still closer than anyone else?
            elif self.max_wealth - player.vault_wealth < self.wealth_difference:
                    self.wealth_difference = self.max_wealth - player.vault_wealth
        
        if self.wealth_difference > self.GAME_WINNING_DIFFERENCE:
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
                        for adventurer in player.adventurers:
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
    VALUE_DISCOVER_WONDER = {"water":1, "land":1}
    VALUE_ARREST = 5
    VALUE_DISPOSSESS_AGENT = 1
    COST_AGENT_RESTORE = 1
    
    ATTACK_SUCCESS_PROB = 1.0/3.0
    
#     LAND_TILES_PER_PLAYER = 15
    NUM_LAND_TILES = 40
    
    ADVENTURER_TYPE = AdventurerRegular
    AGENT_TYPE = AgentRegular
    CITY_TYPE = CityTileRegular #no extra functionality needed until Advanced mode
        
    def __init__(self, players, movement_rules = 'initial', exploration_rules = 'clockwise'):
        super().__init__(players, movement_rules, exploration_rules)
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
    
    In Advanced mode special equipment cards can be equipped by Adventurers, to confer advantages, while each adventurer will have a character card giving them starting equipment.
    
    Methods:
    __init__ takes a List of Cartolan.Player objects and two Strings
    '''
    COST_BUY_EQUIPMENT = 10
    
    def __init__(self, players, movement_rules = 'initial', exploration_rules = 'clockwise'):
        super().__init__(players, movement_rules = 'initial', exploration_rules = 'clockwise')
