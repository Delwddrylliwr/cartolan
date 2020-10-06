from base import Adventurer, Agent, Tile, TileEdges
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
        
        #Unburdened movement is deprecated in Regular mode, see Advanced mode below
        self.max_upwind_moves_unburdened = self.max_upwind_moves
        self.max_land_moves_unburdened = self.max_land_moves
        
        #Record some additional instructions
        self.attacked = 0
        self.restored = False
    
    def choose_pile(self, compass_point):
        # establish which pile to draw from, based on the edge being moved over from the preceding tile
        if self.current_tile.compass_edge_water(compass_point):
            tile_pile = self.game.tile_piles["water"]
            print("Identified the " +tile_pile.tile_back+ " tile pile, which still has " +str(len(tile_pile.tiles)) +" tiles")
            return tile_pile
        else:
            tile_pile = self.game.tile_piles["land"]
            print("Identified the " +tile_pile.tile_back+ " tile pile, which still has " +str(len(tile_pile.tiles)) +" tiles")
            return tile_pile
    
    def choose_discard_pile(self, compass_point):
        # establish which pile to draw from, based on the edge being moved over from the preceding tile
        if self.current_tile.compass_edge_water(compass_point):
            discard_pile = self.game.discard_piles["water"]
            print("Identified the " +discard_pile.tile_back+ " discard pile, which still has " +str(len(discard_pile.tiles)) +" tiles")
            return discard_pile
        else:
            discard_pile = self.game.discard_piles["land"]
            print("Identified the " +discard_pile.tile_back+ " discard pile, which still has " +str(len(discard_pile.tiles)) +" tiles")
            return discard_pile
            
    # Whether movement is possible is handled much like the Beginner mode, except that carrying no wealth increases upwind and land moves, and a dice roll can allow upwind movement
    def can_move(self, compass_point): 
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
        print("Adventurer is checking whether movement is possible over the " +compass_point
              + " edge from their tile at " +str(self.current_tile.tile_position.latitude)+ "," 
              + str(self.current_tile.tile_position.longitude))
        if self.game.movement_rules == "initial": #this version 1 of movement allows land and upwind movement only initially after resting
            moves_since_rest = self.land_moves + self.downwind_moves + self.upwind_moves
            print("Adventurer has determined that they have moved " +str(moves_since_rest)+ " times since resting")
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
    
    def interact_tokens(self):
        #check whether there is an agent here and then check rest, attack if active or restore if dispossessed
        if self.current_tile.agent:
            agent = self.current_tile.agent
            if not agent.is_dispossessed:
                if agent.player == self.player:
                    if agent.wealth > 0:
                        if self.player.check_collect_wealth(agent):
                            self.collect_wealth()
                if self.player.check_rest(self, agent):
                    self.rest()
                if agent.player != self.player and agent.wealth > 0:
                    if self.player.check_attack_agent(self, agent):
                        self.attack(agent)
            else:
                if self.player.check_restore_agent(self, agent):
                    self.restore_agent(agent)

        #check whether there is an adventurer here and attack if the player wants
        if self.current_tile.adventurers:
            for adventurer in self.current_tile.adventurers:
                if adventurer.player != self.player and (adventurer.wealth > 0 or adventurer.pirate_token):
                    if self.player.check_attack_adventurer(self, adventurer):
                        self.attack(adventurer)
    
    def trade(self, tile):
        '''Expands on the trading of an AdventurerBeginner, by checking for pirates and refusing them trade
        
        Arguments
        tile should be a Cartolan.Tile
        '''
        #check whether this is a pirate and refuse them trade
        if self.pirate_token:
            return False
        
        return super().trade(tile)
    
    def rest(self):
        '''Expands on the resting of an AdventurerBeginner, by checking for pirates and refusing them rest
        '''
        #check whether this is a pirate and refuse them rest, unless they belong to the same player
        if self.pirate_token and not self.player == self.current_tile.agent.player:
            return False
        return super().rest()
    
    def attack(self, token):
        import random
        
        #Record the decision to attack thsi move
        self.attacked += 1
        
        self.pirate_token = True # will take away later if this was a pirate
        success = False
        # have opponent roll for defence, roll for attack, compare rolls
        if random.random() < self.game.ATTACK_SUCCESS_PROB:
            success = True
        
        # resolve conflict
        # check whether adventurer or agent
        if isinstance(token, Adventurer):
            adventurer = token
            # check whether the defender adventurer is a pirate, and remove the pirate token
            if adventurer.pirate_token:
                self.pirate_token = False # lose own pirate status for conducting arrest
                # arrest them
                if success:
                    adventurer.wealth = 0
#                     self.player.vault_wealth += self.game.VALUE_ARREST # get a reward straight to the Vault
                    self.wealth += self.game.VALUE_ARREST # get a reward
                    adventurer.current_tile.move_off_tile(adventurer)
                    adventurer.latest_city.move_onto_tile(adventurer) # send them back to their last city
                    adventurer.pirate_token = False # remove their pirate token
                    adventurer.wonders_visited = [] #reset the list of wonders that they've already stocked goods from
            else: # rob them
                if success:
                    self.wealth += adventurer.wealth//2 + adventurer.wealth%2
                    adventurer.wealth //= 2    
        elif isinstance(token, Agent):
            if not token.is_dispossessed:
                if success:
                    agent = token
                    self.wealth += agent.wealth + self.game.VALUE_DISPOSSESS_AGENT
                    agent.is_dispossessed = True
                    agent.wealth = 0;
        else: raise Exception("Not able to deal with this kind of token.")
        
        self.player.attack_history.append([self.current_tile, success])
        return success
    
    def check_tile_available(self, tile):
        '''Extends the AdventurerBeginner method to keep track of whether existing Agents have been dispossessed when placing on a tile'''
        if tile.agent is None:
            return True
        elif tile.agent.is_dispossessed:
            return True
        else:
            return False 
    
    def restore_agent(self, agent):
        #Record the decision to restor this move
        self.restored = True
        
        if agent.is_dispossessed:
            if self.game.COST_AGENT_RESTORE <= self.wealth:
                print("Paying " +str(self.game.COST_AGENT_RESTORE)+ " to restore " 
                      +agent.player.colour+"'s Agent at position " 
                      +str(agent.current_tile.tile_position.latitude)
                     +","+ str(agent.current_tile.tile_position.longitude))
                self.wealth -= self.game.COST_AGENT_RESTORE
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
    '''Extends the CityTileBeginner class to redeem Adventurers from piracy'''
    def visit_city(self, adventurer):
        #Cities provide the Adventurer with civilised clothes so they can be redeemed from piracy
        if adventurer.pirate_token:
            adventurer.pirate_token = False
        
        super().visit_city(adventurer)
                

class AgentRegular(AgentBeginner):
    '''Extends the AgentBeginner class to keep track of information relevant in the Regular mode of Cartolan'''
    def __init__(self, game, player, tile):
        super().__init__(game, player, tile)
        # Need to keep track of whether this Agent has been dispossessed
        self.is_dispossessed = False
        
    def give_rest(self, adventurer):
        if self.is_dispossessed:
            return False
        else:
            super().give_rest(adventurer)
        
    def manage_trade(self, adventurer):
        if self.is_dispossessed:
            return False
        else:
            super().manage_trade(adventurer)

class DisasterTile(Tile):
    '''Represents a Disaster Tile in the game Cartolan, which removes Adventurers' wealth and send them back to a city '''
    def __init__(self, game, tile_back, wind_direction):
        super().__init__(game, tile_back, wind_direction
                         , TileEdges(False, False, False, False), False)
        self.dropped_wealth = 0
    
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
                # check if the Adventurer has a Pirate token
                if token.pirate_token:
                    print("Pirate moves onto disaster tile")
                    super().move_onto_tile(token)
                    if token.player.check_court_disaster(token, self): # get player input on whether to attack the disaster
                        self.attack_adventurer(token)
                else: # otherwise send the Adventurer to the capital and keep their wealth and end their turn 
                    print("Adventurer moved onto disaster tile. Dropping wealth and returning to last city visited.")
                    self.dropped_wealth += token.wealth
                    token.wealth = 0
                    token.latest_city.move_onto_tile(token)
                    token.wonders_visited = []
                    #End the Adventurer's turn and reset their moves
                    token.land_moves = 0
                    token.downwind_moves = 0
                    token.upwind_moves = 0
                    token.turns_moved += 1
            elif isinstance(token, Agent): 
                print("Tried to add Agent to a disaster tile")
                return False
        else: raise Exception("Tried to move something other than a token onto a tile")
    
    def attack_adventurer(self, adventurer):
        '''Checks whether a Player wants to try and recover wealth taken by the tile
        
        Arguments:
        Cartolan.Adventurer for the Adventurer token that is on the tile
        '''
        import random
        
        # if the rolls are the same then the pirate gets helf the wealth
        if random.random() < self.game.ATTACK_SUCCESS_PROB:
            adventurer.wealth += self.dropped_wealth//2 + self.dropped_wealth%2
        else: # otherwise send the Adventurer to the capital and keep their wealth
            self.dropped_wealth += adventurer.wealth
            adventurer.wealth = 0
            adventurer.current_tile.move_off_tile(adventurer)
            adventurer.latest_city.move_onto_tile(adventurer)
            #End the Adventurer's turn so that movement resets
            adventurer.end_turn()