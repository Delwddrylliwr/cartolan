'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import random
from cartolan.core.tokens import Token, Adventurer, Inn
from cartolan.core.tiles import Tile, WindDirection, TileEdges, CityTile
from cartolan.editions.beginner import AdventurerBeginner, InnBeginner, CityTileBeginner

import logging

logger = logging.getLogger(__name__)


class AdventurerRegular(AdventurerBeginner):
    '''An extension to the AdventurerBeginner class that introduces extra behaviours available in Regular mode Cartolan
    
    Methods:
    __init__ takes Cartolan.Game, Cartolan.Player, and Cartolan.Tile
    choose_pile takes a String giving the latter or word for a cardinal compass direction
    choose_discard_pile takes a String giving the latter or word for a cardinal compass direction
    can_move takes takes a String giving the latter or word for a cardinal compass direction
    move takes a String giving the latter or word for a cardinal compass direction
    wait
    trade takes a Cartolan.Tile
    attack takes a Cartolan.Token object
    restore_inn takes a Cartolan.Inn object
    '''
    def __init__(self, game, player, starting_city):
        super().__init__(game, player, starting_city)
        self.pirate_token = False
        
        #Mirror that game variables, mostly for Advanced mode to modify them
        self.attack_success_prob = game.attack_success_prob
        self.value_arrest = game.value_arrest
        self.value_ransack_inn = game.value_ransack_inn
        self.cost_inn_restore = game.cost_inn_restore
        self.num_chest_maps = game.num_chest_maps
        
        #Unburdened movement is deprecated
        self.max_upwind_moves_unburdened = self.max_upwind_moves
        self.max_land_moves_unburdened = self.max_land_moves
        
        #Record some additional instructions
        self.attacked = 0
        self.restored = False
        
        #Draw some tiles randomly to the Adventurer's Chest
        self.chest_maps = self.choose_tiles(self.num_chest_maps)
        #Keep track of which of these should be tried for movement
        self.chosen_map_index = None
        #Track manual clockwise rotation offsets (int 0-3) per chest map, applied on top of wind-matching
        self.chest_map_offsets = [0] * len(self.chest_maps)
    
    
    def choose_pile(self, compass_point):
        '''establish which pile to draw from, based on the edge being moved over from the preceding tile
        '''
        if self.current_tile.compass_edge_water(compass_point):
            tile_pile = self.game.tile_piles["water"]
            logger.debug("Identified the " +tile_pile.tile_back+ " tile pile, which still has " +str(len(tile_pile.tiles)) +" tiles")
            return tile_pile
        else:
            tile_pile = self.game.tile_piles["land"]
            logger.debug("Identified the " +tile_pile.tile_back+ " tile pile, which still has " +str(len(tile_pile.tiles)) +" tiles")
            return tile_pile
    
    def choose_discard_pile(self, compass_point):
        ''' establish which pile to draw from, based on the edge being moved over from the preceding tile
        '''
        if self.current_tile.compass_edge_water(compass_point):
            discard_pile = self.game.discard_piles["water"]
            logger.debug("Identified the " +discard_pile.tile_back+ " discard pile, which still has " +str(len(discard_pile.tiles)) +" tiles")
            return discard_pile
        else:
            discard_pile = self.game.discard_piles["land"]
            logger.debug("Identified the " +discard_pile.tile_back+ " discard pile, which still has " +str(len(discard_pile.tiles)) +" tiles")
            return discard_pile
    
    def choose_tiles(self, num_tiles):
        '''For a given number of tiles, select regular tiles from across the bags / tile_piles
        '''
        chosen_tiles = []
        for tile_num in range(num_tiles):
            #Alternate between bags
            pile_num = tile_num % len(self.game.tile_piles)
            #Select the tile pile to draw from
            tile_pile = self.game.tile_piles[list(self.game.tile_piles.keys())[pile_num]] #WARNING - this isn't deterministic, so an undo that somehow changes the dict may get different results
            #Choose the next tile from the bag / pile and add it to their Chest
            if tile_pile.tiles:
                chosen_tiles.append(tile_pile.tiles.pop())
        return chosen_tiles
            
    # Whether movement is possible is handled much like the Beginner mode, except that carrying no silks increases upwind and land moves, and a dice roll can allow upwind movement
    def can_move(self, compass_point): 
        '''Before checking any further, make sure that the total possible moves havne't been used
        '''
        if not self.has_remaining_moves():
            return False
        
        #Check whether attack is possible
        if compass_point is None:
            if self.downwind_moves + self.land_moves + self.upwind_moves < self.max_downwind_moves:
                if len(self.current_tile.adventurers) > 1:
                    for adventurer in self.current_tile.adventurers:
                        if adventurer is not self and adventurer.silks > 0:
                            return True
                if self.current_tile.inn:
                    if self.current_tile.inn not in self.inns_rested:
                        return True
        
        #Check whether rest is possible and otherwise give an extra opportunity to retreat
        if compass_point is None:
            if ((self.downwind_moves + self.land_moves + self.upwind_moves < self.max_upwind_moves + 1
                or self.downwind_moves + self.land_moves + self.upwind_moves < self.max_land_moves + 1)
                and self.downwind_moves + self.land_moves + self.upwind_moves < self.max_downwind_moves):
                return True #give an extra opportunity to retreat
        
        # check that instruction is valid: a direction provided or an explicit general check through a None
        if compass_point is None:
            logger.debug("Adventurer is checking whether any movement at all is possible")
            if ((self.game.movement_rules == "initial" or self.game.movement_rules == "budgetted")
                and self.max_downwind_moves <= self.land_moves + self.downwind_moves + self.upwind_moves):
                return False
            for compass_point in ["n","e","s","w"]:
                if self.can_move(compass_point):
                    return True
            return False
        elif not (compass_point.lower() in ["north","n","east","e","south","s","west","w"]): 
            raise Exception("invalid direction given for movement")
        
        # check whether move is possible over the edge
#        logger.debug("Adventurer is checking whether movement is possible over the " +compass_point
#              + " edge from their tile at " +str(self.current_tile.tile_position.longitude)+ "," 
#              + str(self.current_tile.tile_position.latitude))
        if self.game.movement_rules == "initial": #this version 1 of movement allows land and upwind movement only initially after resting
            moves_since_rest = self.land_moves + self.downwind_moves + self.upwind_moves
#            logger.debug("Adventurer has determined that they have moved " +str(moves_since_rest)+ " times since resting")
            if not self.current_tile.compass_edge_water(compass_point): #land movement needed
                if(moves_since_rest < self.max_land_moves 
                   or (self.silks == 0 and moves_since_rest < self.max_land_moves_unburdened)):
                    return True
                else: return False
            elif (self.current_tile.compass_edge_water(compass_point) 
                  and self.current_tile.compass_edge_downwind(compass_point)): #downwind movement possible
                if (moves_since_rest < self.max_downwind_moves):
                    return True
                else: return False
            else: #if not land or downwind, then movement must be upwind
                if(moves_since_rest < self.max_upwind_moves
                   or (self.silks == 0 and moves_since_rest < self.max_upwind_moves_unburdened)):
                    return True
                elif self.downwind_moves < self.max_downwind_moves:
#                     return None
                        return False
                else: return False
        elif self.game.movement_rules == "budgetted": #this version 2 of movement allows land and upwind movement any time, but a limited number before resting
            logger.debug("Adventurer has moved " +str(self.upwind_moves)+ " times upwind, " +str(self.land_moves)+ " times overland, and " +str(self.downwind_moves)+ " times downwind, since resting")
            if not self.current_tile.compass_edge_water(compass_point): #land movement needed
                if(self.land_moves < self.max_land_moves
                   or (self.silks == 0 and self.land_moves < self.max_land_moves_unburdened)
                   and self.upwind_moves == 0):
                    return True
                else: return False
            elif (self.current_tile.compass_edge_water(compass_point) 
                  and self.current_tile.compass_edge_downwind(compass_point)): #downwind movement possible
                if (self.downwind_moves + self.land_moves + self.upwind_moves < self.max_downwind_moves):
                    return True
                else: return False
            else: #if not land or downwind, then movement must be upwind
                if ((self.upwind_moves < self.max_upwind_moves 
                   or (self.silks == 0 and self.upwind_moves < self.max_upwind_moves_unburdened))
                   and self.land_moves == 0):
                    return True
                elif self.downwind_moves < self.max_downwind_moves:
#                     return None
                    return False
                else: return False
        else: raise Exception("Invalid movement rules specified")
    
#    def move(self, compass_point):
#        '''Extends Beginnner movement to rotate Chest maps after movement (for more comfortable visualisation)
#        '''
#        moved = super().move(compass_point)
#        if moved:
#            self.match_chest_directions()
#        return moved
    
    def match_chest_directions(self):
        '''Rotates all chest maps to match the current tile's wind direction, then applies any manual offsets.
        '''
        for i, chest_map in enumerate(self.chest_maps):
            while not (chest_map.wind_direction.north == self.current_tile.wind_direction.north and
                       chest_map.wind_direction.east == self.current_tile.wind_direction.east):
                chest_map.rotate_tile_clock()
            offset = self.chest_map_offsets[i] if i < len(self.chest_map_offsets) else 0
            for _ in range(offset):
                chest_map.rotate_tile_clock()
    
    def explore(self, tile_pile, discard_pile, longitude, latitude, compass_point_moving):
        '''Extends exploration to allow tiles to be used from the Adventurer's Chest
        '''
        #check if there is a chest map selected and try to place it
        if isinstance(self.chosen_map_index, int):
            chosen_map = self.chest_maps[self.chosen_map_index]
            adjoining_edges_water = self.get_adjoining_edges(longitude, latitude)
            tile_idx = self.chosen_map_index
            offset = self.chest_map_offsets[tile_idx] if tile_idx < len(self.chest_map_offsets) else 0
            if offset != 0:
                # Player manually rotated this tile: only succeed if it fits in its displayed orientation
                if self.place_tile_exact(chosen_map, longitude, latitude, compass_point_moving, adjoining_edges_water):
                    self.chest_maps.pop(tile_idx)
                    self.chest_map_offsets.pop(tile_idx)
                    self.chosen_map_index = None
                    return True
                self.game.num_failed_explorations += 1
                return False
            else:
                # No manual rotation: use the standard auto-rotating placement
                if self.rotate_and_place(chosen_map, longitude, latitude, compass_point_moving, adjoining_edges_water):
                    self.chest_maps.pop(tile_idx)
                    self.chest_map_offsets.pop(tile_idx)
                    self.chosen_map_index = None
                    return True
        #If there was no tile selected, or the unrotated chest map didn't fit, explore normally
        return super().explore(tile_pile, discard_pile, longitude, latitude, compass_point_moving)
        
    def replenish_chest_maps(self):
        '''If this Adventurer has fewer chest maps than the max, then draw more
        '''
        #Count how many tiles they are short of the max chest maps
        num_tiles_to_choose = self.num_chest_maps - len(self.chest_maps)
        #Add this many extra tiles to their chest, with zero manual rotation offsets
        new_tiles = self.choose_tiles(num_tiles_to_choose)
        self.chest_maps += new_tiles
        self.chest_map_offsets += [0] * len(new_tiles)
    
    def swap_chest_maps(self):
        '''Checks whether the player will pay to replace all an Adventurer's chest maps
        '''
        #For each current tile offer replacements, and return  to the bag / tile pile
        new_chest_maps = []
        for tile in self.chest_maps:
            # Alternate between piles for forming the selection
            tile_options = self.choose_tiles(self.game.num_tile_choices[self.player])
            if tile_options:
                #Offer the current tile too
                tile_options.append(tile)
                chosen_tile = self.player.choose_tile(self, tile_options)
                tile_options.remove(chosen_tile)
                new_chest_maps.append(chosen_tile)
                #Return all the other tiles to the relevant piles
                for rejected_tile in tile_options:
                    self.return_to_pile(rejected_tile)
        self.chest_maps = new_chest_maps
        self.chest_map_offsets = [0] * len(new_chest_maps)

    def return_to_pile(self, tile):
        '''Identifies the pile associated with a particular tile and returns it there
        '''
        relevant_pile = self.game.tile_piles[tile.tile_back]
        relevant_pile.tiles.insert(0, tile)
        
    def discover(self, tile):
        #check whether this is a discovered city and don't offer the usual
        if isinstance(self.current_tile, CityTile):
            self.current_tile.is_discovered = True
            self.silks += self.game.value_discover_city
            self.current_tile.visit_city(self)
            return True
        else:
            super().discover(tile)
    
    def interact_tokens(self):
        #check whether there is an adventurer here and attack if the player wants
        if self.current_tile.adventurers:
            for adventurer in self.current_tile.adventurers:
                if (adventurer.player != self.player 
                    and ((adventurer.silks > 0 and not adventurer.pirate_token)
                         or (adventurer.pirate_token #cannot arrest pirates on Disaster Tiles
                             and not isinstance(self.current_tile, DisasterTile)))):
                    if self.player.check_attack_adventurer(self, adventurer):
                        self.attack(adventurer)
                        
        
        #check whether there is an inn here and then check rest, attack if active or restore if ransacked
        if self.current_tile.inn:
            inn = self.current_tile.inn
            if not inn.is_ransacked:
                if inn.player == self.player:
                    if inn.silks > 0:
                        if self.player.check_collect_silks(inn):
                            self.collect_silks()
                    if self.can_rest(inn):
                        if self.player.check_rest(self, inn):
                            self.rest(inn)
                else:
                    if inn.silks + self.value_ransack_inn > 0:
                        if self.player.check_attack_inn(self, inn):
                            self.attack(inn)
                    #If not attacking, then offer rest
                    if self.can_rest(inn):
                        if self.player.check_rest(self, inn):
                            self.rest(inn)
            #Restore the Inn if they are ransacked        
            else:
                if (inn.player == self.player 
                    and self.silks >= self.cost_inn_restore):
                    if self.player.check_restore_inn(self, inn):
                        self.restore_inn(inn)
    
    def trade(self, tile):
        '''Expands on the AdventurerBeginner, by preventing pirates from trading
        
        Arguments
        tile should be a Cartolan.Tile
        '''
        #check whether this is a pirate and refuse them trade
        if self.pirate_token:
            return False
        
        return super().trade(tile)
    
    def can_rest(self, token):
        '''Expands on AdventurerBeginner by preventing pirates resting with others' Inns
        '''
        #check whether this is a pirate and refuse them rest, unless they belong to the same player
        if self.pirate_token and not self.player == token.player:
            return False
        return super().can_rest(token)
    
    def attack(self, token):
        '''Introduces the mechanic of Adventurers taking silks and maps and cards from other tokens.
        '''
        #Record the decision to attack this move
        self.attacked += 1
        
        success = False
        # have opponent roll for defence, roll for attack, compare rolls
        if self.game.rng.random() < self.attack_success_prob:
            success = True
        
        # resolve conflict
        # check whether adventurer or inn
        if isinstance(token, Adventurer):
            adventurer = token
            # check whether the defender adventurer is a pirate, and remove the pirate token
            if adventurer.pirate_token:
                # arrest them
                if success:
                    self.arrest(adventurer)
            else: # rob them
                self.pirate_token = True #just trying will make them a pirate
                if success:
                    logger.debug(self.player.name+" successfully attacked "+token.player.name+"'s Adventurer.")
                    default_steal = adventurer.silks//2 + adventurer.silks%2
                    chosen_steal = None
                    while not chosen_steal in range(0, adventurer.silks + 1):
                        chosen_steal = self.player.check_steal_amount(adventurer, adventurer.silks, default_steal)
                    self.silks += chosen_steal
                    adventurer.silks -= chosen_steal
                    #Randomly steal chest maps to top up
                    if isinstance(token, AdventurerRegular):
                        if 0 < len(self.chest_maps) < self.num_chest_maps:
                            victim_chest = token.chest_maps
#                            self.chest_maps.append(victim_chest.pop(random.randint(0, len(victim_chest)-1)))
                            if len(victim_chest) > 0:
                                stolen_tile = self.player.choose_tile(self, victim_chest)
                                victim_chest.remove(stolen_tile)
                                self.chest_maps.append(stolen_tile)
        elif isinstance(token, Inn):
            if not token.is_ransacked:
                self.pirate_token = True #just trying will make them a pirate
                if success:
                    logger.debug(self.player.name+" successfully attacked "+token.player.name+"'s Inn.")
                    inn = token
                    self.silks += inn.silks + self.value_ransack_inn
                    inn.is_ransacked = True
                    inn.silks = 0;
        else: raise Exception("Not able to deal with this kind of token.")
        
        #Keep track of attacks for static visualisation
        attack_history = self.player.attack_history.get(self.game)
        if not attack_history:
            attack_history = self.player.attack_history[self.game] = []
        attack_history.append([self.current_tile, success])
        return success
    
    def arrest(self, pirate):
        '''Sends pirates back to their last city and claims a reward.
        '''
        logger.debug(self.player.name+" successfully arrested "+pirate.player.name+"'s Adventurer.")
        self.silks += self.value_arrest # get a reward
        pirate.end_expedition()
    
    def end_expedition(self, city=None):
        '''Extends to deal with piracy
        '''
        self.pirate_token = False
        self.replenish_chest_maps()
        return super().end_expedition(city)
    
    def check_tile_available(self, tile):
        '''Extends the AdventurerBeginner method to keep track of whether existing Inns have been ransacked when placing on a tile
        '''
        if self.pirate_token:
            return False
        elif isinstance(tile, CityTile):
            return False
        elif tile.inn is None:
            return True
        elif tile.inn.is_ransacked:
#            #This ransacked Inn is about to be lost to its pla
#            tile.game.inns[tile.inn.player].remove(tile.inn)
#            tile.move_off_tile(inn)
            return True
        else:
            return False 
    
    def restore_inn(self, inn):
        #Record the decision to restor this move
        self.restored = True
        
        if inn.is_ransacked:
            if self.cost_inn_restore <= self.silks:
                logger.debug("Paying " +str(self.cost_inn_restore)+ " to restore " 
                      +inn.player.name+"'s Inn at position " 
                      +str(inn.current_tile.tile_position.longitude)
                     +","+ str(inn.current_tile.tile_position.latitude))
                self.silks -= self.cost_inn_restore
                inn.is_ransacked = False
                #Make sure that the Adventurer can't use this Inn this turn
                self.inns_rested.append(inn)
                return True
            else:
                logger.debug("Cannot afford to restore an inn")
                return False
        else:
            logger.debug("Didn't need to restore this Inn")
            return False

    def to_json(self):
        d = super().to_json()
        d.update({
            "pirate_token": self.pirate_token,
            "chest_maps": [t.to_json() for t in self.chest_maps],
            "chosen_map_index": self.chosen_map_index,
            "num_chest_maps": self.num_chest_maps,
            "chest_map_offsets": list(self.chest_map_offsets),
        })
        return d


class CityTileRegular(CityTileBeginner):
    '''City tile for Regular mode: behaviour lives on GameRegular.'''

class InnRegular(InnBeginner):
    '''Extends the InnBeginner class to keep track of information relevant in the Regular mode of Cartolan'''
    def __init__(self, game, player, tile):
        super().__init__(game, player, tile)
        # Need to keep track of whether this Inn has been ransacked
        self.is_ransacked = False
        
    def give_rest(self, adventurer):
        '''Takes into account whether Inns have been ransacked, and replenishes chest maps
        '''
        if self.is_ransacked:
            return False
        else:
            adventurer.replenish_chest_maps()
            return InnBeginner.give_rest(self, adventurer)
        
    def manage_trade(self, adventurer):
        if self.is_ransacked:
            return False
        else:
            super().manage_trade(adventurer)
            
    def dismiss(self):
        '''Takes this Inn off a tile fully and out of the game
        '''
        self.game.inns[self.player].remove(self)
        self.current_tile.move_off_tile(self)

    def to_json(self):
        d = super().to_json()
        d["is_ransacked"] = self.is_ransacked
        return d

class DisasterTile(Tile):
    '''***DEPRECATED*** Represents a Disaster Tile in the game Cartolan, which removes Adventurers' silks and send them back to a city '''
    def move_onto_tile(self, token):
        '''Takes the silks of non-Pirate Adventurers as they land on the tile, but allows pirates to move as if from land

        Arguments:
        Cartolan.Token for the Adventurer moving onto the tile
        '''
        if isinstance(token, Token):
            if isinstance(token, Adventurer):
                token.route.append(self)
                token.turn_route.append(self)
                if not self in self.game.disaster_tiles:
                    self.game.disaster_tiles.append(self)
                else:
                    #if this has not just been discovered then the Adventurer isn't surprised and can become a pirate to survive
                    token.pirate_token = True
                # check if the Adventurer has a Pirate token
                if token.pirate_token:
                    logger.debug("Pirate moves onto disaster tile")
                    super().move_onto_tile(token)
#                    if token.player.check_court_disaster(token, self): # get player input on whether to attack the disaster
#                        self.attack_adventurer(token)
                else: # otherwise send the Adventurer to the capital and keep their silks and end their turn
                    logger.debug("Adventurer moved onto disaster tile. Dropping silks and returning to last city visited.")
                    self.dropped_silks += token.silks
                    token.end_expedition()
            elif isinstance(token, Inn):
                logger.debug("Tried to add Inn to a disaster tile")
                return False
        else: raise Exception("Tried to move something other than a token onto a tile")

    def attack_adventurer(self, adventurer):
        '''Checks whether a Player wants to try and recover silks taken by the tile

        Arguments:
        Cartolan.Adventurer for the Adventurer token that is on the tile
        '''
#        import random
#
#        # if the rolls are the same then the pirate gets helf the silks
#        if random.random() < self.game.attack_success_prob:
#            adventurer.silks += self.dropped_silks//2 + self.dropped_silks%2
#        else: # otherwise send the Adventurer to the capital and keep their silks
#            self.dropped_silks += adventurer.silks
#            adventurer.end_expedition()

    def compare(self, tile):
        if not isinstance(tile, DisasterTile):
            return False
        else:
            return super().compare(tile)

    def to_json(self):
        d = super().to_json()
        d["tile_name"] = "water_disaster" if self.tile_back == "water" else "land_disaster"
        return d

class HomeCityTileRegular(CityTileRegular):
    def __init__(self, game, tile_back = "water"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(True,True,True,True)):
        super().__init__(game, wind_direction, tile_edges, True, True)

class MythicalCityTileRegular(CityTileRegular):
    def __init__(self, game, tile_back = "land"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(False,False,False,False)):
        super().__init__(game, wind_direction, tile_edges, False, False)