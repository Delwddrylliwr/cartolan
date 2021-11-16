'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import random
from base import Token, Adventurer, Agent, Tile, WindDirection, TileEdges, CityTile
from beginner import AdventurerBeginner, AgentBeginner, CityTileBeginner


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
    restore_agent takes a Cartolan.Agent object
    '''
    def __init__(self, game, player, starting_city):
        super().__init__(game, player, starting_city)
        self.pirate_token = False
        
        #Mirror that game variables, mostly for Advanced mode to modify them
        self.attack_success_prob = game.attack_success_prob
        self.value_arrest = game.value_arrest
        self.value_dispossess_agent = game.value_dispossess_agent
        self.cost_agent_restore = game.cost_agent_restore
        self.num_chest_tiles = game.num_chest_tiles
        
        #Unburdened movement is deprecated
        self.max_upwind_moves_unburdened = self.max_upwind_moves
        self.max_land_moves_unburdened = self.max_land_moves
        
        #Record some additional instructions
        self.attacked = 0
        self.restored = False
        
        #Draw some tiles randomly to the Adventurer's Chest
        self.chest_tiles = []
        self.choose_tiles(self.num_chest_tiles)
        #Keep track of which of these should be tried for movement
        self.preferred_tile_num = None
    
    
    def choose_pile(self, compass_point):
        '''establish which pile to draw from, based on the edge being moved over from the preceding tile
        '''
        if self.current_tile.compass_edge_water(compass_point):
            tile_pile = self.game.tile_piles["water"]
            print("Identified the " +tile_pile.tile_back+ " tile pile, which still has " +str(len(tile_pile.tiles)) +" tiles")
            return tile_pile
        else:
            tile_pile = self.game.tile_piles["land"]
            print("Identified the " +tile_pile.tile_back+ " tile pile, which still has " +str(len(tile_pile.tiles)) +" tiles")
            return tile_pile
    
    def choose_discard_pile(self, compass_point):
        ''' establish which pile to draw from, based on the edge being moved over from the preceding tile
        '''
        if self.current_tile.compass_edge_water(compass_point):
            discard_pile = self.game.discard_piles["water"]
            print("Identified the " +discard_pile.tile_back+ " discard pile, which still has " +str(len(discard_pile.tiles)) +" tiles")
            return discard_pile
        else:
            discard_pile = self.game.discard_piles["land"]
            print("Identified the " +discard_pile.tile_back+ " discard pile, which still has " +str(len(discard_pile.tiles)) +" tiles")
            return discard_pile
    
    def choose_tiles(self, num_tiles):
        '''For a given number of tiles, select regular tiles from across the bags / tile_piles
        '''
        for tile_num in range(num_tiles):
            #Alternate between bags
            pile_num = tile_num % len(self.game.tile_piles)
            #Select the tile pile to draw from
            tile_pile = self.game.tile_piles[list(self.game.tile_piles.keys())[pile_num]] #WARNING - this isn't deterministic, so an undo that somehow changes the dict may get different results
            #Choose the next tile from the bag / pile and add it to their Chest
            tile_chosen = False
            num_bad_tiles = 0 #keep track of the number of unsuitable tiles, in case there are no suitable ones
            while not tile_chosen:
                if len(tile_pile.tiles) > num_bad_tiles: #check that there are at least some suitable tiles  
                    chosen_tile = tile_pile.tiles.pop()
                    if False:
                    # if (isinstance(chosen_tile, CityTile) 
                    #     or isinstance(chosen_tile, DisasterTile)):
                        tile_pile.tiles.insert(0, chosen_tile)
                        num_bad_tiles += 1
                    else:
                        tile_chosen = True
                        self.chest_tiles.append(chosen_tile)
                else:
                    break
            
    # Whether movement is possible is handled much like the Beginner mode, except that carrying no wealth increases upwind and land moves, and a dice roll can allow upwind movement
    def can_move(self, compass_point): 
        '''Before checking any further, make sure that the total possible moves havne't been used
        '''
        if not self.has_remaining_moves:
            return False
        
        #Check whether attack is possible
        if compass_point is None:
            if self.downwind_moves + self.land_moves + self.upwind_moves < self.max_downwind_moves:
                if len(self.current_tile.adventurers) > 1:
                    for adventurer in self.current_tile.adventurers:
                        if adventurer is not self and adventurer.wealth > 0:
                            return True
                if self.current_tile.agent:
                    if self.current_tile.agent not in self.agents_rested:
                        return True
        
        #Check whether rest is possible and otherwise give an extra opportunity to retreat
        if compass_point is None:
            if ((self.downwind_moves + self.land_moves + self.upwind_moves < self.max_upwind_moves + 1
                or self.downwind_moves + self.land_moves + self.upwind_moves < self.max_land_moves + 1)
                and self.downwind_moves + self.land_moves + self.upwind_moves < self.max_downwind_moves):
                return True #give an estra opportunity to retreat
                if self.current_tile.agent:
                    if self.current_tile.agent not in self.agents_rested:
                        return True
        
        # check that instruction is valid: a direction provided or an explicit general check through a None
        if compass_point is None:
            print("Adventurer is checking whether any movement at all is possible")
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
#        print("Adventurer is checking whether movement is possible over the " +compass_point
#              + " edge from their tile at " +str(self.current_tile.tile_position.longitude)+ "," 
#              + str(self.current_tile.tile_position.latitude))
        if self.game.movement_rules == "initial": #this version 1 of movement allows land and upwind movement only initially after resting
            moves_since_rest = self.land_moves + self.downwind_moves + self.upwind_moves
#            print("Adventurer has determined that they have moved " +str(moves_since_rest)+ " times since resting")
            if not self.current_tile.compass_edge_water(compass_point): #land movement needed
                if(moves_since_rest < self.max_land_moves 
                   or (self.wealth == 0 and moves_since_rest < self.max_land_moves_unburdened)):
                    return True
                else: return False
            elif (self.current_tile.compass_edge_water(compass_point) 
                  and self.current_tile.compass_edge_downwind(compass_point)): #downwind movement possible
                if (moves_since_rest < self.max_downwind_moves):
                    return True
                else: return False
            else: #if not land or downwind, then movement must be upwind
                if(moves_since_rest < self.max_upwind_moves
                   or (self.wealth == 0 and moves_since_rest < self.max_upwind_moves_unburdened)):
                    return True
                elif self.downwind_moves < self.max_downwind_moves:
#                     return None
                        return False
                else: return False
        elif self.game.movement_rules == "budgetted": #this version 2 of movement allows land and upwind movement any time, but a limited number before resting
            print("Adventurer has moved " +str(self.upwind_moves)+ " times upwind, " +str(self.land_moves)+ " times overland, and " +str(self.downwind_moves)+ " times downwind, since resting")
            if not self.current_tile.compass_edge_water(compass_point): #land movement needed
                if(self.land_moves < self.max_land_moves
                   or (self.wealth == 0 and self.land_moves < self.max_land_moves_unburdened)
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
                   or (self.wealth == 0 and self.upwind_moves < self.max_upwind_moves_unburdened))
                   and self.land_moves == 0):
                    return True
                elif self.downwind_moves < self.max_downwind_moves:
#                     return None
                    return False
                else: return False
        else: raise Exception("Invalid movement rules specified")
    
#    def move(self, compass_point):
#        '''Extends Beginnner movement to rotate Chest tiles after movement (for more comfortable visualisation)
#        '''
#        moved = super().move(compass_point)
#        if moved:
#            self.match_chest_directions()
#        return moved
    
    def match_chest_directions(self):
        '''Rotates all chest tiles to match the current tile's wind direction, for visualisation only.
        '''
        for chest_tile in self.chest_tiles:
            while not (chest_tile.wind_direction.north == self.current_tile.wind_direction.north and 
                       chest_tile.wind_direction.east == self.current_tile.wind_direction.east):
                chest_tile.rotate_tile_clock()
    
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
        
    def replenish_chest_tiles(self):
        '''If this Adventurer has fewer chest tiles than the max, then draw more
        '''
        #Count how many tiles they are short of the max chest tiles
        num_tiles_to_choose = self.num_chest_tiles - len(self.chest_tiles)
        #Add this many extra tiles to their chest
        self.choose_tiles(num_tiles_to_choose)
    
    def rechoose_chest_tiles(self):
        '''Checks whether the player will pay to replace all an Adventurer's chest tiles
        '''
        #Return current tiles to the bag / tile pile
        while self.chest_tiles:
            tile = self.chest_tiles.pop()
            relevant_pile = self.game.tile_piles[tile.tile_back]
            relevant_pile.tiles.insert(0, tile)
        #Replenish the empty Chest Tiles
        self.replenish_chest_tiles()
        
    def discover(self, tile):
        #check whether this is a discovered city and don't offer the usual
        if isinstance(self.current_tile, CityTile):
            self.current_tile.is_discovered = True
            self.wealth += self.game.value_discover_city
            self.current_tile.visit_city(self)
            return True
        else:
            super().discover(tile)
    
    def interact_tokens(self):
        #check whether there is an agent here and then check rest, attack if active or restore if dispossessed
        if self.current_tile.agent:
            agent = self.current_tile.agent
            if not agent.is_dispossessed:
                if agent.player == self.player:
                    if agent.wealth > 0:
                        if self.player.check_collect_wealth(agent):
                            self.collect_wealth()
                    if self.can_rest(agent):
                        if self.player.check_rest(self, agent):
                            self.rest(agent)
                else:
                    if self.can_rest(agent):
                        if self.player.check_rest(self, agent):
                            self.rest(agent)
                    if agent.wealth + self.value_dispossess_agent > 0:
                        if self.player.check_attack_agent(self, agent):
                            self.attack(agent)
            else:
                if (agent.player == self.player 
                    and self.wealth >= self.cost_agent_restore):
                    if self.player.check_restore_agent(self, agent):
                        self.restore_agent(agent)

        #check whether there is an adventurer here and attack if the player wants
        if self.current_tile.adventurers:
            for adventurer in self.current_tile.adventurers:
                if (adventurer.player != self.player 
                    and ((adventurer.wealth > 0 and not adventurer.pirate_token)
                         or (adventurer.pirate_token #cannot arrest pirates on Disaster Tiles
                             and not isinstance(self.current_tile, DisasterTile)))):
                    if self.player.check_attack_adventurer(self, adventurer):
                        self.attack(adventurer)
    
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
        '''Expands on AdventurerBeginner by preventing pirates resting with others' Agents
        '''
        #check whether this is a pirate and refuse them rest, unless they belong to the same player
        if self.pirate_token and not self.player == token.player:
            return False
        return super().can_rest(token)
    
    def attack(self, token):
        import random
        
        #Record the decision to attack this move
        self.attacked += 1
        
        success = False
        # have opponent roll for defence, roll for attack, compare rolls
        if random.random() < self.attack_success_prob:
            success = True
        
        # resolve conflict
        # check whether adventurer or agent
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
                    print(self.player.name+" successfully attacked "+token.player.name+"'s Adventurer.")
                    default_steal = adventurer.wealth//2 + adventurer.wealth%2
                    chosen_steal = None
                    while not chosen_steal in range(0, adventurer.wealth + 1):
                        chosen_steal = self.player.check_steal_amount(adventurer, adventurer.wealth, default_steal)
                    self.wealth += chosen_steal
                    adventurer.wealth -= chosen_steal
                    #Randomly steal chest tiles to top up
                    if isinstance(token, AdventurerRegular):
                        if 0 < len(self.chest_tiles) < self.num_chest_tiles:
                            victim_chest = token.chest_tiles
#                            self.chest_tiles.append(victim_chest.pop(random.randint(0, len(victim_chest)-1)))
                            stolen_tile = self.player.choose_tile(self, victim_chest)
                            victim_chest.remove(stolen_tile)
                            self.chest_tiles.append(stolen_tile)
        elif isinstance(token, Agent):
            if not token.is_dispossessed:
                self.pirate_token = True #just trying will make them a pirate
                if success:
                    print(self.player.name+" successfully attacked "+token.player.name+"'s Agent.")
                    agent = token
                    self.wealth += agent.wealth + self.value_dispossess_agent
                    agent.is_dispossessed = True
                    agent.wealth = 0;
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
        print(self.player.name+" successfully arrested "+pirate.player.name+"'s Adventurer.")
        self.wealth += self.value_arrest # get a reward
        pirate.end_expedition()
    
    def end_expedition(self, city=None):
        '''Extends to deal with piracy
        '''
        self.pirate_token = False
        return super().end_expedition(city)
    
    def check_tile_available(self, tile):
        '''Extends the AdventurerBeginner method to keep track of whether existing Agents have been dispossessed when placing on a tile
        '''
        if self.pirate_token:
            return False
        elif isinstance(tile, CityTile):
            return False
        elif tile.agent is None:
            return True
        elif tile.agent.is_dispossessed:
#            #This dispossessed Agent is about to be lost to its pla
#            tile.game.agents[tile.agent.player].remove(tile.agent)
#            tile.move_off_tile(agent)
            return True
        else:
            return False 
    
    def restore_agent(self, agent):
        #Record the decision to restor this move
        self.restored = True
        
        if agent.is_dispossessed:
            if self.cost_agent_restore <= self.wealth:
                print("Paying " +str(self.cost_agent_restore)+ " to restore " 
                      +agent.player.name+"'s Agent at position " 
                      +str(agent.current_tile.tile_position.longitude)
                     +","+ str(agent.current_tile.tile_position.latitude))
                self.wealth -= self.cost_agent_restore
                agent.is_dispossessed = False
                #Make sure that the Adventurer can't use this Agent this turn
                self.agents_rested.append(agent)
                return True
            else:
                print("Cannot afford to restore an agent")
                return False
        else:
            print("Didn't need to restore this Agent")
            return False

        
class CityTileRegular(CityTileBeginner):
    '''Extends the CityTileBeginner class to redeem Adventurers from piracy and to replenish Chest Tiles, and offer purchase of refreshed chest tiles
    '''
    
    def visit_city(self, adventurer, abandoned=False):
        '''Extends to redeem pirates, replenish Chest Tiles, and offer purchase of refreshed chest tiles
        '''
        #Cities provide the Adventurer with civilised clothes so they can be redeemed from piracy
        if adventurer.pirate_token:
            adventurer.pirate_token = False
        
        #Top up any missing chest tiles from the bags
        adventurer.replenish_chest_tiles()
        
        super().visit_city(adventurer, abandoned)
        
        if self.game.game_over or abandoned:
            return
        
        #Offer the chance to pay and completely swap out chest tiles
        while (adventurer.game.player_wealths[adventurer.player] >= self.game.cost_refresh_maps 
            and adventurer.player.check_buy_maps(adventurer)):
            adventurer.game.player_wealths[adventurer.player] -= self.game.cost_refresh_maps
            adventurer.rechoose_chest_tiles()
                

class AgentRegular(AgentBeginner):
    '''Extends the AgentBeginner class to keep track of information relevant in the Regular mode of Cartolan'''
    def __init__(self, game, player, tile):
        super().__init__(game, player, tile)
        # Need to keep track of whether this Agent has been dispossessed
        self.is_dispossessed = False
        
    def give_rest(self, adventurer):
        '''Takes into account whether Agents have been dispossessed, and replenishes chest tiles
        '''
        if self.is_dispossessed:
            return False
        else:
            adventurer.replenish_chest_tiles()
            return AgentBeginner.give_rest(self, adventurer)
        
    def manage_trade(self, adventurer):
        if self.is_dispossessed:
            return False
        else:
            super().manage_trade(adventurer)
            
    def dismiss(self):
        '''Takes this Agent off a tile fully and out of the game
        '''
        self.game.agents[self.player].remove(self)
        self.current_tile.move_off_tile(self)

class DisasterTile(Tile):
    '''***DEPRECATED*** Represents a Disaster Tile in the game Cartolan, which removes Adventurers' wealth and send them back to a city '''
    def move_onto_tile(self, token):
        '''Takes the wealth of non-Pirate Adventurers as they land on the tile, but allows pirates to move as if from land
        
        Arguments:
        Cartolan.Token for the Adventurer moving onto the tile
        '''
        if isinstance(token, Token):
            if isinstance(token, Adventurer):
                token.route.append(self)
                if not self in self.game.disaster_tiles:
                    self.game.disaster_tiles.append(self)
                else:
                    #if this has not just been discovered then the Adventurer isn't surprised and can become a pirate to survive
                    token.pirate_token = True
                # check if the Adventurer has a Pirate token
                if token.pirate_token:
                    print("Pirate moves onto disaster tile")
                    super().move_onto_tile(token)
#                    if token.player.check_court_disaster(token, self): # get player input on whether to attack the disaster
#                        self.attack_adventurer(token)
                else: # otherwise send the Adventurer to the capital and keep their wealth and end their turn 
                    print("Adventurer moved onto disaster tile. Dropping wealth and returning to last city visited.")
                    self.dropped_wealth += token.wealth
                    token.end_expedition()
            elif isinstance(token, Agent): 
                print("Tried to add Agent to a disaster tile")
                return False
        else: raise Exception("Tried to move something other than a token onto a tile")
    
    def attack_adventurer(self, adventurer):
        '''Checks whether a Player wants to try and recover wealth taken by the tile
        
        Arguments:
        Cartolan.Adventurer for the Adventurer token that is on the tile
        '''
#        import random
#        
#        # if the rolls are the same then the pirate gets helf the wealth
#        if random.random() < self.game.attack_success_prob:
#            adventurer.wealth += self.dropped_wealth//2 + self.dropped_wealth%2
#        else: # otherwise send the Adventurer to the capital and keep their wealth
#            self.dropped_wealth += adventurer.wealth
#            adventurer.end_expedition()
            
    def compare(self, tile):
        if not isinstance(tile, DisasterTile):
            return False
        else:
            return super().compare(tile)

class CapitalTileRegular(CityTileRegular):
    def __init__(self, game, tile_back = "water"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(True,True,True,True)):
        super().__init__(game, wind_direction, tile_edges, True, True)

class MythicalTileRegular(CityTileRegular):
    def __init__(self, game, tile_back = "land"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(False,False,False,False)):
        super().__init__(game, wind_direction, tile_edges, False, False)