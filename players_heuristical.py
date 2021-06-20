'''
    Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

from base import Player
import random

class PlayerBeginnerExplorer(Player):    
    '''A virtual player for Cartolan that makes decisions favouring exploration

    This crude computer player will always move away from the Capital while its Chest has less than the points difference and then towards the Capital once it has collected enough wealth
    
    Methods:
    explore_best_space takes a Cartolan.Adventurer
    move_away_from_tile takes a Cartolan.Adventurer and a Cartolan.Tile
    move_towards_tile takes a Cartolan.Adventurer and a Cartolan.Tile
    continue_move takes a Cartolan.Adventurer
    continue_turn takes a Cartolan.Adventurer
    check_trade takes a Cartolan.Adventurer and a Cartolan.Tile
    check_collect_wealth takes a Cartolan.Agent
    check_rest takes a Cartolan.Adventurer and a Cartolan.Agent
    check_bank_wealth takes a Cartolan.Adventurer and a String
    check_buy_adventurer takes a Cartolan.Adventurer and a String
    check_place_agent takes a Cartolan.Adventurer
    check_buy_agent takes a Cartolan.Adventurer
    check_move_agent takes a Cartolan.Adventurer
    '''
    def __init__(self, colour):
        super().__init__(colour)
        self.p_deviate = 0.1 #some randomness for artificial player behaviour to avoid rutts
    
    def check_location_to_avoid(self, longitude, latitude):
        '''Compares coordinates to a list to avoid'''
        #Check each of the coordinate pairs to avoid in turn
        for location in self.locations_to_avoid:
            if location[0] == longitude and location[1] == latitude:
                print("Identified these coordinates as a location to avoid: " +str(longitude)+ ", " +str(latitude))
                return True
        #If the given coordinates didn't match any of the locations to avoid
        print("Identified these coordinates as NOT a location to avoid: " +str(longitude)+ ", " +str(latitude))
        return False
    
    def explore_best_space(self, adventurer):
        '''A heuristic for Adventurer movement that selects the adjacent gap in the map with the highest prospective score from adjoining edges, preferring downwind and right when this is tied'''
        #check downwind clockwise first, then downwind anti, then upwind clock, then upwind anti
        print(str(adventurer.player.colour) +": trying heuristic that prefers the adjacent gap in the map with the highest prospective score from adjoining edges, preferring downwind and right when this is tied")
        if adventurer.current_tile.wind_direction.east:
            if adventurer.current_tile.wind_direction.north:
                potential_moves = ['e', 'n', 'w', 's']
            else:
                potential_moves = ['s', 'e', 'n', 'w']
        else:
            if adventurer.current_tile.wind_direction.north:
                potential_moves = ['n', 'w', 's', 'e']
            else:
                potential_moves = ['w', 's', 'e', 'n']
        
        #for each possible move, check wether an empty space in the map
        preferred_move = None
        preferred_score = 0
        exploration_moves = 0
        for compass_point in potential_moves:
            if adventurer.can_move(compass_point):
                #translate the compass point into coordinates
                longitude_increment = int(compass_point.lower() in ["east","e"]) - int(compass_point.lower() in ["west","w"])
                new_longitude = adventurer.current_tile.tile_position.longitude + longitude_increment
                latitude_increment = int(compass_point.lower() in ["north","n"]) - int(compass_point.lower() in ["south","s"])
                new_latitude = adventurer.current_tile.tile_position.latitude + latitude_increment
                #check whether empty or otherwise designated to avoid
                if (adventurer.exploration_needed(new_longitude, new_latitude) 
                    and not self.check_location_to_avoid(new_longitude, new_latitude)):
                    #Check whether the score from exploring here beats any checked so far
                    exploration_moves += 1
                    potential_score = adventurer.get_exploration_value(adventurer.get_adjoining_edges(new_longitude, new_latitude), compass_point)
                    if potential_score > preferred_score:
                        preferred_move = compass_point
                        preferred_score = potential_score
        print(self.colour +" player's Adventurer has "+str(exploration_moves)+" exploration options.")
        if preferred_move is not None:
            if adventurer.move(preferred_move):
                return True
            else:
                #If movement failed because the turn is over then leave here
                if adventurer.turns_moved >= adventurer.game.turn:
                    return True
                self.locations_to_avoid.append([new_longitude, new_latitude])
                return False
        elif exploration_moves == 3:
            #The absence of any scoring opportunities despite exploration on all sides implies isolation and that it's worth abandoning the expedition
            city_tile = adventurer.latest_city
            adventurer.abandon_expedition(city_tile)
        print("With no valid exploration moves were found, then simply move away slowly from the Adventurer's city of choice")
        return self.move_away_from_tile(adventurer, adventurer.latest_city)
                    
    def move_away_from_tile(self, adventurer, tile):
        '''A heuristic that moves the Adventurer in the direction that increases the distance from a given tile, but by the minimum'''
        print(str(adventurer.player.colour) +": trying heuristic that prefers moves away from the tile at " +str(tile.tile_position.longitude)+ ", " +str(tile.tile_position.longitude))
        #establish directions to the tile, as preferring to increase the distance in the lesser dimension first, between latitude and longitude
        if (abs(adventurer.current_tile.tile_position.longitude - tile.tile_position.longitude) 
            > abs(adventurer.current_tile.tile_position.latitude - tile.tile_position.latitude)):
            #Now establish which cardinal compass direction would be moving away rather than towards
            if adventurer.current_tile.tile_position.latitude > tile.tile_position.latitude:
                if adventurer.current_tile.tile_position.longitude >= tile.tile_position.longitude:
                    preferred_moves = ['n', 'e']
                else:
                    preferred_moves = ['n', 'w']
            else:
                if adventurer.current_tile.tile_position.longitude >= tile.tile_position.longitude:
                    preferred_moves = ['s', 'e']
                else:
                    preferred_moves = ['s', 'w']
        else:
            if adventurer.current_tile.tile_position.longitude >= tile.tile_position.longitude:
                if adventurer.current_tile.tile_position.latitude > tile.tile_position.latitude:
                    preferred_moves = ['e', 'n']
                else:
                    preferred_moves = ['e', 's']
            else:
                if adventurer.current_tile.tile_position.latitude > tile.tile_position.latitude:
                    preferred_moves = ['w', 'n']
                else:
                    preferred_moves = ['w', 's']
        
        #Try the moves in sequence
        for compass_point in preferred_moves:
            #translate the compass point into coordinates
            longitude_increment = int(compass_point.lower() in ["east","e"]) - int(compass_point.lower() in ["west","w"])
            new_longitude = adventurer.current_tile.tile_position.longitude + longitude_increment
            latitude_increment = int(compass_point.lower() in ["north","n"]) - int(compass_point.lower() in ["south","s"])
            new_latitude = adventurer.current_tile.tile_position.latitude + latitude_increment
            #try moving, but if this ends up with failed exploration, then remember and avoid in future
            if not self.check_location_to_avoid(new_longitude, new_latitude):
                if adventurer.move(compass_point):
                    return True
                else:
                    self.locations_to_avoid.append([new_longitude, new_latitude])
                    #If movement failed because the turn is over then leave here
                    if adventurer.turns_moved >= adventurer.game.turn:
                        return True
        
        print("With no suitable moves available, try a random one, to avoid getting stuck in place")
        if adventurer.move(random.choice(['n','e','s','w'])):
            return True
        print("With even the random move failing, just wait in place")
        return adventurer.wait()
            
    def move_towards_tile(self, adventurer, tile):
        '''A heuristic that moves the Adventurer in the direction that decreases the distance from a given tile, by the maximum, but if unable waits in place'''
        print(str(adventurer.player.colour) +": trying heuristic that prefers moves towards the tile at " +str(tile.tile_position.longitude)+ ", " +str(tile.tile_position.longitude))
        #establish directions to the tile, as preferring to decrease the distance in the greater dimension first, between latitude and longitude
        if (abs(adventurer.current_tile.tile_position.longitude - tile.tile_position.longitude) 
            < abs(adventurer.current_tile.tile_position.latitude - tile.tile_position.latitude)):
            #Now establish which cardinal compass direction would be moving towards rather than away
            if adventurer.current_tile.tile_position.latitude < tile.tile_position.latitude:
                if adventurer.current_tile.tile_position.longitude <= tile.tile_position.longitude:
                    preferred_moves = ['n', 'e']
                else:
                    preferred_moves = ['n', 'w']
            else:
                if adventurer.current_tile.tile_position.longitude <= tile.tile_position.longitude:
                    preferred_moves = ['s', 'e']
                else:
                    preferred_moves = ['s', 'w']
        else:
            if adventurer.current_tile.tile_position.longitude <= tile.tile_position.longitude:
                if adventurer.current_tile.tile_position.latitude < tile.tile_position.latitude:
                    preferred_moves = ['e', 'n']
                else:
                    preferred_moves = ['e', 's']
            else:
                if adventurer.current_tile.tile_position.latitude < tile.tile_position.latitude:
                    preferred_moves = ['w', 'n']
                else:
                    preferred_moves = ['w', 's']
        
        #Try the moves in sequence
        for compass_point in preferred_moves:
            if compass_point == preferred_moves[-1]:
                print("Can't move in desired direction so risking a move away to get a favourable wind direction")
            #translate the compass point into coordinates
            longitude_increment = int(compass_point.lower() in ["east","e"]) - int(compass_point.lower() in ["west","w"])
            new_longitude = adventurer.current_tile.tile_position.longitude + longitude_increment
            latitude_increment = int(compass_point.lower() in ["north","n"]) - int(compass_point.lower() in ["south","s"])
            new_latitude = adventurer.current_tile.tile_position.latitude + latitude_increment
            #try moving, but if this ends up with failed exploration, then remember and avoid in future
            if not self.check_location_to_avoid(new_longitude, new_latitude):
                if adventurer.move(compass_point):
                    return True
                else:
                    self.locations_to_avoid.append([new_longitude, new_latitude])
                    #If movement failed because the turn is over then leave here
                    if adventurer.turns_moved >= adventurer.game.turn:
                        return True
        
        #If nothing else has worked then just wait for the next turn
        return adventurer.wait()
    
    
    def continue_move(self, adventurer):
        #with some probability, move in a random direction, to break out of degenerate situations
        if random.random() < self.p_deviate:
            print(str(adventurer.player.colour)+ " is making a random movement, rather than following a heuristic")
            adventurer.move(random.choice(['n','e','s','w']))
#        #move towards a city while banking will put the player ahead, and explore otherwise
#        elif(adventurer.wealth > adventurer.game.wealth_difference):
        #move towards a city while banking will increase earning potential
        elif(adventurer.wealth > adventurer.game.cost_adventurer):
            self.move_towards_tile(adventurer, adventurer.latest_city)
        else:
#             self.explore_away_from_tile(adventurer, adventurer.latest_city)
            self.explore_best_space(adventurer)
        return True
    
    def continue_turn(self, adventurer):
        print(str(adventurer.player.colour)+ " player is moving an Adventurer, which has " 
              +str(adventurer.wealth)+ " wealth, and is on the "
              +adventurer.current_tile.tile_back+ " tile at position " 
              +str(adventurer.current_tile.tile_position.longitude)+ "," 
              +str(adventurer.current_tile.tile_position.latitude))
        
        #reset the record of tiles already visited this turn
        self.locations_to_avoid = []
        
        while adventurer.turns_moved < adventurer.game.turn:
            #record the current tile so that it can be avoided in subsequent moves to prevent degenerate yo-yoing
            self.locations_to_avoid.append([adventurer.current_tile.tile_position.longitude, adventurer.current_tile.tile_position.latitude])
            self.continue_move(adventurer)
                
        return True
    
    #if offered by a Wonder, always trade
    def check_trade(self, adventurer, tile):
        return True
    
    #if offered by an agent, always collect wealth
    def check_collect_wealth(self, agent):
        return True
    
    #if offered always rest
    def check_rest(self, adventurer, agent):
        if adventurer.wealth >= adventurer.game.cost_agent_rest:
            return True
        return False
    
    #if offered by a city then always bank everything
    def check_deposit(self, adventurer, maximum, minimum, report="Player is being asked whether to bank wealth"):
        print(report)
        return maximum
    
    #if offered by a city, then check whether oponents will win on their next visit to a city, and buy an Adventurer if not
    def check_buy_adventurer(self, adventurer, report="Player is being asked whether to buy an adventurer"):
        print(report)
        
        #randomly choose not to hire, regardless of other conditions
        if random.random() < 0.5:
            return False
        
        if self.vault_wealth > adventurer.game.cost_adventurer:
            #Check whether player has won compared to wealthiest opponent 
            wealthiest_opponent_wealth = 0
            #Check whether any opponent is in a position to win based just on their incoming wealth, if an Adventurer were hired
            opponent_near_win = False
            for player in adventurer.game.players:
                if player is not self:
                    if player.vault_wealth > wealthiest_opponent_wealth:
                        wealthiest_opponent_wealth = player.vault_wealth
                    player_chest_wealth = 0
                    for other_adventurer in adventurer.game.adventurers[player]:
                        player_chest_wealth += other_adventurer.wealth
                    if (player.vault_wealth + player_chest_wealth 
                        > adventurer.game.game_winning_difference + self.vault_wealth - adventurer.game.cost_adventurer):
                        opponent_near_win = True
            #Don't hire if player has won compared to wealthiest opponent 
            if self.vault_wealth > wealthiest_opponent_wealth + adventurer.game.game_winning_difference:
                return False
            #Hire if no opponent can then win based on their incoming wealth
            if not opponent_near_win:
                return True    
        return False
    
    # never place an agent when offered
    def check_place_agent(self, adventurer):
        return False
    
    # never buy an agent when offered
    def check_buy_agent(self, adventurer, report="Player has been offered to buy an agent by a city"):
        print(report)
        return None
    
    # never move an agent when offered
    def check_move_agent(self, adventurer):     
#         return agent_to_move
        return None
    
    def check_transfer_agent(self, adventurer):
        return None
    
    def check_travel_money(self, adventurer, maximum, default):
        return default


class PlayerBeginnerTrader(PlayerBeginnerExplorer):    
    '''A virtual player for Beginner mode of Cartolan, that makes decisions that maximises income from each trade

    this crude computer player will always move away from the Capital while its Chest has less than the points difference and then towards the Capital once it has collected enough wealth
    if it can't move away from the Capital as desired, but can move, it will avoid the clockwise rotation of the wind, by heading downwind to the left
    if it can't move toward the Capital as desired, but can move, it will make use of the clockwise rotation of the wind, by heading downwind to the right
    unlike the crude explorer, it will establish agents whenever it discovers a wonder


    Methods:
    continue_move takes a Cartolan.Adventurer
    check_rest takes a Cartolan.Adventurer and a Cartolan.Agent
    check_bank_wealth takes a Cartolan.Adventurer and a String
    check_place_agent takes a Cartolan.Adventurer
    check_move_agent takes a Cartolan.Adventurer
    '''
    def __init__(self, colour):
        super().__init__(colour)
        self.next_agent_num = [0] # this won't work for multiple adventurers
    
    def continue_move(self, adventurer):
        adventurers = adventurer.game.adventurers[self]
        agents = adventurer.game.agents[self]
                                
        #with some probability, move in a random direction, to break out of degenerate situations
        if random.random() < self.p_deviate:
            adventurer.move(random.choice(['n','e','s','w']))
        #locate the next unvisited agent and move towards them, or if all agents have been visited either explore or return home
        elif not self.next_agent_num[adventurers.index(adventurer)] < len(agents):
            if (adventurer.wealth <= adventurer.game.wealth_difference and len(agents) < adventurer.game.MAX_AGENTS):
                self.explore_best_space(adventurer)
#                   self.explore_above_distance(adventurer, adventurer.latest_city, adventurer.game.CITY_DOMAIN_RADIUS)
            else:
                self.move_towards_tile(adventurer, adventurer.latest_city)
        else:
#            if adventurer.wealth <= adventurer.game.wealth_difference:
            if (adventurer.wealth <= adventurer.game.cost_adventurer 
                and self.next_agent_num[adventurers.index(adventurer)] < len(agents) - 1):
                self.move_towards_tile(adventurer, agents[self.next_agent_num[adventurers.index(adventurer)]].current_tile)
            else:
                self.move_towards_tile(adventurer, adventurer.latest_city)

        return True

    def check_rest(self, adventurer, agent):
        adventurers = adventurer.game.adventurers[self]
        agents = adventurer.game.agents[self]
        #if there is an agent then always rest
        adventurer.rest()
        #if this was the target agent for movement then start looking for the next one
        if self.next_agent_num[adventurers.index(adventurer)] < len(agents):
            if agent == agents[self.next_agent_num[adventurers.index(adventurer)]]:
                #start targetting the next agent
                self.next_agent_num[adventurers.index(adventurer)] += 1

    def check_bank_wealth(self, adventurer, report="Player is being asked whether to bank"):
        adventurers = adventurer.game.adventurers[self]
        #register that a city has been visited and that should start going back to first agent
        self.next_agent_num[adventurers.index(adventurer)] = 0
        return super().check_bank_wealth(adventurer, report)
    
    # if this is a wonder then always place an agent when offered
    def check_place_agent(self, adventurer):
        agents = adventurer.game.agents[self]
        if len(agents) < adventurer.current_tile.game.MAX_AGENTS and adventurer.current_tile.is_wonder:
            return True
        else:
            return False
    
    # Never move an agent when offered, because should simply be repeating a route consisting of all agents
    def check_move_agent(self, adventurer):
        return None
    
    # if a new Adventurer is hired then extend the tracker for which Agent is next to visit
    def check_buy_adventurer(self, adventurer, report=""):
        if super().check_buy_adventurer(adventurer):
            self.next_agent_num += [0]
            return True
        else:
            return False
        
    
    
class PlayerBeginnerRouter(PlayerBeginnerTrader):    
    '''A virtual plaer for Beginner mode of the game Cartolan, who makes decisions that maximise route length
    
    this crude computer player will always move away from the Capital while its Chest has less than the points difference and then towards the Capital once it has collected enough wealth
    if it can't move away from the Capital as desired, but can move, it will avoid the clockwise rotation of the wind, by heading downwind to the left
    if it can't move toward the Capital as desired, but can move, it will make use of the clockwise rotation of the wind, by heading downwind to the right
    unlike the crude trader, it will establish agents only on its final move
    
    
    Methods:
    continue_move takes a Cartolan.Adventurer
    check_place_agent takes a Cartolan.Adventurer
    check_move_agent takes a Cartolan.Adventurer
    '''    
    def continue_move(self, adventurer):
        adventurers = adventurer.game.adventurers[self]
        agents = adventurer.game.agents[self]
        #with some probability, move in a random direction, to break out of degenerate situations
        if random.random() < self.p_deviate:
            adventurer.move(random.choice(['n','e','s','w']))
        #locate the next unvisited agent and move towards them, or if all agents have been visited either explore or return home
        elif self.next_agent_num[adventurers.index(adventurer)] >= len(agents):
#            if (adventurer.wealth <= adventurer.game.wealth_difference):
            if (adventurer.wealth <= adventurer.game.cost_adventurer):
                self.explore_best_space(adventurer)
#                 self.explore_above_distance(adventurer, adventurer.latest_city, adventurer.game.CITY_DOMAIN_RADIUS)
            else:
                self.move_towards_tile(adventurer, adventurer.latest_city)
        else:
            self.move_towards_tile(adventurer, agents[self.next_agent_num[adventurers.index(adventurer)]].current_tile)

        #if this is a wonder then always trade
#             if isinstance(adventurer.current_tile, WonderTile):
        if adventurer.current_tile.is_wonder:
            adventurer.trade(adventurer.current_tile)
        return True
    
    # if this is the last movement of a turn then always place an agent when offered
    def check_place_agent(self, adventurer):
        agents = adventurer.game.agents[self]
        #if this would otherwise be the last move this turn, then place an agent
        if len(agents) < adventurer.game.MAX_AGENTS and not adventurer.can_move(None):
            return True
        else:
            return False
    
    # move agents as further exploration is done, so that the route can evolve over time
    def check_move_agent(self, adventurer):
        agents = adventurer.game.agents[self]
        return agents.pop(0)


class PlayerRegularExplorer(PlayerBeginnerExplorer):    
    '''A virtual player for Regular Cartolan, that favours exploration
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates and restore dispossessed agents
    
    Methods:
    continue_turn takes a Cartolan.Adventurer
    check_attack_adventurer takes two Cartolan.Adventurers
    check_attack_agent takes a Cartolan.Adventurer and a Carolan.Agent
    check_restore_agent takes a Cartolan.Adventurer and a Carolan.Agent
    '''
    def __init__(self, colour):
        self.attack_history = {} #to keep track of when this player has attacked, for reference
        super().__init__(colour)
    
    
    def continue_turn(self, adventurer):
        print(str(adventurer.player.colour)+ " player is moving an Adventurer, which has " 
              +str(adventurer.wealth)+ " wealth, and is on the "
              +adventurer.current_tile.tile_back+ " tile at position " 
              +str(adventurer.current_tile.tile_position.longitude)+ "," 
              +str(adventurer.current_tile.tile_position.latitude))
        
        #update awareness of disaster tiles, to avoid them, and reset the record of tiles already visited this turn
        self.locations_to_avoid = []
        for disaster_tile in adventurer.game.disaster_tiles:
            self.locations_to_avoid.append([disaster_tile.tile_position.longitude, disaster_tile.tile_position.latitude])
        
        #check whether already on a tile with an adventurer, and wait here in order to attack/arrest
        for other_adventurer in adventurer.current_tile.adventurers:
            if self.check_attack_adventurer(adventurer, other_adventurer):
                print(self.colour+ " player's adventurer is waiting on their current tile to attack an adventurer belonging to " 
                      +other_adventurer.player.colour)
                adventurer.wait()   
        
        while adventurer.turns_moved < adventurer.game.turn:
            #record the current tile so that it can be avoided in subsequent moves to prevent degenerate yo-yoing
            self.locations_to_avoid.append([adventurer.current_tile.tile_position.longitude, adventurer.current_tile.tile_position.latitude])
            self.continue_move(adventurer)
        return True    
        
    def check_attack_adventurer(self, adventurer, other_adventurer):
        # if the adventurer has a pirate token and the wealth from an arrest exceeds the loss from piracy then stick around and fight
        if (other_adventurer.pirate_token and other_adventurer.player != self
           and adventurer.wealth < adventurer.game.value_arrest):
            return True
        return False
    
    def check_attack_agent(self, adventurer, agent):
        # Explorer will never attack agents
        return False
    
    def check_steal_amount(self, adventurer, maximum, default):
        return default
    
    def check_restore_agent(self, adventurer, agent):
        if agent.player == adventurer.player and adventurer.wealth >= adventurer.game.cost_agent_restore:
            return True
        return False
    
    # if half Disaster tile dropped wealth exceeds own wealth then try to collect it
    def check_court_disaster(self, adventurer, disaster_tile):
        return False
    
    #Never refresh map tiles
    def check_buy_maps(self, adventurer):
        return False
    
    #@TODO replicate all player types in Advanced mode and separate this out
    def check_buy_tech(self, adventurer):
        #randomly choose not to buy, regardless of other conditions
        if random.random() < 0.5:
            return False
        
        if self.vault_wealth > adventurer.game.cost_tech:
            #Check whether player has won compared to wealthiest opponent 
            wealthiest_opponent_wealth = 0
            #Check whether any opponent is in a position to win based just on their incoming wealth, if an Adventurer were hired
            opponent_near_win = False
            for player in adventurer.game.players:
                if player is not self:
                    if player.vault_wealth > wealthiest_opponent_wealth:
                        wealthiest_opponent_wealth = player.vault_wealth
                    player_chest_wealth = 0
                    for other_adventurer in adventurer.game.adventurers[player]:
                        player_chest_wealth += other_adventurer.wealth
                    if (player.vault_wealth + player_chest_wealth 
                        > adventurer.game.game_winning_difference + self.vault_wealth - adventurer.game.cost_adventurer):
                        opponent_near_win = True
            #Don't buy if player has won compared to wealthiest opponent 
            if self.vault_wealth > wealthiest_opponent_wealth + adventurer.game.game_winning_difference:
                return False
            #Hire if no opponent can then win based on their incoming wealth
            if not opponent_near_win:
                return True    
        return False

        
class PlayerRegularTrader(PlayerBeginnerTrader, PlayerRegularExplorer):    
    '''A virtual player for Regular Cartolan that favours maximising trade value
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates'''
    def __init__(self, colour):
        super().__init__(colour)

class PlayerRegularRouter(PlayerBeginnerRouter, PlayerRegularExplorer):    
    '''A virtual player for Regular Cartolan that favours building trade routes
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates'''
    def __init__(self, colour):
        super().__init__(colour)

class PlayerRegularPirate(PlayerRegularExplorer):    
    '''A virtual player for Regular Cartolan that favour attacking other players' tokens
    
    this crude computer player seeks out opponents adventurers and agents to attack, and otherwise behaves like the Explorer 
    
    Methods:
    continue_move takes a Cartolan.Adventurer
    check_attack_adventurer takes two Cartolan.Adventurers
    check_court_disaster takes a Cartolan.Adventurer and a Cartolan.DisasterTile
    check_attack_agent takes a Cartolan.Adventurer and a Cartolan.Agent
    '''
    def continue_move(self, adventurer):    
    # seek out the other player's Adventurer or Agent or Disaster tile with the most wealth
        
#        #update awareness of disaster tiles, to avoid them, if not a pirate
#        for disaster_tile in adventurer.game.disaster_tiles:
#            if not disaster_tile in self.locations_to_avoid and not adventurer.pirate_token:
#                self.locations_to_avoid.append([disaster_tile.tile_position.longitude, disaster_tile.tile_position.latitude])
#        
        #check whether already on a tile with an adventurer, and wait here in order to attack/arrest
        for other_adventurer in adventurer.current_tile.adventurers:
            if self.check_attack_adventurer(adventurer, other_adventurer):
                print(self.colour+ " player's adventurer is waiting on their current tile to attack an adventurer belonging to " 
                      +other_adventurer.player.colour)
                adventurer.wait()
        
        #with some probability, move in a random direction, to break out of degenerate situations
        if random.random() < self.p_deviate:
            adventurer.move(random.choice(['n','e','s','w']))
        #move towards the capital while banking will put the player ahead, and chase the next big score otherwise
#        elif(adventurer.wealth > adventurer.game.wealth_difference):
        elif(adventurer.wealth > adventurer.game.cost_adventurer):
            self.move_towards_tile(adventurer, adventurer.latest_city)
        else:
            # if there is an adventurer on the same tile then attack them
            #update awareness of disaster tiles, to avoid them
            for other_adventurer in adventurer.current_tile.adventurers:
                if self.check_attack_adventurer(adventurer, other_adventurer):
                    print(self.colour+ " player's adventurer is waiting on their current tile to attack an adventurer belonging to " 
                          +other_adventurer.player.colour)
                    adventurer.wait()
            
            # check all other players' adventurers and agents and tiles for the most lucrative
            max_score = 0
            score_location = None
            for player in adventurer.game.players:
                if player != self:
                    for other_adventurer in adventurer.game.adventurers[player]:
                        if max_score < other_adventurer.wealth // 2 + other_adventurer.wealth % 2:
                            max_score = other_adventurer.wealth // 2 + other_adventurer.wealth % 2
                            score_location = other_adventurer.current_tile
                    for agent in adventurer.game.agents[self]:
                        if max_score < agent.wealth + 1:
                            max_score = agent.wealth + 1
                            score_location = agent.current_tile
            for longitude in adventurer.game.play_area:
                for latitude in adventurer.game.play_area[longitude]:
                    tile = adventurer.game.play_area[longitude][latitude] 
                if max_score < tile.dropped_wealth:
                    max_score = tile.dropped_wealth
                    score_location = tile
            if score_location is None:
#                 self.explore_away_from_tile(adventurer, adventurer.latest_city)
                self.explore_best_space(adventurer)
            else:
                print("Pirate is moving towards the tile at location "+str(score_location.tile_position.longitude)+", "+str(score_location.tile_position.latitude))
                self.move_towards_tile(adventurer, score_location)
        return True
    
    # attack adventurers or agents when encountered
    def check_attack_adventurer(self, adventurer, other_adventurer):
        # if the adventurer has less wealth to steal than the pirate has to bank they leave it
        if (other_adventurer.player != self
           and adventurer.wealth < other_adventurer.wealth // 2 + other_adventurer.wealth % 2):
            return True
        return False
    
    # if half Disaster tile dropped wealth exceeds own wealth then try to collect it
    def check_court_disaster(self, adventurer, disaster_tile):
        if adventurer.wealth < disaster_tile.dropped_wealth // 2 + disaster_tile.dropped_wealth % 2:
            return True
        return False
    
    def check_attack_agent(self, adventurer, agent):
        return True
    