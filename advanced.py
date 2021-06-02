'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import random
from regular import AdventurerRegular, AgentRegular, CityTileRegular
from base import WindDirection, TileEdges

class AdventurerAdvanced(AdventurerRegular):
    '''Extends to allow a set of map tiles to be carried by each Adventurer in their chest and placed instead of a random one
    '''
    def __init__(self, game, player, starting_city):
        super().__init__(game, player, starting_city)
        
        #Draw some tiles randomly to the Adventurer's Chest
        self.chest_tiles = []
        self.choose_random_tiles(self.game.NUM_CHEST_TILES)
        #Keep track of which of these should be tried for movement
        self.preferred_tile_num = None
    
    def choose_random_tiles(self, num_tiles):
        '''For a given number of tiles, select randomly from across the bags / tile_piles
        '''
        for tile_num in range(num_tiles):
            #Randomly select a tile pile to draw from
            tile_pile = self.game.tile_piles[random.choice(list(self.game.tile_piles.keys()))]
            #Randomly choose a tile from the bag / pile and add it to their Chest
            chosen_tile = tile_pile.tiles.pop(random.randint(0,len(tile_pile.tiles)-1))
            self.chest_tiles.append(chosen_tile)
    
    def move(self, compass_point):
        '''Extends Beginnner movement to rotate Chest tiles after movement (for more comfortable visualisation)
        '''
        moved = super().move(compass_point)
        if moved:
            for chest_tile in self.chest_tiles:
                while not (chest_tile.wind_direction.north == self.current_tile.wind_direction.north and 
                           chest_tile.wind_direction.east == self.current_tile.wind_direction.east):
                    chest_tile.rotate_tile_clock()
        return moved
    
    def explore(self, tile_pile, discard_pile, longitude, latitude, compass_point_moving):
        '''Extends exploration to allow tiles to be used from the Adventurer's Chest
        '''
        #check if there is a chest tile selected and try to place this
        if isinstance(self.preferred_tile_num, int):
            preferred_tile = self.chest_tiles[self.preferred_tile_num]
            #establish what edges adjoin the given space
            adjoining_edges_water = self.get_adjoining_edges(longitude, latitude)
            #try to place the tile
            if self.rotate_and_place(preferred_tile, longitude, latitude, compass_point_moving, adjoining_edges_water):
                self.chest_tiles.pop(self.preferred_tile_num)
                self.preferred_tile_num = None
                return True          
        #If there was no tile selected or this wouldn't fit, then explore normally, drawing a random tile
        return super().explore(tile_pile, discard_pile, longitude, latitude, compass_point_moving)
        
    def attack(self, token):
        '''Extends Regular mode to allow stealing of Chest Tiles
        '''
        if super().attack(token):
            #Randomly steal tiles to top up
            if isinstance(token, AdventurerAdvanced):
                if len(self.chest_tiles) < self.game.NUM_CHEST_TILES:
                    victim_chest = token.chest_tiles
                    self.chest_tiles.append(victim_chest.pop(random.randint(0, len(victim_chest)-1)))
        else:
            return False
        
    def replenish_chest_tiles(self):
        '''If this Adventurer has fewer chest tiles than the max, then draw more
        '''
        #Count how many tiles they are short of the max chest tiles
        num_tiles_to_choose = self.game.NUM_CHEST_TILES - len(self.chest_tiles)
        #Add this many extra tiles to their chest
        self.choose_random_tiles(num_tiles_to_choose)
        
    def rechoose_chest_tiles(self):
        '''Checks whether the player will pay to replace all an Adventurer's chest tiles
        '''
#        if self.player.check_rechoose_tiles():
#            #Return current tiles to the bag / tile pile
#            while self.chest_tiles:
#                tile = self.chest_tiles.pop()
#                relevant_pile = self.game.tile_piles[tile.tile_back]
#                relevant_pile.append(tile)
#            #Replenish the empty Chest Tiles
#            self.replenish_chest_tiles()

class AgentAdvanced(AgentRegular):
    '''Extends Regular mode to replenish Chest Tiles
    '''
    def give_rest(self, adventurer):
        '''Extends Regular mode to replenish Chest Tiles
        '''
        if self.is_dispossessed:
            return False
        else:
            adventurer.replenish_chest_tiles()
            super().give_rest(adventurer)

class CityTileAdvanced(CityTileRegular):
    '''Extends to replenish Chest Tiles, and offer purchase of refreshed chest tiles
    '''
    def visit_city(self, adventurer, abandoned=False):
       '''Extends to replenish Chest Tiles, and offer purchase of refreshed chest tiles
       '''
       #Top up any missing chest tiles from the bags
       adventurer.replenish_chest_tiles()
       #Offer the chance to pay and completely swap out chest tiles
       adventurer.rechoose_chest_tiles()
       #Continue as usual
       super().visit_city(adventurer, abandoned)

class CapitalTileAdvanced(CityTileAdvanced):
    def __init__(self, game, tile_back = "water"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(True,True,True,True)):
        super().__init__(game, wind_direction, tile_edges, True, True)

class MythicalTileAdvanced(CityTileAdvanced):
    def __init__(self, game, tile_back = "land"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(False,False,False,False)):
        super().__init__(game, wind_direction, tile_edges, False, False)