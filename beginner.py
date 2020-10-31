from base import Adventurer, Agent, CityTile, Tile

class AdventurerBeginner(Adventurer):
    '''Representing an Adventurer token with the movement and action possibilities from Beginner mode of Cartolan
    
    Methods:
    __init__ taking Game, Player, and CityTile objects from the Cartolan module
    can_move taking a string compass point
    exploration_needed taking two Int coordinates
    choose_pile
    choose_discard_pile
    move taking a string compass point
    wait
    explore taking two Int coordinates
    discover taking a Tile
    trade taking a Tile
    place_agent taking a Tile
    can_rest
    rest
    can_collect_wealth
    collect_wealth
    '''
    def __init__(self, game, player, starting_city):
        super().__init__(game, player, starting_city)
        
        print("adding an adventurer for " +str(player.colour)+ " player")
        
        self.max_exploration_attempts = game.EXPLORATION_ATTEMPTS
        self.max_downwind_moves = game.MAX_DOWNWIND_MOVES
        self.max_land_moves = game.MAX_LAND_MOVES
        self.max_upwind_moves = game.MAX_UPWIND_MOVES
        
        #Some variables that determine valid moves
        self.downwind_moves = 0
        self.upwind_moves = 0
        self.land_moves = 0
        self.turns_moved = 0
        self.latest_city = starting_city
        self.wonders_visited = []
        self.agents_rested = []
        
        #Some records of actions taken each move
        self.moved = None
        self.traded = False
        self.rested = False
        self.collected = False
        self.placed = False
        self.banked = False
        self.bought_adventurer = 0
        self.bought_agent = 0 #@TODO this variable may need to store different information
        self.moved_agent = None #@TODO this variable may need to store different information
    
    
    def can_move(self, compass_point):
        '''confirm whether the Adventurer can move in a given cardinal compass direction
        
        key arguments:
        String word or letter cardinal compass direction
        '''
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
              + " edge from their tile at " +str(self.current_tile.tile_position.longitude)+ "," 
              + str(self.current_tile.tile_position.latitude))
        if self.game.movement_rules == "initial": #this version 1 of movement allows land and upwind movement only initially after resting
            moves_since_rest = self.land_moves + self.downwind_moves + self.upwind_moves
            print("Adventurer has determined that they have moved " +str(moves_since_rest)+ " times since resting")
            if not self.current_tile.compass_edge_water(compass_point): #land movement needed
                if(moves_since_rest < self.max_land_moves):
                    return True
            elif (self.current_tile.compass_edge_water(compass_point) 
                  and self.current_tile.compass_edge_downwind(compass_point)): #downwind movement possible
                if (moves_since_rest < self.max_downwind_moves):
                    return True
            else: #if not land or downwind, then movement must be upwind
                if(moves_since_rest < self.max_upwind_moves):
                    return True
                else: return False
        elif self.game.movement_rules == "budgetted": #this version 2 of movement allows land and upwind movement any time, but a limited number before resting
            print("Adventurer has moved " +str(self.upwind_moves)+ " times upwind, " +str(self.land_moves)+ " times overland, and " +str(self.downwind_moves)+ " times downwind, since resting")
            if not self.current_tile.compass_edge_water(compass_point): #land movement needed
                if(self.land_moves < self.max_land_moves and self.upwind_moves == 0):
                    return True
            elif (self.current_tile.compass_edge_water(compass_point) 
                  and self.current_tile.compass_edge_downwind(compass_point)): #downwind movement possible
                if (self.downwind_moves + self.land_moves + self.upwind_moves < self.max_downwind_moves):
                    return True
            else: #if not land or downwind, then movement must be upwind
                if(self.upwind_moves < self.max_upwind_moves and self.land_moves == 0):
                    return True
                else: return False
        else: raise Exception("Invalid movement rules specified")
        
    
    def exploration_needed(self, longitude, latitude):
        '''check whether there is a tile already in a given space, or if exploration is needed
        
        key arguments:
        int longitude
        int latitude
        '''
        return self.game.play_area.get(longitude) is None or self.game.play_area.get(longitude).get(latitude) is None
        
    def choose_pile(self, compass_point):
        ''' establish which pile to draw from - always the water tile in beginner mode'''
        tile_pile = self.game.tile_piles["water"]
        print("Identifying the " +tile_pile.tile_back+ " tile pile, which still has " +str(len(tile_pile.tiles)) +" tiles")
        return tile_pile
    
    def choose_discard_pile(self, compass_point):
        ''' establish which pile to draw from - always the water tile in beginner mode'''
        discard_pile = self.game.discard_piles["water"]
        print("Identifying the " +discard_pile.tile_back+ " discard pile, which still has " +str(len(discard_pile.tiles)) +" tiles")
        return discard_pile 
    
    def interact_tokens(self):
        #check whether there is an agent here and then check rest
        if self.current_tile.agent:
            agent = self.current_tile.agent
            if agent.player == self.player:
                if agent.wealth > 0:
                    if self.player.check_collect_wealth(agent):
                        self.collect_wealth()
            if self.player.check_rest(self, agent):
                self.rest()
    
    def interact_tile(self):
        #check whether this is a city and remember the visit
        if isinstance(self.current_tile, CityTile):
            self.current_tile.visit_city(self)

        #check whether this is a wonder, and if the player wants to trade
        if self.current_tile.is_wonder:
            if self.player.check_trade(self, self.current_tile):
                self.trade(self.current_tile)
        
        #interact with any Tokens on the tile, Adventurers or other Agents
        
    def end_turn(self):
        self.turns_moved += 1
        #the adventurer will rest now before the next turn and be ready
        self.downwind_moves = 0
        self.land_moves = 0
        self.upwind_moves = 0
        #the list of agents rested with is reset
        self.agents_rested = []
    
    
    def move(self, compass_point):        
        '''move the Adventurer over the tile edge in a given cardinal compass direction
        
        key arguments:
        String word or letter cardinal compass direction
        '''
        #Reset records of actions taken from the previous move and record the direction of movement
        self.moved = compass_point # even if exlploration fails this still counts as a move
        self.traded = False
        self.rested = False
        self.collected = False
        self.placed = False
        self.banked = False
        self.bought_adventurer = 0
        self.bought_agent = 0 #@TODO this variable may need to store different information
        self.moved_agent = None #@TODO this variable may need to store different information
        
        # check whether the next tile exists and explore if needed, movement rules can be either "initial" or "budgetted"
        moved = False
        if self.can_move(compass_point):
            #include this in the number of moves so far since resting - even if exploration subsequently fails
            if not self.current_tile.compass_edge_water(compass_point): #land movement
                print("Making a land move")
                self.land_moves += 1
            elif self.current_tile.compass_edge_downwind(compass_point): #downwind movement possible
                print("Making a downwind water move")
                self.downwind_moves += 1
            else: #if not land or downwind, then movement must have been upwind
                print("Making an upwind water move")
                self.upwind_moves += 1
            
            #locate the space in the play area that the Adventurer is moving into
            longitude_increment = int(compass_point.lower() in ["east","e"]) - int(compass_point.lower() in ["west","w"])
            new_longitude = self.current_tile.tile_position.longitude + longitude_increment
            latitude_increment = int(compass_point.lower() in ["north","n"]) - int(compass_point.lower() in ["south","s"])
            new_latitude = self.current_tile.tile_position.latitude + latitude_increment

            #is this an existing tile or is exploration needed?
            if self.exploration_needed(new_longitude, new_latitude):
                # establish which pile to draw from - always the water tile in beginner mode
                tile_pile = self.choose_pile(compass_point)
                discard_pile = self.choose_discard_pile(compass_point)
                
                if self.explore(tile_pile, discard_pile, new_longitude, new_latitude, compass_point):
                    #place the Adventurer on the newly placed Tile
                    self.current_tile.move_off_tile(self)
                    self.current_tile = self.game.play_area.get(new_longitude).get(new_latitude)
                    self.current_tile.move_onto_tile(self)
                    
                    # if this is a Wonder then discovery should be automatic
#                     if isinstance(self.current_tile, WonderTile):
                    if self.current_tile.is_wonder:
                        self.discover(self.current_tile)             
                
                    #check whether an agent can be placed and then whether the player wants to
                    self.place_agent()
                    
                    moved = True
                
            else:
                #place the Adventurer on the next existing Tile
                self.current_tile.move_off_tile(self)
                self.current_tile = self.game.play_area.get(new_longitude).get(new_latitude)
                self.current_tile.move_onto_tile(self)
                #carry out any actions that are possible given this tile or tokens on it
                self.interact_tile()                
                self.interact_tokens()
                
                moved = True
        
        #check whether any more moves will be possible
        if not self.can_move(None):
            print("Adventurer determined that cannot move any more, so finishing turn")
            self.end_turn()
        
        return moved #even if exlploration fails this still counts as a move
        
    
    def wait(self):
        '''Allows the Adventurer to just wait in place rather than moving, to end a turn early'''
        print("Adventurer is choosing to wait in place")
        #Reset records of actions taken from previous move, and record that this was a choice to wait in place
        self.moved = "wait"
        self.traded = False
        self.rested = False
        self.collected = False
        self.placed = False
        self.banked = False
        self.bought_adventurer = 0
        self.bought_agent = 0 #@TODO this variable may need to store different information
        self.moved_agent = None #@TODO this variable may need to store different information        
        
        #Treat this as if it was a move
        self.downwind_moves += 1
        
        #carry out any actions that are possible given this tile or tokens on it
        self.interact_tile()
        self.interact_tokens()
        
        if not self.can_move(None):
            print("Adventurer determined that cannot move any more, so finishing turn")
            self.end_turn()
        
        return True
    
    def get_adjoining_edges(self, longitude, latitude):
        '''for a given set of coordinates, gets the adjoining edges from the neighbouring tiles, if any'''
        adjoining_edges_water = {"n":None, "e":None, "s":None, "w":None}
        for longitude_increment in [- 1, 1]:
            if not self.game.play_area.get(longitude + longitude_increment) is None:
                neighbour_tile = self.game.play_area.get(longitude + longitude_increment).get(latitude)
                if not neighbour_tile is None:
                    #for the tile -1 longitude it will be the eastern edge that is relevant
                    if longitude_increment == -1:
                        adjoining_edges_water["w"] = neighbour_tile.compass_edge_water("east")
                    else:
                        adjoining_edges_water["e"] = neighbour_tile.compass_edge_water("west")
        for latitude_increment in [- 1, 1]:
            if not self.game.play_area.get(longitude) is None:
                neighbour_tile = self.game.play_area.get(longitude).get(latitude + latitude_increment)
                if not neighbour_tile is None:
                    #for the tile -1 latitude it will be the northern edge that is relevant
                    if latitude_increment == -1:
                        adjoining_edges_water["s"] = neighbour_tile.compass_edge_water("north")
                    else:
                        adjoining_edges_water["n"] = neighbour_tile.compass_edge_water("south")
        print("Identified adjoining edges as, North: " +str(adjoining_edges_water["n"])+ ", East: " +str(adjoining_edges_water["e"])
              + ", South: " +str(adjoining_edges_water["s"])+ ", West: " +str(adjoining_edges_water["w"]))
        return adjoining_edges_water
    
    def get_exploration_value(self, adjoining_edges_water, compass_point_moving):
        '''calculate the score that would come from filling a particular gap in the map'''
        num_adjacent_water = 0
        num_adjacent_land = 0
        for compass_point in ['n', 'e', 's', 'w']:
            if adjoining_edges_water[compass_point]:
                num_adjacent_water += 1
            elif adjoining_edges_water[compass_point] is not None: 
                num_adjacent_land += 1
        #Exclude the edge over which the Adventurer is moving
        if self.current_tile.compass_edge_water(compass_point_moving):
            num_adjacent_water -= 1
        else:
            num_adjacent_land -= 1
        
        #Calculate the score this represents
        exploration_value = self.game.VALUE_FILL_MAP_GAP[num_adjacent_water][num_adjacent_land]
        print(self.player.colour+" the gap in the  map is adjacent to " +str(num_adjacent_water)
              + " water tiles and " +str(num_adjacent_land)+ " land tiles, and is worth " 
              +str(exploration_value))
        return exploration_value
        
    
    def explore(self, tile_pile, discard_pile, longitude, latitude, compass_point_moving):        
        '''Randomly tries and suitably places a Tile where an Adventurer moves into a space with no Tile
        
        key arguments:
        TilePile the tile of piles that should be drawn from given the edge that is being moved over.
        TilePile the corresponding discard pile for unsuitable tiles
        int the longitude of the space to explore
        int the latitude of the space to explore
        String giving the word or letter for cardinal compass direction from which the Adventurer is moving
        '''
        print("Exploring to the " +compass_point_moving+ " into the slot at " +str(longitude)+ "," +str(latitude)+ " which has edges...")
        
        #establish what edges adjoin the given space
        adjoining_edges_water = self.get_adjoining_edges(longitude, latitude)
        
        # take multiple attempts at drawing a suitable tile from the pile
        for attempt in range(0, self.max_exploration_attempts):
            if tile_pile.tiles:
                print("Drawing a tile from the " +tile_pile.tile_back+ " tile deck, which has " +str(len(tile_pile.tiles))+ " tiles")
                potential_tile = tile_pile.draw_tile()
            elif discard_pile.tiles:
                print("Have found main tile pile empty, so shuffling Discard Pile")
                self.game.refresh_pile(tile_pile, discard_pile)
                tile_pile = self.game.tile_piles[tile_pile.tile_back]
                discard_pile = self.game.discard_piles[discard_pile.tile_back]
                potential_tile = tile_pile.draw_tile()
            else: #the game is over, and so this exploration and the turn too
                self.turns_moved += 1
                self.game.game_over = True
                break
            print("Have drawn a tile with edges N:" +str(potential_tile.compass_edge_water("n"))
                  +";E:"+str(potential_tile.compass_edge_water("e"))
                  +";S:"+str(potential_tile.compass_edge_water("s"))
                  +";W:"+str(potential_tile.compass_edge_water("w"))
                  + " and with wind direction N:" +str(potential_tile.wind_direction.north)
                  +";E:"+str(potential_tile.wind_direction.east))
            # rotate it to the orientation of the current tile
            def null():
                pass
            while not (potential_tile.wind_direction.north == self.current_tile.wind_direction.north and 
                       potential_tile.wind_direction.east == self.current_tile.wind_direction.east):
                potential_tile.rotate_tile_clock()
            print("...after rotating to match wind, it has edges N:" +str(potential_tile.compass_edge_water("n"))
                  +";E:"+str(potential_tile.compass_edge_water("e"))
                  +";S:"+str(potential_tile.compass_edge_water("s"))
                  +";W:"+str(potential_tile.compass_edge_water("w"))
                  + " and wind direction N:" +str(potential_tile.wind_direction.north)
                  +";E:"+str(potential_tile.wind_direction.east))
            
            # check whether the tile will place, rotating as needed
            if self.game.exploration_rules == "clockwise": # this version 1 of exploration rules will just try a clockwise rotation and then an anti
                rotations = [null, potential_tile.rotate_tile_anti, potential_tile.rotate_tile_clock] # remember these will pop in reverse order, print used as a null function that will do nothing to the potential tile
            elif  self.game.exploration_rules == "continuous": # this version 2 of the exploration rules will try to line up arrows head to toe as a first preference 
                #the rotation will be anti first if the wind direction is north-east or south-west and the movement is north or south
                if ((self.current_tile.wind_direction.north and self.current_tile.wind_direction.east) 
                    or (not self.current_tile.wind_direction.north and not self.current_tile.wind_direction.east)):
                    if compass_point_moving in ["n","s"]:
#                         rotations = [null, potential_tile.rotate_tile_clock, potential_tile.rotate_tile_anti]
                        rotations = [null, potential_tile.rotate_tile_anti]
                    else:
#                         rotations = [null, potential_tile.rotate_tile_anti, potential_tile.rotate_tile_clock]
                        rotations = [null, potential_tile.rotate_tile_clock]
                #the rotation will be anti first if the wind direction is north-west or south-east and the movement is west or east
                elif ((self.current_tile.wind_direction.north and not self.current_tile.wind_direction.east) 
                    or (not self.current_tile.wind_direction.north and self.current_tile.wind_direction.east)):
                    if compass_point_moving in ["n","s"]:
#                         rotations = [null, potential_tile.rotate_tile_anti, potential_tile.rotate_tile_clock]
                        rotations = [null, potential_tile.rotate_tile_clock]
                    else:
#                         rotations = [null, potential_tile.rotate_tile_clock, potential_tile.rotate_tile_anti]
                        rotations = [null, potential_tile.rotate_tile_anti]
                else: raise Exception("Failed to exhaust wind directions")
            
            while len(rotations) > 0:
                compass_points = ["n", "e", "s", "w"]
                edge_matches = True
                while edge_matches and len(compass_points) > 0:
                    compass_point = compass_points.pop()
                    print("checking tile matches on the " +compass_point.upper()+ ", where an adjoining edge of "
                         +str(adjoining_edges_water[compass_point])+ " must match with the tile's "
                          + str(potential_tile.compass_edge_water(compass_point)))
                    edge_matches = adjoining_edges_water[compass_point] is None or adjoining_edges_water[compass_point] == potential_tile.compass_edge_water(compass_point)

                if edge_matches:
                    # place tile and feed back to calling function that tile has been placed
                    potential_tile.place_tile(longitude, latitude)
                    # if this filled a gap in the map then award the Adventurer accordingly 
                    self.wealth += self.get_exploration_value(adjoining_edges_water, compass_point_moving)
                    return True
                else:
                    #return the tile to the same wind direction as the original
                    while not (potential_tile.wind_direction.north == self.current_tile.wind_direction.north and 
                           potential_tile.wind_direction.east == self.current_tile.wind_direction.east):
                        potential_tile.rotate_tile_anti()
                    # rotate the tile according to the alternative options in the exploration method
                    rotations.pop()()
                    print("rotated tile, so that its wind points N:" +str(potential_tile.wind_direction.north)
                         + ";E:"+ str(potential_tile.wind_direction.east))
            # discard the tile
            discard_pile.add_tile(potential_tile)
            self.game.exploration_attempts += 1
            
            
        # feed back to calling function that a tile has NOT been placed
        print("Exploration failed")
        self.game.num_failed_explorations += 1
        return False
            
        
    def discover(self, tile):
        '''awards an extra bonus when exploration first reveals a Wonder tile
        
        key arguments:
        Cartolan.Tile giving the Wonder Tile that has just been discoverred.
        '''
        #check whether this tile is inside a city's domain, four or less tiles from it by taxi norm, and just trade instead if so
        for city_tile in self.game.cities:
            city_longitude = city_tile.tile_position.longitude
            city_latitude = city_tile.tile_position.latitude
            if (abs(tile.tile_position.longitude - city_longitude) 
                + abs(tile.tile_position.latitude - city_latitude) <= self.game.CITY_DOMAIN_RADIUS):
                self.trade(tile)
                return False
        
        #award wealth
        self.wealth += self.game.VALUE_DISCOVER_WONDER[tile.tile_back]
        self.wonders_visited.append(tile)
        return True
        
        
    def trade(self, tile):
        '''awards wealth when a Wonder tile is visited for the first time since the last visit to a city
        
        key arguments:
        Cartolan.Tile giving the tile that has been visited
        '''
        #Record the instruction to Trade
        self.traded = True
        
        #confirm that this tile is a Wonder
#         if isinstance(tile, WonderTile):
        if not tile.is_wonder:
            return False
        
        # check that Adventurer hasn't visited this Wonder yet, since visiting a city
        if tile in self.wonders_visited:
            return False
        
        # check whether there is an Agent on the tile
        if not tile.agent is None:
            tile.agent.manage_trade(self)
        
        # collect appropriate wealth into Chest
        print("Adventurer is trading on tile " 
                  +str(tile.tile_position.longitude)+ "," +str(tile.tile_position.latitude))
        self.wealth += self.game.VALUE_TRADE
        
        # keep track of visiting this Wonder
        self.wonders_visited.append(tile)
        
        return True
    
    def check_tile_available(self, tile):
        '''Checks the conditions for being able to place an Agent on a tile.'''
        if tile.agent is None:
            return True
        else:
            return False
    
    def place_agent(self):
        '''places an Agent as a tile is first placed through exploration'''
        #Record the instruction to place
        self.placed = True
        
        tile = self.current_tile
        #@DEPRECATED city tile domains are no longer a feature
        #check whether this tile is inside a city's domain, four or less tiles from it by taxi norm
        for city_tile in self.game.cities:
            city_longitude = city_tile.tile_position.longitude
            city_latitude = city_tile.tile_position.latitude
            if (abs(tile.tile_position.longitude - city_longitude) 
                + abs(tile.tile_position.latitude - city_latitude) <= self.game.CITY_DOMAIN_RADIUS):
                return False
        
        #check that the adventurer has requisite wealth in their Chest
        if self.wealth >= self.game.COST_AGENT_EXPLORING and self.check_tile_available(tile):
            
            #check whether the player actually wants to place an agent, even if they have to move an existing one
            if self.player.check_place_agent(self):
                if len(self.player.agents) >= self.game.MAX_AGENTS:
                    agent = self.player.check_move_agent(self)
                    if agent is None:
                        return False
                    else:
                        #pick up the Agent from its existing tile if there are no other agents available
                        #otherwise get a new agent
                        agent.current_tile.move_off_tile(agent)
                        tile.move_onto_tile(agent)
                else:
                    agent = self.game.AGENT_TYPE(self.game, self.player, tile)
                #check whether the tile already has an active Agent
                self.wealth -= self.game.COST_AGENT_EXPLORING
                #Rest this adventurer
#                 self.rest()
#                 #End this Adventurer's turn
#                 print("Adventurer has placed an Agent and must end their turn to set them up")
#                 self.turns_moved += 1
                #prevent the Adventurer using the Agent this turn
                self.agents_rested.append(agent)
#                 #the adventurer will rest now before the next turn and be ready
#                 self.downwind_moves = 0
#                 self.land_moves = 0
#                 self.upwind_moves = 0
                return True
        else: return False
            
    
    def can_rest(self):
        '''checks whether the Adventurer can rest with an Agent on this tile'''
        tile = self.current_tile
        # check whether there is an agent on the tile
        if tile.agent is None:
            return False
        
        # can the adventurer afford rest here?
        if tile.agent.player == self.player or self.wealth > self.game.COST_AGENT_REST:
            return True
        else:
            return False
    
    
    def rest(self):
        '''rests with an Agent if there is one on the tile'''
        #Record the instruction to rest
        self.rested = True
        
        tile = self.current_tile
        # check whether there is an agent on the tile
        if tile.agent is None:
            return False
        
        # use the agent if there is enough Chest wealth to
        if tile.agent.player == self.player or self.wealth >= self.game.COST_AGENT_REST:
            print("Adventurer is resting with the agent on tile " 
                  +str(tile.tile_position.longitude)+ "," +str(tile.tile_position.latitude))
            tile.agent.give_rest(self)
            return True
        else:
            return False

    
    def can_collect_wealth(self):
        '''checks whether there is wealth with an Agent on the current tile that can be collected'''
        tile = self.current_tile
        #check whether there is an agent on the tile
        if tile.agent is None:
            return False
        #check that the agent shares a player
        if tile.agent.player == self.player and tile.agent.wealth > 0:
            return True
        else:
            return False
        

    def collect_wealth(self):
        '''Collects any wealth that is with any Agent of the same player on the current tile'''
        #Record the instruction to collect
        self.collected = True
        
        tile = self.current_tile
        #check whether there is an agent on the tile
        if tile.agent is None:
            return False
        else:
            #check that the agent shares a player
            agent = tile.agent
            if tile.agent.player == self.player:
                #transfer wealth
                print("Adventurer is collecting " +str(agent.wealth)+ " wealth from the agent on tile "
                     +str(agent.current_tile.tile_position.longitude)+","+str(agent.current_tile.tile_position.latitude))
                self.wealth += agent.wealth
                agent.wealth = 0
                return True
            else:
                return False
        
# Unit test, collects wealth from wonder tile

# Unit test, cannot place mismatched tiles - all land next to a water

# Unit test, rotation clockwise then anticlockwise returns wind direction and compass edges
# tile = Tile(Game([Player(),Player()]),wind_direction=WindDirection(True,True),tile_edges = TileEdges(True, False, False, False))
# print(str(tile.wind_direction.north)+str(tile.wind_direction.east))
# rotations = [print, tile.rotate_tile_anti, tile.rotate_tile_clock]
# print(str(tile.wind_direction.north)+str(tile.wind_direction.east))
# rotations.pop()()
# print(str(tile.wind_direction.north)+str(tile.wind_direction.east))
# print(str(tile.compass_edge_water("w")))
# rotations.pop()()
# print(str(tile.wind_direction.north)+str(tile.wind_direction.east))
# print(str(tile.compass_edge_water("w")))
# rotations.pop()()
# print(str(tile.wind_direction.north)+str(tile.wind_direction.east))


class AgentBeginner(Agent):
    '''Represents Agent tokens with their behaviours for Beginner mode of the game Cartolan
    
    Methods:
    __init__ takes Cartolan.Game, Cartolan.Player, and Cartolan.Tile objects
    give_rest takes a Cartolan.Adventurer
    manage_trade takes a Cartolan.Adventurer
    '''
    def __init__(self, game, player, tile):
        super().__init__(game, player, tile)
    
    def give_rest(self, adventurer):
        '''Resets the move counts for an Adventurer token, so that they can continue to move
        
        Arguments:
        Cartolan.Adventurer the Adventurer to rest
        '''
        #check whether Adventurer has rested with this agent already this turn
        if self in adventurer.agents_rested:
            return False
        
        #check whether Adventurer is from same player and charge if other player
        if not adventurer.player == self.player:
            # pay as necessary
            adventurer.wealth -= self.game.COST_AGENT_REST
            self.wealth += self.game.COST_AGENT_REST
        
        # reset move count
        adventurer.downwind_moves = 0
        adventurer.upwind_moves = 0
        adventurer.land_moves = 0
        
        #remember that this Agent has been used already this turn
        adventurer.agents_rested.append(self)
        
        return True
    
    def manage_trade(self, adventurer):
        '''Receives wealth when trade takes place on its tile, either keeping this or giving it to an Adventurer of the same player
        
        Arguments:
        Cartolan.Adventurer the Adventurer making the trade
        '''
        #check whether Adventurer trading is from the same player
        if adventurer.player == self.player:
            print("Agent on tile " +str(self.current_tile.tile_position.longitude)+","
                  +str(self.current_tile.tile_position.longitude)+ " has given monopoly bonus to Adventurer")
            # pay as necessary
            adventurer.wealth += self.game.VALUE_AGENT_TRADE
        else:
            # retain wealth if they are a different player
            print("Agent on tile " +str(self.current_tile.tile_position.longitude)+","
                  +str(self.current_tile.tile_position.longitude)+ " has kept monopoly bonus")
            self.wealth += self.game.VALUE_AGENT_TRADE
        
        return True

class CityTileBeginner(CityTile):
    '''Represents a city tile in the Beginner mode for the game Cartolan
    
    Methods:
    visit_city takes a Cartolan.Adventurer
    bank_wealth takes a Cartolan.Adventurer
    buy_adventurer takes a Cartolan.Adventurer
    buy_agent takes a Cartolan.Adventurer
    '''
    
    def visit_city(self, adventurer):
        '''Initiates all the possible actions when a city is visited
        
        Arguments:
        Cartolan.Adventurer the Adventurer arriving on the City tile
        '''
        #reset Adventurer's list of visited Wonders
        adventurer.wonders_visited = []
        
        #record that this is the latest city visited
        adventurer.latest_city = self
        
        self.bank_wealth(adventurer)
        
        self.buy_adventurers(adventurer)
        
        self.buy_agents(adventurer)
        
        #End the Adventurer's turn and reset their moves
        adventurer.end_turn()
        
        self.game.game_over = self.game.check_win_conditions()
        
        return True
    
    
    def bank_wealth(self, adventurer):
        '''Offers a player to move wealth from their Adventurer's Chest into their Vault
        
        Arguments:
        Cartolan.Adventurer the Adventurer that has arrived at the City
        '''
        #check whether and how much the player wants to bank
        wealth_to_bank = adventurer.player.check_bank_wealth(adventurer)
        #record the decision about how much wealth will be banked
        adventurer.banked = wealth_to_bank
        
        #check if wealth is available and move it from the adventurer's Chest to their Vault
        if adventurer.wealth >= wealth_to_bank:
            adventurer.wealth -= wealth_to_bank
            adventurer.player.vault_wealth += wealth_to_bank
            print(adventurer.player.colour+ " player has banked " +str(wealth_to_bank)+ " in their Vault")
            self.game.game_over = self.game.check_win_conditions()
            return True
        else:
            return False
    
    def buy_adventurers(self, adventurer):
        '''Offers the Player of an Adventurer arriving at the City Tile to buy another Adventurer
        
        Arguments:
        Cartolan.Adventurer the Adventurer arriving at the City
        '''
        #record the decision to buy an adventurer this turn
        adventurer.bought_adventurer += 1
        
        #keep checking whether the player has enough wealth and wants to buy another adventurer until they refuse
        while (len(adventurer.player.adventurers) < adventurer.game.MAX_ADVENTURERS 
                and adventurer.player.vault_wealth >= adventurer.game.COST_ADVENTURER):
            if adventurer.player.check_buy_adventurer(adventurer):
                #take payment of wealth from their Vault
                adventurer.player.vault_wealth -= adventurer.game.COST_ADVENTURER
                #place another Adventurer for this Player on the City tile
#                 new_adventurer = AdventurerBeginner(adventurer.game, adventurer.player, self)
                new_adventurer = adventurer.game.ADVENTURER_TYPE(adventurer.game, adventurer.player, self)
#                 self.adventurers.append(new_adventurer)
                self.move_onto_tile(new_adventurer)
                #Allow this new Adventurer to move this turn
#                 new_adventurer.turns_moved = adventurer.game.turn - 1 # This new Adventurer will play immediately
                new_adventurer.turns_moved = adventurer.game.turn # This new Adventurer will play from the next turn
                print(adventurer.player.colour+ " player has bought an adventurer from the city at " 
                      +str(self.tile_position.longitude)+","+str(self.tile_position.latitude))
            else:
                return False
        return True
    
    
    def buy_agents(self, adventurer):
        '''Offers the Player of an Adventurer arriving at the City Tile to buy another Agent and place it on any unclaimed tile
        
        Arguments:
        Cartolan.Adventurer the Adventurer arriving at the City, if None, then the Player will no longer be prompted
        '''
        #Record the decision to buy an agent this move
        adventurer.bought_agent += 1
        
        #keep checking whether the player can afford another Adventurer and wants one until they refuse
        while adventurer.player.vault_wealth >= adventurer.game.COST_AGENT_FROM_CITY:
            tile = adventurer.player.check_buy_agent(adventurer, report="Do you want to place an agent, and where?") 
            if not tile is None:
                #check whether this tile is inside a city's domain, four or less tiles from it by taxi norm
                for city_tile in self.game.cities:
                    city_longitude = city_tile.tile_position.longitude
                    city_latitude = city_tile.tile_position.latitude
                    if (abs(tile.tile_position.longitude - city_longitude) 
                        + abs(tile.tile_position.latitude - city_latitude) <= self.game.CITY_DOMAIN_RADIUS):
                        continue
            else:
                return False

            #check whether the tile already has an active Agent 
            if not adventurer.check_tile_available(tile):
                continue
            else:
                #pick up an existing Agent from its tile if there are no other agents available
                #otherwise get a new agent
                if len(adventurer.player.agents) >= self.game.MAX_AGENTS:
                    agent = adventurer.player.check_move_agent(adventurer)
                    if not agent is None:
                        print(adventurer.player.colour+ " player is recalling their agent from the tile at " 
                          +str(agent.current_tile.tile_position.longitude)
                              +","+str(agent.current_tile.tile_position.latitude))
                        agent.current_tile.move_off_tile(agent)
                        #place the Agent on that tile
                        tile.move_onto_tile(agent)
                    else:
                        print(adventurer.player.colour+ " player did not want to move any existing Agents, so moving on.")
                        return False
                else:
                    agent = adventurer.game.AGENT_TYPE(adventurer.game, adventurer.player, tile)
                
                #take payment from the Player's Vault
                adventurer.player.vault_wealth -= adventurer.game.COST_AGENT_FROM_CITY
                print(adventurer.player.colour+ " player has hired an agent from the city at " 
                  +str(self.tile_position.longitude)+","+str(self.tile_position.latitude)
                     +" and sent them to the tile at "
                     +str(tile.tile_position.longitude)+","+str(tile.tile_position.latitude))
        return True

# class WonderTile(Tile):
#     def __init__(game, is_wonder):
#         super().
    
#     def reward_discovery(adventurer): # This is handled in the Adventurer class atm
#         #check what kind of tile this is and look up the reward
        
#         #add wealth to Adventurer's Chest
#         pass
    
#     def reward_trade(adventurer): # This is handled in the Adventurer class atm
#         #check that adventurer has not visited this tile already since their last visit to a city
        
#         #check whether there is an active Agent on this tile and involve them in the trade if so
#         pass

# class WaterWonderTile(WonderTile)

