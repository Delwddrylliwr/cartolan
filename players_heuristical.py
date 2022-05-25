'''
    Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

from base import Player, CityTile
from advanced import AdventurerAdvanced
from game import GameAdvanced
from game_config import BeginnerConfig, RegularConfig, AdvancedConfig
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
    def __init__(self, name):
        super().__init__(name)
        self.p_deviate = BeginnerConfig.P_DEVIATE #some randomness for artificial player behaviour to avoid rutts
        self.p_buy_adventurer = BeginnerConfig.P_BUY_ADVENTURER
        self.return_city_attr = BeginnerConfig.RETURN_CITY_ATTR #Set a criterion for returning to bank wealth
    
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
        print(str(adventurer.player.name) +": trying heuristic that prefers the adjacent gap in the map with the highest prospective score from adjoining edges, preferring downwind and right when this is tied")
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
                    potential_score = adventurer.get_exploration_value(new_longitude, new_latitude)
                    if potential_score > preferred_score:
                        preferred_move = compass_point
                        preferred_score = potential_score
        print(self.name +"'s Adventurer has "+str(exploration_moves)+" exploration options.")
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
        print(str(adventurer.player.name) +": trying heuristic that prefers moves away from the tile at " +str(tile.tile_position.longitude)+ ", " +str(tile.tile_position.longitude))
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
        print(str(adventurer.player.name) +": trying heuristic that prefers moves towards the tile at " +str(tile.tile_position.longitude)+ ", " +str(tile.tile_position.longitude))
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
            print(str(adventurer.player.name)+ " is making a random movement, rather than following a heuristic")
            adventurer.move(random.choice(['n','e','s','w']))
#        #move towards a city while banking will put the player ahead, and explore otherwise
#        elif(adventurer.wealth > adventurer.game.wealth_difference):
        #move towards a city while banking will increase earning potential
        elif(adventurer.wealth >= getattr(adventurer.game, self.return_city_attr)):
            self.move_towards_tile(adventurer, adventurer.latest_city)
        else:
#             self.explore_away_from_tile(adventurer, adventurer.latest_city)
            self.explore_best_space(adventurer)
        return True
    
    def continue_turn(self, adventurer):
        print(str(adventurer.player.name)+ " is moving an Adventurer, which has " 
              +str(adventurer.wealth)+ " wealth, and is on the "
              +adventurer.current_tile.tile_back+ " tile at position " 
              +str(adventurer.current_tile.tile_position.longitude)+ "," 
              +str(adventurer.current_tile.tile_position.latitude))
        
        game = adventurer.game
        if isinstance(game, GameAdvanced):
            if game.assigned_cadres.get(self) is None:
                game.choose_cadre(self)
        
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
        if random.random() > self.p_buy_adventurer:
            return False
        
        if adventurer.game.player_wealths[adventurer.player] > adventurer.game.cost_adventurer:
            #Check whether player has won compared to wealthiest opponent 
            wealthiest_opponent_wealth = 0
            #Check whether any opponent is in a position to win based just on their incoming wealth, if an Adventurer were hired
            opponent_near_win = False
            for player in adventurer.game.players:
                if player is not self:
                    if adventurer.game.player_wealths[player] > wealthiest_opponent_wealth:
                        wealthiest_opponent_wealth = adventurer.game.player_wealths[player]
                    player_chest_wealth = 0
                    for other_adventurer in adventurer.game.adventurers[player]:
                        player_chest_wealth += other_adventurer.wealth
                    if (adventurer.game.player_wealths[player] + player_chest_wealth 
                        > adventurer.game.game_winning_difference + adventurer.game.player_wealths[adventurer.player] - adventurer.game.cost_adventurer):
                        opponent_near_win = True
            #Don't hire if player has won compared to wealthiest opponent 
            if adventurer.game.player_wealths[adventurer.player] > wealthiest_opponent_wealth + adventurer.game.game_winning_difference:
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
    def __init__(self, name):
        super().__init__(name)
        self.next_agent_num = {} #An integer for each Adventurer, tracking by index which Inn/Agent is next to visit
    
    def continue_move(self, adventurer):
        agents = adventurer.game.agents[self]
                                
        #with some probability, move in a random direction, to break out of degenerate situations
        if random.random() < self.p_deviate:
            adventurer.move(random.choice(['n','e','s','w']))
        #locate the next unvisited agent and move towards them, or if all agents have been visited either explore or return home
        elif self.next_agent_num.get(adventurer) is not None and self.next_agent_num.get(adventurer) < len(agents):
            if (adventurer.wealth < getattr(adventurer.game, self.return_city_attr)):
                print("As a Trader, "+self.name+" is moving towards their next Inn, #"+str(self.next_agent_num.get(adventurer)))
                self.move_towards_tile(adventurer, agents[self.next_agent_num.get(adventurer)].current_tile)
            else:
                self.move_towards_tile(adventurer, adventurer.latest_city)
        else:
            if self.next_agent_num.get(adventurer) is not None:
                print("As a Trader, "+self.name+" has visited all their "+str(self.next_agent_num.get(adventurer)+1)+" Inns")
            if (adventurer.wealth < getattr(adventurer.game, self.return_city_attr) and len(agents) < adventurer.game.MAX_AGENTS):
                self.explore_best_space(adventurer)
#                   self.explore_above_distance(adventurer, adventurer.latest_city, adventurer.game.CITY_DOMAIN_RADIUS)
            else:
                self.move_towards_tile(adventurer, adventurer.latest_city)
        
        if isinstance(adventurer.current_tile, CityTile):
            print(self.name+" has visited a city and will start heading to their first Inn again")
            self.next_agent_num[adventurer] = 0
        return True

    def check_rest(self, adventurer, agent):
        agents = adventurer.game.agents[self]
        #if this was the target agent for movement then start looking for the next one
        if self.next_agent_num.get(adventurer) is not None and self.next_agent_num.get(adventurer) < len(agents):
            if agent == agents[self.next_agent_num.get(adventurer)]:
                print(self.name+"has reached their intended Inn, and will now head for Inn #"+str(self.next_agent_num[adventurer]+1))
                self.next_agent_num[adventurer] += 1
        #if there is an agent then always rest
        return True        

    def check_bank_wealth(self, adventurer, report="Player is being asked whether to bank"):
        print(self.name+"has visited a city and will start heading to their first Inn again")
        self.next_agent_num[adventurer] = 0
        return super().check_bank_wealth(adventurer, report)
    
    # if this is a wonder then always place an agent when offered
    def check_place_agent(self, adventurer):
        agents = adventurer.game.agents[self]
        if len(agents) < adventurer.current_tile.game.MAX_AGENTS and adventurer.current_tile.is_wonder:
            print(self.name+" is placing an Inn where they can trade.")
            return True
        else:
            return False
    
    # Never move an agent when offered, because should simply be repeating a route consisting of all agents
    def check_move_agent(self, adventurer):
        return None
    
    # if a new Adventurer is hired then extend the tracker for which Agent is next to visit
    def check_buy_adventurer(self, adventurer, report=""):
        adventurers = adventurer.game.adventurers[self]
        if super().check_buy_adventurer(adventurer):
            self.next_agent_num[adventurers[-1]] = 0
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
        agents = adventurer.game.agents[self]
        #with some probability, move in a random direction, to break out of degenerate situations
        if random.random() < self.p_deviate:
            adventurer.move(random.choice(['n','e','s','w']))
        #locate the next unvisited agent and move towards them, or if all agents have been visited either explore or return home
        elif self.next_agent_num.get(adventurer) is not None and  self.next_agent_num.get(adventurer) < len(agents):
            print("As a Router, "+self.name+" is moving towards their next Inn, #"+str(self.next_agent_num.get(adventurer)))
            self.move_towards_tile(adventurer, agents[self.next_agent_num.get(adventurer)].current_tile)
        else:
            if self.next_agent_num.get(adventurer):
                print("As a Router, "+self.name+" has visited all their "+str(self.next_agent_num.get(adventurer) + 1)+" Inns")
#            if (adventurer.wealth <= adventurer.game.wealth_difference):
            if (adventurer.wealth < getattr(adventurer.game, self.return_city_attr)):
                self.explore_best_space(adventurer)
#                 self.explore_above_distance(adventurer, adventurer.latest_city, adventurer.game.CITY_DOMAIN_RADIUS)
            else:
                self.move_towards_tile(adventurer, adventurer.latest_city)

        #if this is a wonder then always trade
#             if isinstance(adventurer.current_tile, WonderTile):
        if adventurer.current_tile.is_wonder:
            adventurer.trade(adventurer.current_tile)
        if isinstance(adventurer.current_tile, CityTile):
            print(self.name+" has visited a city and will start heading to their first Inn again")
            self.next_agent_num[adventurer] = 0
        return True
    
    # if this is the last movement of a turn then always place an agent when offered
    def check_place_agent(self, adventurer):
        agents = adventurer.game.agents[self]
        #if this would otherwise be the last move this turn, then place an agent
        if len(agents) < adventurer.game.MAX_AGENTS and not adventurer.can_move(None):
            print(self.name+" is placing an Inn where they have struggled to move.")
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
    def __init__(self, name):
        self.attack_history = {} #to keep track of when this player has attacked, for reference
        super().__init__(name)
    
    #@TODO this repeats a lot from the parent method, but the changes touch everything slightly so a more elegant solution would take a complete rewrite
    def explore_best_space(self, adventurer):
        '''Extends basic behaviour by trying to use Chest maps first'''
        #check downwind clockwise first, then downwind anti, then upwind clock, then upwind anti
        print(str(adventurer.player.name) +": trying heuristic that prefers the adjacent gap in the map with the highest prospective score from adjoining edges, preferring downwind and right when this is tied")
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
        
        #for each possible move, check wether an empty space in the map and how much exploration is worth
        preferred_move = None
        preferred_guaranteed = False #Keep track of whether there is a Chest tile that will guarantee this exploration succeeds
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
                    potential_score = adventurer.get_exploration_value(new_longitude, new_latitude)
                    score_guaranteed = None #An int for the index of the Chest tile that fits
                    for tile in adventurer.chest_tiles:
                        if adventurer.rotated_tile_fits(tile, compass_point, adventurer.get_adjoining_edges(new_longitude, new_latitude)):
                            score_guaranteed = adventurer.chest_tiles.index(tile)
                    if preferred_guaranteed:
                        if score_guaranteed is not None:
                            #Omly bother evaluating if this exploration is also guaranteed
                            if potential_score > preferred_score:
                                preferred_move = compass_point
                                preferred_score = potential_score
                                adventurer.preferred_tile_num = score_guaranteed #Select this chest tile to be used
                    else:
                        #Either a higher reward or a guaranteed reward will make this move preferable
                        if score_guaranteed is not None or potential_score > preferred_score:
                            preferred_move = compass_point
                            preferred_score = potential_score
                            adventurer.preferred_tile_num = score_guaranteed #Select this chest tile to be used
        print(self.name +"'s Adventurer has "+str(exploration_moves)+" exploration options.")
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
        print("With no valid Chest map placements found, then looking for random exploration")
        return self.move_away_from_tile(adventurer, adventurer.latest_city)
    
    def continue_turn(self, adventurer):
        print(str(adventurer.player.name)+ " is moving an Adventurer, which has " 
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
                print(self.name+ "'s adventurer is waiting on their current tile to attack an adventurer belonging to " 
                      +other_adventurer.player.name)
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
    
    def choose_tile(self, adventurer, tiles):
        #randomly choose one
        return random.choice(tiles) 

        
class PlayerRegularTrader(PlayerBeginnerTrader, PlayerRegularExplorer):    
    '''A virtual player for Regular Cartolan that favours maximising trade value
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates'''
    def __init__(self, name):
        super().__init__(name)

class PlayerRegularRouter(PlayerBeginnerRouter, PlayerRegularExplorer):    
    '''A virtual player for Regular Cartolan that favours building trade routes
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates'''
    def __init__(self, name):
        super().__init__(name)

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
                print(self.name+ "'s adventurer is waiting on their current tile to attack an adventurer belonging to " 
                      +other_adventurer.player.name)
                adventurer.wait()
        
        #with some probability, move in a random direction, to break out of degenerate situations
        if random.random() < self.p_deviate:
            adventurer.move(random.choice(['n','e','s','w']))
        #move towards the capital while banking will put the player ahead, and chase the next big score otherwise
#        elif(adventurer.wealth > adventurer.game.wealth_difference):
        elif(adventurer.wealth >= getattr(adventurer.game, self.return_city_attr)):
            self.move_towards_tile(adventurer, adventurer.latest_city)
        else:
            # if there is an adventurer on the same tile then attack them
            #update awareness of disaster tiles, to avoid them
            for other_adventurer in adventurer.current_tile.adventurers:
                if self.check_attack_adventurer(adventurer, other_adventurer):
                    print(self.name+ "'s adventurer is waiting on their current tile to attack an adventurer belonging to " 
                          +other_adventurer.player.name)
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

class PlayerAdvancedExplorer(PlayerRegularExplorer):
    '''Extends Regular to incorporate buying cards.
    '''
    def __init__(self, name):
        super().__init__(name)
        self.p_buy_tech = AdvancedConfig.P_BUY_TECH
        self.return_city_attr = AdvancedConfig.RETURN_CITY_ATTR
    
    def continue_turn(self, adventurer):
        if isinstance(adventurer.game, GameAdvanced):
            if adventurer.game.assigned_cadres.get(self) is None:
                adventurer.game.choose_cadre(self)
        if isinstance(adventurer, AdventurerAdvanced):
            if adventurer.character_card is None:
                adventurer.choose_character()
        
        super().continue_turn(adventurer)
    
    def check_buy_tech(self, adventurer):
        #randomly choose not to buy, regardless of other conditions
        if random.random() > self.p_buy_tech:
            return False
        
        print(self.name+" is deciding whether to buy a Manuscript card")
        if adventurer.game.player_wealths[adventurer.player] >= adventurer.game.cost_tech:
            #Check whether player has won compared to wealthiest opponent 
            wealthiest_opponent_wealth = 0
            #Check whether any opponent is in a position to win based just on their incoming wealth, if an Adventurer were hired
            opponent_near_win = False
            for player in adventurer.game.players:
                if player is not self:
                    if adventurer.game.player_wealths[player] > wealthiest_opponent_wealth:
                        wealthiest_opponent_wealth = adventurer.game.player_wealths[player]
                    player_chest_wealth = 0
                    for other_adventurer in adventurer.game.adventurers[player]:
                        player_chest_wealth += other_adventurer.wealth
                    if (adventurer.game.player_wealths[player] + player_chest_wealth 
                        > adventurer.game.game_winning_difference + adventurer.game.player_wealths[adventurer.player] - adventurer.game.cost_tech):
                        opponent_near_win = True
            #Don't buy if player has won compared to wealthiest opponent 
            if adventurer.game.player_wealths[adventurer.player] > wealthiest_opponent_wealth + adventurer.game.game_winning_difference:
                return False
            #Hire if no opponent can then win based on their incoming wealth
            if not opponent_near_win:
                return True    
        return False
    
    def choose_card(self, adventurer, cards):
        '''Gives an automated response to games giving the choice to buy
        '''
        #randomly choose one
        return random.choice(cards)

class PlayerAdvancedTrader(PlayerRegularTrader, PlayerAdvancedExplorer):    
    '''A virtual player for Regular Cartolan that favours maximising trade value
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates'''
    def __init__(self, name):
        super().__init__(name)
        self.p_buy_tech = AdvancedConfig.P_BUY_TECH
        self.return_city_attr = AdvancedConfig.RETURN_CITY_ATTR
    
class PlayerAdvancedRouter(PlayerRegularRouter, PlayerAdvancedExplorer):    
    '''A virtual player for Regular Cartolan that favours maximising trade value
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates'''
    def __init__(self, name):
        super().__init__(name)
        self.p_buy_tech = AdvancedConfig.P_BUY_TECH
        self.return_city_attr = AdvancedConfig.RETURN_CITY_ATTR
    
class PlayerAdvancedPirate(PlayerRegularPirate, PlayerAdvancedExplorer):    
    '''A virtual player for Regular Cartolan that favours maximising trade value
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates'''
    def __init__(self, name):
        super().__init__(name)
        self.p_buy_tech = AdvancedConfig.P_BUY_TECH
        self.return_city_attr = AdvancedConfig.RETURN_CITY_ATTR
    