'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import random

from cartolan.core.tokens import Token, Adventurer, Inn

import logging

logger = logging.getLogger(__name__)

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
                , has_trade_port = False):
        self.game = game
        self.tile_back = tile_back
        self.wind_direction = wind_direction
        self.tile_edges = tile_edges
        self.tile_position = TilePosition(None, None)
        self.has_trade_port = has_trade_port
        
        self.adventurers = [] # to keep track of the Adventurer tokens on a tile at any point
        self.inn = None # there can only be one Inn token on a given tile
        self.dropped_silks = 0 # to keep track of silks dropped when returning abruptly to a City
        # self.tile_id = tile_back+str(wind_direction.north)+str(wind_direction.east)+str(tile_edges.upwind_clock_water)+str(tile_edges.upwind_anti_water)+str(tile_edges.downwind_clock_water) + str(tile_edges.downwind_anti_water)+str(random.random())
        self.tile_id = game.register(self)

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

    def to_json(self):
        e = self.tile_edges
        uc = 't' if e.upwind_clock_water else 'f'
        ua = 't' if e.upwind_anti_water else 'f'
        dc = 't' if e.downwind_clock_water else 'f'
        da = 't' if e.downwind_anti_water else 'f'
        wonder = 't' if self.has_trade_port else 'f'
        return {
            "tile_id": self.tile_id,
            "tile_name": uc + ua + dc + da + wonder,
            "wind_north": self.wind_direction.north,
            "wind_east": self.wind_direction.east,
            "longitude": self.tile_position.longitude,
            "latitude": self.tile_position.latitude,
            "dropped_silks": self.dropped_silks,
            "tile_back": self.tile_back,
        }

#    def __deepcopy__(self, memo):
#        '''Excludes creation of new version from deep copying, copying only the reference
#        '''
#        return self
    
    def place_tile(self, longitude, latitude):
        '''records the location of a Tile object in the PlayArea of a Cartolan game
        
        key arguments:
        int longitude
        int latitude
        '''
        # logger.debug("Placing tile " +str(longitude)+", "+str(latitude))
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
        '''records that a token is now on this tile, whether an Inn or Adventurer
        
        key arguments:
        Token either an Inn or an Adventurer from the Cartolan module
        '''
        if isinstance(token, Token):
            #Collect any silks that has been dropped on this tile
            if self.dropped_silks > 0:
                token.silks += self.dropped_silks
                self.dropped_silks = 0
                
            if isinstance(token, Adventurer):
                logger.debug("Moving adventurer for " +str(token.player.name)+ " onto tile at " +str(self.tile_position.longitude)+ ", " +str(self.tile_position.latitude))
                if token.current_tile:
                    if token in token.current_tile.adventurers:
                        token.current_tile.adventurers.remove(token)
                token.current_tile = self
                self.adventurers.append(token)
                token.route.append(self)
                token.turn_route.append(self)
                
            elif isinstance(token, Inn):
                if token.__dict__.get("is_ransacked"):
                    token.is_ransacked = False                 
                if self.inn is None or self.inn == token:
                    logger.debug("Moving inn for " +str(token.player.name)+ " onto tile at " +str(self.tile_position.longitude)+ ", " +str(self.tile_position.latitude))
                    if token.current_tile:
                        token.current_tile.inn = None
                    token.current_tile = self
                    self.inn = token
                    token.route.append(self) 
                    token.turn_route.append(self)
                elif self.inn.__dict__.get("is_ransacked"):
                    self.inn.dismiss()
                    logger.debug("Moving inn for " +str(token.player.name)+ " onto tile at " +str(self.tile_position.longitude)+ ", " +str(self.tile_position.latitude))
                    self.inn = token
                    self.inn.current_tile = self
                    token.route.append(self) # relevant only in Regular and Advanced mode
                    token.turn_route.append(self)
                else: raise Exception("Tried to add multiple Inns to a tile: adding and inn of " +token.player.name+ " where there was an existing inn of " +self.inn.player.name)
            else: raise Exception("Didn't know how to handle this kind of token")
        else: raise Exception("Tried to move something other than a token onto a tile")
    
    def move_off_tile(self, token):
        '''Records a token being removed from a Tile
        
        key arguments:
        Token either an Inn or an Adventurer from the Cartolan module
        '''
        if token == self.inn:
            self.inn.current_tile = None
            self.inn = None
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
            and tile.has_trade_port == self.has_trade_port):
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
    
    def shuffle_tiles(self, rng=random):
        '''Randomises the order of tiles in the pile

        Arguments:
        rng: source of randomness; pass the game's rng for reproducible games
        '''
        rng.shuffle(self.tiles)

    def to_json(self):
        return {
            "tile_back": self.tile_back,
            "tile_count": len(self.tiles),
            "tiles": [t.to_json() for t in self.tiles],
        }

class CityTile(Tile):
    '''A template for Tiles representing cities in the game Cartolan
    
    Methods:
    __init__ taking a Game object and two Bools recording whether this is the Capital and whether it has been discovered 
    
    Interfaces:
    visit_city, bank_silks, buy_adventurers, buy_inns
    '''
    def __init__(self, game, wind_direction, tile_edges, is_home_city, is_discovered):
        super().__init__(game, "land", wind_direction, tile_edges, False)
        self.is_home_city = is_home_city
        self.is_discovered = is_discovered
        game.cities.append(self)
        
    def compare(self, tile):
        if not isinstance(tile, CityTile):
            return False
        elif not tile.is_home_city == self.is_home_city:
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
        
    def bank_silks(self, adventurer):
        '''placeholder for letting players move silks from an adventurer's Chest to their Vault'''
        return None
    
    def buy_adventurers(self, adventurer):
        '''placeholder for letting players buy another Adventurer using silks from their Vault'''
        return None
        
    def buy_inns(self, adventurer):
        '''placeholder for letting players buy another Inn using silks from their Vault'''
        return None

    def to_json(self):
        d = super().to_json()
        d["tile_name"] = "home_city" if self.is_home_city else "mythical_city"
        return d