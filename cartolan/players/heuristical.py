'''
    Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

from cartolan.players.base import Player
from cartolan.core.tiles import CityTile
from cartolan.editions.advanced import AdventurerAdvanced
from cartolan.editions.modes import GameAdvanced
import random

class PlayerBeginnerExplorer(Player):    
    #CPU behaviour tuning
    P_DEVIATE = 0.1 #The probability of randomly deviating from the heuristic
    P_BUY_ADVENTURER = 0.5 #The probability of spending Vault silks on further Adventurers when affordable
    RETURN_CITY_ATTR = "cost_adventurer" #The cost attribute compared against Chest silks when deciding to head home

    '''A virtual player for Cartolan that makes decisions favouring exploration

    This crude computer player will always move away from the Capital while its Chest has less than the points difference and then towards the Capital once it has collected enough silks
    
    Methods:
    explore_best_space takes a Cartolan.Adventurer
    move_away_from_tile takes a Cartolan.Adventurer and a Cartolan.Tile
    move_towards_tile takes a Cartolan.Adventurer and a Cartolan.Tile
    continue_move takes a Cartolan.Adventurer
    continue_turn takes a Cartolan.Adventurer
    check_trade takes a Cartolan.Adventurer and a Cartolan.Tile
    check_collect_silks takes a Cartolan.Inn
    check_rest takes a Cartolan.Adventurer and a Cartolan.Inn
    check_bank_silks takes a Cartolan.Adventurer and a String
    check_buy_adventurer takes a Cartolan.Adventurer and a String
    check_hire_inn takes a Cartolan.Adventurer
    check_buy_inn takes a Cartolan.Adventurer
    check_move_inn takes a Cartolan.Adventurer
    '''
    def __init__(self, name):
        super().__init__(name)
        self.p_deviate = self.P_DEVIATE #some randomness for artificial player behaviour to avoid rutts
        self.p_buy_adventurer = self.P_BUY_ADVENTURER
        self.return_city_attr = self.RETURN_CITY_ATTR #Set a criterion for returning to bank silks
    
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
                    potential_score = adventurer.get_exploration_value(adventurer.get_adjoining_edges(new_longitude, new_latitude), compass_point)
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
#        elif(adventurer.silks > adventurer.game.silks_difference):
        #move towards a city while banking will increase earning potential
        elif(adventurer.silks >= getattr(adventurer.game, self.return_city_attr)):
            self.move_towards_tile(adventurer, adventurer.latest_city)
        else:
#             self.explore_away_from_tile(adventurer, adventurer.latest_city)
            self.explore_best_space(adventurer)
        return True
    
    def continue_turn(self, adventurer):
        print(str(adventurer.player.name)+ " is moving an Adventurer, which has " 
              +str(adventurer.silks)+ " silks, and is on the "
              +adventurer.current_tile.tile_back+ " tile at position " 
              +str(adventurer.current_tile.tile_position.longitude)+ "," 
              +str(adventurer.current_tile.tile_position.latitude))
        
        game = adventurer.game
        if isinstance(game, GameAdvanced):
            if game.assigned_cultures.get(self) is None:
                game.choose_culture(self)
        
        #reset the record of tiles already visited this turn
        self.locations_to_avoid = []
        
        while adventurer.turns_moved < adventurer.game.turn:
            #record the current tile so that it can be avoided in subsequent moves to prevent degenerate yo-yoing
            self.locations_to_avoid.append([adventurer.current_tile.tile_position.longitude, adventurer.current_tile.tile_position.latitude])
            self.continue_move(adventurer)
                
        return True
    
    #if offered by a Trade Port, always trade
    def check_trade(self, adventurer, tile):
        return True
    
    #if offered by an inn, always collect silks
    def check_collect_silks(self, inn):
        return True
    
    #if offered always rest
    def check_rest(self, adventurer, inn):
        if adventurer.silks >= adventurer.game.cost_inn_rest:
            return True
        return False
    
    #if offered by a city then always bank everything
    def check_bank_amount(self, adventurer, maximum, minimum, report="Player is being asked whether to bank silks"):
        print(report)
        return maximum
    
    #if offered by a city, then check whether oponents will win on their next visit to a city, and buy an Adventurer if not
    def check_buy_adventurer(self, adventurer, report="Player is being asked whether to buy an adventurer"):
        print(report)
        
        #randomly choose not to hire, regardless of other conditions
        if random.random() > self.p_buy_adventurer:
            return False
        
        if adventurer.game.vault_silks[adventurer.player] > adventurer.game.cost_adventurer:
            winning_difference = adventurer.game.winning_silks_difference
            if winning_difference is None:
                return self._check_purchase_worthwhile(adventurer, adventurer.game.cost_adventurer)
            #Check whether player has won compared to wealthiest opponent
            wealthiest_opponent_silks = 0
            #Check whether any opponent is in a position to win based just on their incoming silks, if an Adventurer were hired
            opponent_near_win = False
            for player in adventurer.game.players:
                if player is not self:
                    if adventurer.game.vault_silks[player] > wealthiest_opponent_silks:
                        wealthiest_opponent_silks = adventurer.game.vault_silks[player]
                    player_chest_silks = 0
                    for other_adventurer in adventurer.game.adventurers[player]:
                        player_chest_silks += other_adventurer.silks
                    if (adventurer.game.vault_silks[player] + player_chest_silks
                        > winning_difference + adventurer.game.vault_silks[adventurer.player] - adventurer.game.cost_adventurer):
                        opponent_near_win = True
            #Don't hire if player has won compared to wealthiest opponent
            if adventurer.game.vault_silks[adventurer.player] > wealthiest_opponent_silks + winning_difference:
                return False
            #Hire if no opponent can then win based on their incoming silks
            if not opponent_near_win:
                return True
        return False
    
    def _check_purchase_worthwhile(self, adventurer, cost):
        '''Shared vault-threshold guard used when winning_silks_difference is None.
        Returns False if the purchase gap to win is smaller than the cost, or if any
        opponent can already reach the win threshold with their current total silks.
        '''
        game = adventurer.game
        winning_vault = game.winning_vault_silks
        if winning_vault is None:
            return True
        my_vault = game.vault_silks[adventurer.player]
        # Don't spend if the gap remaining is smaller than the cost — better to just bank
        if winning_vault - my_vault <= cost:
            return False
        # Don't spend if an opponent can already win with their current vault + chest silks
        for player in game.players:
            if player is not self:
                opp_total = game.vault_silks[player] + sum(a.silks for a in game.adventurers[player])
                if opp_total >= winning_vault:
                    return False
        return True

    def check_hire_companion(self, adventurer):
        if random.random() > self.p_buy_adventurer:
            return False
        if adventurer.game.vault_silks[adventurer.player] >= adventurer.cost_companion:
            winning_difference = adventurer.game.winning_silks_difference
            if winning_difference is None:
                return self._check_purchase_worthwhile(adventurer, adventurer.cost_companion)
            wealthiest_opponent_silks = 0
            opponent_near_win = False
            for player in adventurer.game.players:
                if player is not self:
                    if adventurer.game.vault_silks[player] > wealthiest_opponent_silks:
                        wealthiest_opponent_silks = adventurer.game.vault_silks[player]
                    player_chest_silks = sum(a.silks for a in adventurer.game.adventurers[player])
                    if (adventurer.game.vault_silks[player] + player_chest_silks
                            > winning_difference + adventurer.game.vault_silks[adventurer.player] - adventurer.cost_companion):
                        opponent_near_win = True
            if adventurer.game.vault_silks[adventurer.player] > wealthiest_opponent_silks + winning_difference:
                return False
            if not opponent_near_win:
                return True
        return False

    # never place an inn when offered
    def check_hire_inn(self, adventurer):
        return False
    
    # never buy an inn when offered
    def check_buy_inn(self, adventurer, report="Player has been offered to buy an inn by a city"):
        print(report)
        return None
    
    # never move an inn when offered
    def check_move_inn(self, adventurer):     
#         return inn_to_move
        return None
    
    def check_transfer_inn(self, adventurer):
        return None
    
    def check_travel_silks(self, adventurer, maximum, default):
        return default


class PlayerBeginnerTrader(PlayerBeginnerExplorer):    
    '''A virtual player for Beginner mode of Cartolan, that makes decisions that maximises income from each trade

    this crude computer player will always move away from the Capital while its Chest has less than the points difference and then towards the Capital once it has collected enough silks
    if it can't move away from the Capital as desired, but can move, it will avoid the clockwise rotation of the wind, by heading downwind to the left
    if it can't move toward the Capital as desired, but can move, it will make use of the clockwise rotation of the wind, by heading downwind to the right
    unlike the crude explorer, it will establish inns whenever it discovers a trade port


    Methods:
    continue_move takes a Cartolan.Adventurer
    check_rest takes a Cartolan.Adventurer and a Cartolan.Inn
    check_bank_silks takes a Cartolan.Adventurer and a String
    check_hire_inn takes a Cartolan.Adventurer
    check_move_inn takes a Cartolan.Adventurer
    '''
    def __init__(self, name):
        super().__init__(name)
        self.next_inn_num = {} #An integer for each Adventurer, tracking by index which Inn/Inn is next to visit
    
    def continue_move(self, adventurer):
        inns = adventurer.game.inns[self]
                                
        #with some probability, move in a random direction, to break out of degenerate situations
        if random.random() < self.p_deviate:
            adventurer.move(random.choice(['n','e','s','w']))
        #locate the next unvisited inn and move towards them, or if all inns have been visited either explore or return home
        elif self.next_inn_num.get(adventurer) is not None and self.next_inn_num.get(adventurer) < len(inns):
            if (adventurer.silks < getattr(adventurer.game, self.return_city_attr)):
                print("As a Trader, "+self.name+" is moving towards their next Inn, #"+str(self.next_inn_num.get(adventurer)))
                self.move_towards_tile(adventurer, inns[self.next_inn_num.get(adventurer)].current_tile)
            else:
                self.move_towards_tile(adventurer, adventurer.latest_city)
        else:
            if self.next_inn_num.get(adventurer) is not None:
                print("As a Trader, "+self.name+" has visited all their "+str(self.next_inn_num.get(adventurer)+1)+" Inns")
            if (adventurer.silks < getattr(adventurer.game, self.return_city_attr) and len(inns) < adventurer.game.max_inns):
                self.explore_best_space(adventurer)
#                   self.explore_above_distance(adventurer, adventurer.latest_city, adventurer.game.CITY_DOMAIN_RADIUS)
            else:
                self.move_towards_tile(adventurer, adventurer.latest_city)
        
        if isinstance(adventurer.current_tile, CityTile):
            print(self.name+" has visited a city and will start heading to their first Inn again")
            self.next_inn_num[adventurer] = 0
        return True

    def check_rest(self, adventurer, inn):
        inns = adventurer.game.inns[self]
        #if this was the target inn for movement then start looking for the next one
        if self.next_inn_num.get(adventurer) is not None and self.next_inn_num.get(adventurer) < len(inns):
            if inn == inns[self.next_inn_num.get(adventurer)]:
                print(self.name+"has reached their intended Inn, and will now head for Inn #"+str(self.next_inn_num[adventurer]+1))
                self.next_inn_num[adventurer] += 1
        #if there is an inn then always rest
        return True        

    def check_bank_silks(self, adventurer, report="Player is being asked whether to bank"):
        print(self.name+"has visited a city and will start heading to their first Inn again")
        self.next_inn_num[adventurer] = 0
        return super().check_bank_silks(adventurer, report)
    
    # if this is a trade port then always place an inn when offered
    def check_hire_inn(self, adventurer):
        inns = adventurer.game.inns[self]
        if len(inns) < adventurer.current_tile.game.max_inns and adventurer.current_tile.has_trade_port:
            print(self.name+" is placing an Inn where they can trade.")
            return True
        else:
            return False
    
    # Never move an inn when offered, because should simply be repeating a route consisting of all inns
    def check_move_inn(self, adventurer):
        return None
    
    # if a new Adventurer is hired then extend the tracker for which Inn is next to visit
    def check_buy_adventurer(self, adventurer, report=""):
        adventurers = adventurer.game.adventurers[self]
        if super().check_buy_adventurer(adventurer):
            self.next_inn_num[adventurers[-1]] = 0
            return True
        else:
            return False
        
    
    
class PlayerBeginnerRouter(PlayerBeginnerTrader):    
    '''A virtual plaer for Beginner mode of the game Cartolan, who makes decisions that maximise route length
    
    this crude computer player will always move away from the Capital while its Chest has less than the points difference and then towards the Capital once it has collected enough silks
    if it can't move away from the Capital as desired, but can move, it will avoid the clockwise rotation of the wind, by heading downwind to the left
    if it can't move toward the Capital as desired, but can move, it will make use of the clockwise rotation of the wind, by heading downwind to the right
    unlike the crude trader, it will establish inns only on its final move
    
    
    Methods:
    continue_move takes a Cartolan.Adventurer
    check_hire_inn takes a Cartolan.Adventurer
    check_move_inn takes a Cartolan.Adventurer
    '''    
    def continue_move(self, adventurer):
        inns = adventurer.game.inns[self]
        #with some probability, move in a random direction, to break out of degenerate situations
        if random.random() < self.p_deviate:
            adventurer.move(random.choice(['n','e','s','w']))
        #locate the next unvisited inn and move towards them, or if all inns have been visited either explore or return home
        elif self.next_inn_num.get(adventurer) is not None and  self.next_inn_num.get(adventurer) < len(inns):
            print("As a Router, "+self.name+" is moving towards their next Inn, #"+str(self.next_inn_num.get(adventurer)))
            self.move_towards_tile(adventurer, inns[self.next_inn_num.get(adventurer)].current_tile)
        else:
            if self.next_inn_num.get(adventurer):
                print("As a Router, "+self.name+" has visited all their "+str(self.next_inn_num.get(adventurer) + 1)+" Inns")
#            if (adventurer.silks <= adventurer.game.silks_difference):
            if (adventurer.silks < getattr(adventurer.game, self.return_city_attr)):
                self.explore_best_space(adventurer)
#                 self.explore_above_distance(adventurer, adventurer.latest_city, adventurer.game.CITY_DOMAIN_RADIUS)
            else:
                self.move_towards_tile(adventurer, adventurer.latest_city)

        #if this is a trade port then always trade
#             if isinstance(adventurer.current_tile, TradePortTile):
        if adventurer.current_tile.has_trade_port:
            adventurer.trade(adventurer.current_tile)
        if isinstance(adventurer.current_tile, CityTile):
            print(self.name+" has visited a city and will start heading to their first Inn again")
            self.next_inn_num[adventurer] = 0
        return True
    
    # if this is the last movement of a turn then always place an inn when offered
    def check_hire_inn(self, adventurer):
        inns = adventurer.game.inns[self]
        #if this would otherwise be the last move this turn, then place an inn
        if len(inns) < adventurer.game.max_inns and not adventurer.can_move(None):
            print(self.name+" is placing an Inn where they have struggled to move.")
            return True
        else:
            return False
    
    # move inns as further exploration is done, so that the route can evolve over time
    def check_move_inn(self, adventurer):
        inns = adventurer.game.inns[self]
        return inns.pop(0)


class PlayerRegularExplorer(PlayerBeginnerExplorer):    
    '''A virtual player for Regular Cartolan, that favours exploration
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates and restore ransacked inns
    
    Methods:
    continue_turn takes a Cartolan.Adventurer
    check_attack_adventurer takes two Cartolan.Adventurers
    check_attack_inn takes a Cartolan.Adventurer and a Carolan.Inn
    check_restore_inn takes a Cartolan.Adventurer and a Carolan.Inn
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
        preferred_guaranteed = False #Keep track of whether there is a Chest map that will guarantee this exploration succeeds
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
                    score_guaranteed = None #An int for the index of the Chest map that fits
                    for tile in adventurer.chest_maps:
                        if adventurer.rotated_tile_fits(tile, compass_point, adventurer.get_adjoining_edges(new_longitude, new_latitude)):
                            score_guaranteed = adventurer.chest_maps.index(tile)
                    if preferred_guaranteed:
                        if score_guaranteed is not None:
                            #Omly bother evaluating if this exploration is also guaranteed
                            if potential_score > preferred_score:
                                preferred_move = compass_point
                                preferred_score = potential_score
                                adventurer.chosen_map_index = score_guaranteed #Select this chest map to be used
                    else:
                        #Either a higher reward or a guaranteed reward will make this move preferable
                        if score_guaranteed is not None or potential_score > preferred_score:
                            preferred_move = compass_point
                            preferred_score = potential_score
                            adventurer.chosen_map_index = score_guaranteed #Select this chest map to be used
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
              +str(adventurer.silks)+ " silks, and is on the "
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
        # if the adventurer has a pirate token and the silks from an arrest exceeds the loss from piracy then stick around and fight
        if (other_adventurer.pirate_token and other_adventurer.player != self
           and adventurer.silks < adventurer.game.value_arrest):
            return True
        return False
    
    def check_attack_inn(self, adventurer, inn):
        # Explorer will never attack inns
        return False
    
    def check_steal_amount(self, adventurer, maximum, default):
        return default
    
    def check_restore_inn(self, adventurer, inn):
        if inn.player == adventurer.player and adventurer.silks >= adventurer.game.cost_inn_restore:
            return True
        return False
    
    # if half Disaster tile dropped silks exceeds own silks then try to collect it
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
    
    this crude computer player seeks out opponents adventurers and inns to attack, and otherwise behaves like the Explorer 
    
    Methods:
    continue_move takes a Cartolan.Adventurer
    check_attack_adventurer takes two Cartolan.Adventurers
    check_court_disaster takes a Cartolan.Adventurer and a Cartolan.DisasterTile
    check_attack_inn takes a Cartolan.Adventurer and a Cartolan.Inn
    '''
    def continue_move(self, adventurer):    
    # seek out the other player's Adventurer or Inn or Disaster tile with the most silks
        
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
#        elif(adventurer.silks > adventurer.game.silks_difference):
        elif(adventurer.silks >= getattr(adventurer.game, self.return_city_attr)):
            self.move_towards_tile(adventurer, adventurer.latest_city)
        else:
            # if there is an adventurer on the same tile then attack them
            #update awareness of disaster tiles, to avoid them
            for other_adventurer in adventurer.current_tile.adventurers:
                if self.check_attack_adventurer(adventurer, other_adventurer):
                    print(self.name+ "'s adventurer is waiting on their current tile to attack an adventurer belonging to " 
                          +other_adventurer.player.name)
                    adventurer.wait()
            
            # check all other players' adventurers and inns and tiles for the most lucrative
            max_score = 0
            score_location = None
            for player in adventurer.game.players:
                if player != self:
                    for other_adventurer in adventurer.game.adventurers[player]:
                        if max_score < other_adventurer.silks // 2 + other_adventurer.silks % 2:
                            max_score = other_adventurer.silks // 2 + other_adventurer.silks % 2
                            score_location = other_adventurer.current_tile
                    for inn in adventurer.game.inns[self]:
                        if max_score < inn.silks + 1:
                            max_score = inn.silks + 1
                            score_location = inn.current_tile
            for longitude in adventurer.game.play_area:
                for latitude in adventurer.game.play_area[longitude]:
                    tile = adventurer.game.play_area[longitude][latitude] 
                if max_score < tile.dropped_silks:
                    max_score = tile.dropped_silks
                    score_location = tile
            if score_location is None:
#                 self.explore_away_from_tile(adventurer, adventurer.latest_city)
                self.explore_best_space(adventurer)
            else:
                print("Pirate is moving towards the tile at location "+str(score_location.tile_position.longitude)+", "+str(score_location.tile_position.latitude))
                self.move_towards_tile(adventurer, score_location)
        return True
    
    # attack adventurers or inns when encountered
    def check_attack_adventurer(self, adventurer, other_adventurer):
        # if the adventurer has less silks to steal than the pirate has to bank they leave it
        if (other_adventurer.player != self
           and adventurer.silks < other_adventurer.silks // 2 + other_adventurer.silks % 2):
            return True
        return False
    
    # if half Disaster tile dropped silks exceeds own silks then try to collect it
    def check_court_disaster(self, adventurer, disaster_tile):
        if adventurer.silks < disaster_tile.dropped_silks // 2 + disaster_tile.dropped_silks % 2:
            return True
        return False
    
    def check_attack_inn(self, adventurer, inn):
        return True

class PlayerAdvancedExplorer(PlayerRegularExplorer):
    '''Extends Regular to incorporate buying cards.
    '''
    P_BUY_MANUSCRIPT = 0.25 #The probability of spending Vault silks on Manuscript cards when affordable
    RETURN_CITY_ATTR = "cost_manuscript"

    def __init__(self, name):
        super().__init__(name)
        self.p_buy_manuscript = self.P_BUY_MANUSCRIPT
        self.return_city_attr = self.RETURN_CITY_ATTR
    
    def continue_turn(self, adventurer):
        if isinstance(adventurer.game, GameAdvanced):
            if adventurer.game.assigned_cultures.get(self) is None:
                adventurer.game.choose_culture(self)
        if isinstance(adventurer, AdventurerAdvanced):
            if adventurer.character_card is None:
                adventurer.choose_character()
        
        super().continue_turn(adventurer)
    
    def check_buy_manuscript(self, adventurer):
        #randomly choose not to buy, regardless of other conditions
        if random.random() > self.p_buy_manuscript:
            return False
        
        print(self.name+" is deciding whether to buy a Manuscript card")
        if adventurer.game.vault_silks[adventurer.player] >= adventurer.game.cost_manuscript:
            winning_difference = adventurer.game.winning_silks_difference
            if winning_difference is None:
                return self._check_purchase_worthwhile(adventurer, adventurer.game.cost_manuscript)
            #Check whether player has won compared to wealthiest opponent
            wealthiest_opponent_silks = 0
            #Check whether any opponent is in a position to win based just on their incoming silks, if tech is bought
            opponent_near_win = False
            for player in adventurer.game.players:
                if player is not self:
                    if adventurer.game.vault_silks[player] > wealthiest_opponent_silks:
                        wealthiest_opponent_silks = adventurer.game.vault_silks[player]
                    player_chest_silks = 0
                    for other_adventurer in adventurer.game.adventurers[player]:
                        player_chest_silks += other_adventurer.silks
                    if (adventurer.game.vault_silks[player] + player_chest_silks
                        > winning_difference + adventurer.game.vault_silks[adventurer.player] - adventurer.game.cost_manuscript):
                        opponent_near_win = True
            #Don't buy if player has won compared to wealthiest opponent
            if adventurer.game.vault_silks[adventurer.player] > wealthiest_opponent_silks + winning_difference:
                return False
            #Buy if no opponent can then win based on their incoming silks
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
        self.p_buy_manuscript = self.P_BUY_MANUSCRIPT
        self.return_city_attr = self.RETURN_CITY_ATTR
    
class PlayerAdvancedRouter(PlayerRegularRouter, PlayerAdvancedExplorer):    
    '''A virtual player for Regular Cartolan that favours maximising trade value
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates'''
    def __init__(self, name):
        super().__init__(name)
        self.p_buy_manuscript = self.P_BUY_MANUSCRIPT
        self.return_city_attr = self.RETURN_CITY_ATTR
    
class PlayerAdvancedPirate(PlayerRegularPirate, PlayerAdvancedExplorer):    
    '''A virtual player for Regular Cartolan that favours maximising trade value
    
    this crude computer player behaves like the Beginner mode version, but has additional behaviour for trying to arrest pirates'''
    def __init__(self, name):
        super().__init__(name)
        self.p_buy_manuscript = self.P_BUY_MANUSCRIPT
        self.return_city_attr = self.RETURN_CITY_ATTR
    