'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import random
import uuid

class Game:
    '''A template for maintaining a record of the game state in different modes of Cartolan.
    
    Methods:
    __init__ taking a list full of Player objects
    establish_turn_order taking no arguments
    '''
    MAX_PLAYERS = 4
    MIN_PLAYERS = 2
    
    def __init__(self, players):
        if len(players) in range(self.MIN_PLAYERS, self.MAX_PLAYERS +1):
            self.players = players
#            self.establish_turn_order()
        else: raise Exception("Game created with an invalid number of players: should be 2-4, but was " +str(len(players)))
        
        #register this game with each of the players
        self.game_id = uuid.uuid4()
        for player in players:
            player.join_game(self)
        
        self.tile_piles = {}
        self.play_area = {}
        self.player_wealths = {}
        self.adventurers = {}
        self.agents = {}
        for player in players:
            self.player_wealths[player] = 0
            self.adventurers[player] = []
            self.agents[player] = []
        
        self.game_started = False #Keep track of whether the game is running
        self.turn = 0
        
        #some information to keep track of centrally for players to make decisions
        self.winning_player = None
        self.max_wealth = 0
        self.total_vault_wealth =  0
        self.total_chest_wealth = 0
        self.wealth_difference = 0
        self.num_failed_explorations = 0
#         self.agent_network = None #placeholder to keep track of which routes are possible in a single turn
#         self.agent_distances = [[]] #placeholder to keep track of where trade routes could be built
#         self.most_lucrative_route_value = 0
#         self.most_lucrative_route_player = None

        
#    def establish_turn_order(self):
#        '''Randomises the order in which Player objects will be activated'''
#        random.shuffle(self.players)

#@TODO allow players to join multiple games, through maintaining a game-indexed dict of wealth/adventurers/agents/game-specific stats. This will help allow AI players to learn across multiple games in parallel
class Player:
    '''A template for actual Players responding to play in a Game of Cartolan.
    
    Methods:
    __init__ taking a colour string that should correspond to a pyplot colour
    
    Interfaces:
    continue_turn; continue_move 
    '''
    def __init__(self, colour = "red"):
        self.colour = colour
        self.games = {}
    
    def join_game(self, game):
        '''Establishes dict to retain strategic info for each game
        '''
        self.games[game.game_id] = {"game":game
                  , "locations_to_avoid":[] #tiles to remember to avoid for artificial players @TODO move this into game-specific dict entry
                  , "attack_history":[] #a record of where attacks have taken place, to support visualisation @TODO move this into the visual
                  }
    
    def connect_gui(self, game_vis):
        '''Associates a particular gui with a game
        '''
        game = game_vis.game
        self.games[game.game_id]["game_vis"] = game_vis
    
    def continue_move(self, adventurer):
        '''placeholder for responding to the state of the game by choosing movement for an adventurer'''
        pass
        
    def continue_turn(self, adventurer):
        '''placeholder for responding to the state of the game'''
        pass

class Token:
    '''A template for actual tokens used in play.
    
    Methods:
    __init__ taking a Game and a Player and a Tile from the Cartolan module
    
    Interfaces:
    None
    '''
    def __init__(self, game, player, current_tile):
        self.game = game
        self.player = player
        self.current_tile = current_tile
        
        self.wealth = 0
        self.route = []
        
        current_tile.move_onto_tile(self)

class Card:
    '''A template for cards that will modify other objects with buffs
    '''
    def __init__(self, game, card_type):
        self.game = game
        self.card_type = card_type
        self.buffs = None
        self.card_id = card_type+str(random.random())
        
    def __hash__(self):
        return hash(self.card_id)
    
    def __eq__(self, other):
        if isinstance(other, Card):
            return self.card_id == other.card_id
        else: return False
        
    def __ne__(self, other):
        if isinstance(other, Card):
            return not self.card_id == other.card_id
        else: return True

class Adventurer(Token):
    '''A template for actual Adventurer tokens used in different game modes.
    
    Methods:
    __init__ taking a Game and a Player and a Tile from the Cartolan module
    
    Interfaces:
    move; explore; discover; trade; rest; 
    '''
    def __init__(self, game, player, current_tile):
        super().__init__(game, player, current_tile)
        game.adventurers[player].append(self)
        
        self.turns_moved = 0
    
    def move(self, compass_point):
        '''placeholder for movement'''
        pass
        
    def explore(self, longitude, latitude):
        '''placeholder for exploration'''
        pass
        
    def discover(self, tile):
        '''placeholder for discovering new wealth'''
        pass
        
    def trade(self, tile):
        '''placeholder for trading on a suitable tile'''
        pass
        
    def rest(self, agent):
        '''placeholder for resting with an agent'''
        pass
    
    def attack(self, token):
        '''placeholder for attacking other tokens in Regular and Advanced modes'''
        pass

class Agent(Token):
    '''A template for actual Agent tokens used in different game modes.
    
    Methods:
    __init__ taking a Game and a Player and a Tile from the Cartolan module
    
    Interfaces:
    give_rest; manage_trade 
    '''
    def __init__(self, game, player, current_tile):
        super().__init__(game, player, current_tile)
        game.agents[player].append(self)
        
    def give_rest(self, adventurer):
        '''placeholder for resting adventurers'''
        pass
    
    def manage_trade(self, adventurer):
        '''placeholder for agents involved in trade on a tile'''
        pass


class TilePosition: 
    '''keeps track of the coordinates of a Tile entity in a PlayArea for the game Cartolan'''
    def __init__(self, longitude = None, latitude = None):
        '''keep track of the tile's position in two ints'''
        self.longitude = longitude
        self.latitude = latitude


class WindDirection:
    '''keeps track of the direction of the diagonal wind arrow on a Tile entity in the game Cartolan'''
    def __init__(self, north = True, east = True):
        '''keep track of the wind direction with two bits'''
        self.north = north
        self.east = east

        
class TileEdges:
    '''keeps track of whether each of the edges are land or water, relative to wind direction, for a Tile entity in the game Cartolan'''
    def __init__(self, uc_water = True, ua_water = True, dc_water = True, da_water = True):
        ''' keep track of the edges of the tile in four bits'''
        self.upwind_clock_water = uc_water
        self.upwind_anti_water = ua_water
        self.downwind_clock_water = dc_water
        self.downwind_anti_water = da_water


class Tile:
    '''represents the tiles used in the game Cartolan, procedurally generating a play area and affecting movement
    
    Methods:
    __init__ taking Game, WindDirection, and TileEdges objects from Cartolan module, and a tile_back string
    place_tile taking two int arguments for coordinates
    '''
    def __init__(self, game
                 , tile_back = "water"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(True,True,True,True)
                , is_wonder = False):
        self.game = game
        self.tile_back = tile_back
        self.wind_direction = wind_direction
        self.tile_edges = tile_edges
        self.tile_position = TilePosition(None, None)
        self.is_wonder = is_wonder
        
        self.adventurers = [] # to keep track of the Adventurer tokens on a tile at any point
        self.agent = None # there can only be one Agent token on a given tile
        self.dropped_wealth = 0 # to keep track of wealth dropped when returning abruptly to a City
        self.tile_id = tile_back+str(wind_direction.north)+str(wind_direction.east)+str(tile_edges.upwind_clock_water)+str(tile_edges.upwind_anti_water)+str(tile_edges.downwind_clock_water) + str(tile_edges.downwind_anti_water)+str(random.random())
        
    def __hash__(self):
        return hash(self.tile_id)
    
    def __eq__(self, other):
        if isinstance(other, Tile):
            return self.tile_id == other.tile_id
        else: return False
        
    def __ne__(self, other):
        if isinstance(other, Tile):
            return not self.tile_id == other.tile_id
        else: return True
    
    def place_tile(self, longitude, latitude):
        '''records the location of a Tile object in the PlayArea of a Cartolan game
        
        key arguments:
        int longitude
        int latitude
        '''
        print("Placing tile " +str(longitude)+", "+str(latitude))
        play_area = self.game.play_area
        if play_area.get(longitude) is None:
            play_area[longitude] = {latitude:self}
            self.tile_position = TilePosition(longitude, latitude)
        elif play_area.get(longitude).get(latitude) is None: 
            play_area[longitude][latitude] = self
            self.tile_position = TilePosition(longitude, latitude)
        else: raise Exception("Tried to place a tile on top of another")
    
    def rotate_tile_clock(self):
        '''Replicates the change in direction of the wind arrow on a tile from rotating it
        
        Rotates the tie sequentially: NE->SE, SE->SW, SW->NW, NW->NE
        '''
        if self.wind_direction.north and self.wind_direction.east:
            self.wind_direction.north = False
        elif not self.wind_direction.north and self.wind_direction.east:
            self.wind_direction.east = False
        elif not self.wind_direction.north and not self.wind_direction.east:
            self.wind_direction.north = True
        elif self.wind_direction.north and not self.wind_direction.east:
            self.wind_direction.east = True
        else: raise Exception("Tile orientations have become confused")
    
    def rotate_tile_anti(self):
        '''Replicates the change in direction of the wind arrow on a tile from rotating it
        
        Rotates the tie sequentially: NE->NW, NW->SW, SW->SE, SE->NE
        '''
        if self.wind_direction.north and self.wind_direction.east:
            self.wind_direction.east = False
        elif self.wind_direction.north and not self.wind_direction.east:
            self.wind_direction.north = False
        elif not self.wind_direction.north and not self.wind_direction.east:
            self.wind_direction.east = True
        elif not self.wind_direction.north and self.wind_direction.east:
            self.wind_direction.north = True
        else: raise Exception("Tile orientations have become confused")
    
    def compass_edge_water(self, compass_point):
        '''Reports whether a tile edge is land or water, based on tile orientation rather than wind direction
        
        key arguments:
        string giving either the word or letter for one of the four cardinal compass directions
        '''
        if self.wind_direction.north and self.wind_direction.east: # NE orientation => N = downwind anti
            if compass_point.lower() in ["north", "n"]:
                return self.tile_edges.downwind_anti_water
            elif compass_point.lower() in ["east", "e"]:
                return self.tile_edges.downwind_clock_water
            elif compass_point.lower() in ["south", "s"]:
                return self.tile_edges.upwind_anti_water
            elif compass_point.lower() in ["west", "w"]:
                return self.tile_edges.upwind_clock_water
            else: raise Exception("Tile orientations have become confused")
        elif not self.wind_direction.north and self.wind_direction.east: # SE orientation => N = upwind clock 
            if compass_point.lower() in ["north", "n"]:
                return self.tile_edges.upwind_clock_water
            elif compass_point.lower() in ["east", "e"]:
                return self.tile_edges.downwind_anti_water
            elif compass_point.lower() in ["south", "s"]:
                return self.tile_edges.downwind_clock_water
            elif compass_point.lower() in ["west", "w"]:
                return self.tile_edges.upwind_anti_water
            else: raise Exception("Tile orientations have become confused")
        elif not self.wind_direction.north and not self.wind_direction.east: # SW orientation => N = upwind anti
            if compass_point.lower() in ["north", "n"]:
                return self.tile_edges.upwind_anti_water
            elif compass_point.lower() in ["east", "e"]:
                return self.tile_edges.upwind_clock_water
            elif compass_point.lower() in ["south", "s"]:
                return self.tile_edges.downwind_anti_water
            elif compass_point.lower() in ["west", "w"]:
                return self.tile_edges.downwind_clock_water
            else: raise Exception("Tile orientations have become confused")
        elif self.wind_direction.north and not self.wind_direction.east: # NW orientation => N = downwind clock
            if compass_point.lower() in ["north", "n"]:
                return self.tile_edges.downwind_clock_water
            elif compass_point.lower() in ["east", "e"]:
                return self.tile_edges.upwind_anti_water
            elif compass_point.lower() in ["south", "s"]:
                return self.tile_edges.upwind_clock_water
            elif compass_point.lower() in ["west", "w"]:
                return self.tile_edges.downwind_anti_water
            else: raise Exception("Tile orientations have become confused")
        else: raise Exception("Tile orientations have become confused")
    
    
    def compass_edge_downwind(self, compass_point):
        '''Reports whether a tile edge has the wind arrow pointing to it
        
        key arguments:
        string giving either the word or letter for one of the four cardinal compass directions
        '''
        if compass_point.lower() in ["north","n"]:
            return self.wind_direction.north
        elif compass_point.lower() in ["east","e"]:
            return self.wind_direction.east
        elif compass_point.lower() in ["south","s"]:
            return not self.wind_direction.north
        elif compass_point.lower() in ["west","w"]:
            return not self.wind_direction.east
        else: raise Exception("Invalid compass direction checked")
        
    
    def move_onto_tile(self, token):
        '''records that a token is now on this tile, whether an Agent or Adventurer
        
        key arguments:
        Token either an Agent or an Adventurer from the Cartolan module
        '''
        if isinstance(token, Token):
            #Collect any wealth that has been dropped on this tile
            if self.dropped_wealth > 0:
                token.wealth += self.dropped_wealth
                self.dropped_wealth = 0
                
            if isinstance(token, Adventurer):
                print("Moving adventurer for " +str(token.player.colour)+ " player onto tile at " +str(self.tile_position.longitude)+ ", " +str(self.tile_position.latitude))
                if token.current_tile:
                    if token in token.current_tile.adventurers:
                        token.current_tile.adventurers.remove(token)
                token.current_tile = self
                self.adventurers.append(token)
                token.route.append(self)
                
            elif isinstance(token, Agent):
                if token.__dict__.get("is_dispossessed"):
                    token.is_dispossessed = False                 
                if self.agent is None or self.agent == token:
                    print("Moving agent for " +str(token.player.colour)+ " player onto tile at " +str(self.tile_position.longitude)+ ", " +str(self.tile_position.latitude))
                    if token.current_tile:
                        token.current_tile.agent = None
                    token.current_tile = self
                    self.agent = token
                    token.route.append(self) 
                elif self.agent.__dict__.get("is_dispossessed"):
                    self.agent.dismiss()
                    print("Moving agent for " +str(token.player.colour)+ " player onto tile at " +str(self.tile_position.longitude)+ ", " +str(self.tile_position.latitude))
                    self.agent = token
                    self.agent.current_tile = self
                    token.route.append(self) # relevant only in Regular and Advanced mode
                else: raise Exception("Tried to add multiple Agents to a tile: adding and agent of " +token.player.colour+ " player where there was an existing agent of " +self.agent.player.colour)
            else: raise Exception("Didn't know how to handle this kind of token")
        else: raise Exception("Tried to move something other than a token onto a tile")
    
    def move_off_tile(self, token):
        '''Records a token being removed from a Tile
        
        key arguments:
        Token either an Agent or an Adventurer from the Cartolan module
        '''
        if token == self.agent:
            self.agent.current_tile = None
            self.agent = None
            return True
        elif token in self.adventurers:
            self.adventurers.remove(token)
            return True
        else:
            return False
    
    def compare(self, tile):
        '''Deeply compares data with another tile, except for position and orientation.
        
        key arguments:
        Tile takes a Cartolan.Base.Tile
        '''
        if (tile.tile_edges.upwind_clock_water == self.tile_edges.upwind_clock_water
            and tile.tile_edges.upwind_anti_water == self.tile_edges.upwind_anti_water
            and tile.tile_edges.downwind_clock_water == self.tile_edges.downwind_clock_water
            and tile.tile_edges.downwind_anti_water == self.tile_edges.downwind_anti_water
            and tile.tile_back == self.tile_back
            and tile.is_wonder == self.is_wonder):
            return True
        else:
            return False
        

class TilePile:
    '''Represents a stack of tiles in the game Cartolan
    
    methods:
    __init__ optionally takes a tile_back string and a List of tiles
    '''
    def __init__(self, tile_back = "water", tiles = []):
        self.tile_back = tile_back
        self.tiles = tiles
    
    def add_tile(self, tile):
        '''Includes another Tile in this pile
        
        key arguments:
        Tile object from the Cartolan module
        '''
        if isinstance(tile, Tile):
            if tile.tile_back == self.tile_back:
                self.tiles.append(tile)
            else: raise Exception ("Tried adding a tile to the wrong pile")
        else: raise Exception("Tried adding something other than a tile to a pile")
    
    def draw_tile(self):
        '''Removes and returns a Tile from the pile'''
        if self.tiles:
            return self.tiles.pop()
        else:
            return None
    
    def shuffle_tiles(self):
        '''Randomises the order of tiles in the pile'''
        random.shuffle(self.tiles)

class CityTile(Tile):
    '''A template for Tiles representing cities in the game Cartolan
    
    Methods:
    __init__ taking a Game object and two Bools recording whether this is the Capital and whether it has been discovered 
    
    Interfaces:
    visit_city, bank_wealth, buy_adventurers, buy_agents
    '''
    def __init__(self, game, wind_direction, tile_edges, is_capital, is_discovered):
        super().__init__(game, "land", wind_direction, tile_edges, False)
        self.is_capital = is_capital
        self.is_discovered = is_discovered
        game.cities.append(self)
        
    def compare(self, tile):
        if not isinstance(tile, CityTile):
            return False
        elif not tile.is_capital == self.is_capital:
            return False
        else:
            return super().compare(tile)
   
    def move_off_tile(self, token):
        '''Resets the route as an Adventurer leaves the city'''
        super().move_off_tile(token)
        token.route = [self]
    
    def visit_city(self, adventurer):
        '''placeholder for interactions between an Adventurer and city'''
        return None
        
    def bank_wealth(self, adventurer):
        '''placeholder for letting players move wealth from an adventurer's Chest to their Vault'''
        return None
    
    def buy_adventurers(self, adventurer):
        '''placeholder for letting players buy another Adventurer using wealth from their Vault'''
        return None
        
    def buy_agents(self, adventurer):
        '''placeholder for letting players buy another Agent using wealth from their Vault'''
        return None