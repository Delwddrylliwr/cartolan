'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

from base import Player, CityTile
from game import GameRegular
from regular import AdventurerRegular
from advanced import AdventurerAdvanced

class PlayerHuman(Player):
    '''A pyplot-based interface for a human players to make decisions in live play.
    '''
    def __init__(self, colour):
        super().__init__(colour)
        self.attack_history = {} #to keep track of when this player has attacked, for reference
        
        #Allow for fixed responses to checks on particular actions, to speed up GUI
        self.fixed_responses = {"rest":None
                           , "attack":None
                           , "place_agent":None
                           , "restore_agent":None
                           }
        #Keep track of whether the player has chosen to queue up a move rather than take any Actions
        self.queued_move = None
        self.fast_forward = False
    
    def establish_moves(self, adventurer):
        '''Checks the available moves away from their tile for an adventurer and provides suitable highlights, as well as a mapping from coordinates to compass points
        '''
        game = adventurer.game
        moves = {}
        move_map = {}
            
        if adventurer.has_remaining_moves():
            #Build up a list of move options to highlight
            moves["move"] = []
            moves["invalid"] = [] 
            
            #highlight the adjacent tiles that can be reached this move
            for compass_point in ['n', 'e', 's', 'w']:
                #locate the space in the play area that the Adventurer is moving into
                longitude_increment = int(compass_point.lower() in ["east","e"]) - int(compass_point.lower() in ["west","w"])
                potential_longitude = adventurer.current_tile.tile_position.longitude + longitude_increment
                latitude_increment = int(compass_point.lower() in ["north","n"]) - int(compass_point.lower() in ["south","s"])
                potential_latitude = adventurer.current_tile.tile_position.latitude + latitude_increment
                can_move = adventurer.can_move(compass_point)
                if can_move:
                    moves["move"].append([potential_longitude, potential_latitude])
                else:
                    moves["invalid"].append([potential_longitude, potential_latitude])
                #keep track of what compass point these coordinates correspond to
                if move_map.get(potential_longitude):
                    move_map[potential_longitude][potential_latitude] = compass_point
                else:
                    move_map[potential_longitude] = {potential_latitude:compass_point}
                    
        return moves, move_map
    
    def respond_menu_choices(self, adventurer, gui_input):
        '''In case input isn't coordinates for a game move or action, check whether it is a menu interaction changing a player/Adventurer preference
        
        Arguments:
        adventurer takes a Cartolan Adventurer
        move_coords will only respond to a dict with a key value pair for a menu selection
        '''
        game_vis = self.games[adventurer.game.game_id]["game_vis"]
        if isinstance(gui_input, dict):    
            if isinstance(adventurer, AdventurerRegular):
                preferred_tile = gui_input.get("preferred_tile")
                print("Player received menu input, choosing a chest tile, with a value of "+str(preferred_tile))
                if isinstance(preferred_tile, int):
                    if adventurer.preferred_tile_num == preferred_tile:
                        adventurer.preferred_tile_num = None
                    elif preferred_tile < len(adventurer.chest_tiles):
                        adventurer.preferred_tile_num = preferred_tile
                    game_vis.draw_chest_tiles(adventurer.chest_tiles, adventurer.preferred_tile_num, adventurer.num_chest_tiles)
                for action in self.fixed_responses:
                    fixed_response = gui_input.get(action)
                    if isinstance(fixed_response, bool) or fixed_response is None:
                        self.fixed_responses[action] = fixed_response
            if isinstance(adventurer, AdventurerAdvanced):
                game_vis.draw_cards(adventurer)
                
    
    def continue_move(self, adventurer):
        '''Offers the user available moves, translates their mouse input into movement, and updates visuals.
        
        Arguments
        adventurer takes a Cartolan.Adventurer
        '''
        #If Actions were skipped for a queued move, then carry it out and start checking actions with input again
        if self.fast_forward:
            self.fast_forward = False
            if self.queued_move in ['n', 'e', 's', 'w']:
                moved = adventurer.move(self.queued_move)
                #check whether the turn is over despite movement failing, e.g. it failed because exploration failed
                if adventurer.turns_moved == adventurer.game.turn:
                    moved = True
                return moved
        
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
                        
        #prompt the player to choose a tile to move on to
        print("Prompting the "+self.colour+" player for input")
#        game_vis.clear_prompt()
        game_vis.give_prompt("Click which tile you would like "+str(self.colour)+" adventurer #" 
                                       +str(game.adventurers[self].index(adventurer)+1) 
                                       +" to move to?")
        
        moves, move_map = self.establish_moves(adventurer)
        #Include waiting in the current location among move options
        moves["move"].append([adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude])
        longitude_moves = move_map.get(adventurer.current_tile.tile_position.longitude)    
        if longitude_moves:
            longitude_moves[adventurer.current_tile.tile_position.latitude] = 'wait'
        else:
            move_map[adventurer.current_tile.tile_position.longitude] = {adventurer.current_tile.tile_position.latitude:'wait'}
        #add all cities' coordinates to a list of abandon expedition moves, unless a valid move is possible
        moves["abandon"] = []
        for city_tile in game.cities:
            #Check whether this city can be reached by movement, before giving the option to abandon the expedition
            city_longitude = city_tile.tile_position.longitude
            city_latitude = city_tile.tile_position.latitude
#            print("City tile found at coordinates: "+str(city_longitude)+str(city_latitude))
            if city_longitude is not None and city_latitude is not None:
                if [city_longitude, city_latitude] in moves["move"]:
                        continue
                elif [city_longitude, city_latitude] in moves["invalid"]:    
                    moves["invalid"].pop(moves["invalid"].index([city_longitude, city_latitude]))
                moves["abandon"].append([city_longitude, city_latitude])
        
        #highlight the tiles
#        print("Highlighting the available moves for the "+self.colour+" player's Adventurer #"+str(game.adventurers[self].index(adventurer)+1))
        #redraw all the tokens and scores
        game_vis.draw_play_area()
        game_vis.draw_routes()
        game_vis.draw_tokens()
        game_vis.draw_scores()
        moves_since_rest = adventurer.downwind_moves + adventurer.upwind_moves + adventurer.land_moves
        max_moves = adventurer.max_downwind_moves
        game_vis.draw_move_options(moves_since_rest, moves, max_moves)
        if isinstance(adventurer, AdventurerRegular):
            game_vis.draw_chest_tiles(adventurer.chest_tiles, adventurer.preferred_tile_num, adventurer.num_chest_tiles)
        if isinstance(adventurer, AdventurerAdvanced):
            game_vis.draw_cards(adventurer)
        
        #Carry out the player's chosen move
        move_coords = game_vis.get_input_coords(adventurer)
        #Recieve input for menu actions that change player preferences, while no coordinates are received
        while move_coords not in moves["move"] and move_coords not in moves["abandon"]:
            self.respond_menu_choices(adventurer, move_coords)
            move_coords = game_vis.get_input_coords(adventurer)
        if move_coords in moves["move"]:
#            print(self.colour+" player chose valid coordinates to move to.")
            if move_map[move_coords[0]].get(move_coords[1]) == "wait":
                game_vis.clear_move_options()
                moved = adventurer.wait()
#                print("moved = "+str(moved))
            else:
                game_vis.clear_move_options()
                moved = adventurer.move(move_map[move_coords[0]].get(move_coords[1]))
                #check whether the turn is over despite movement failing, e.g. it failed because exploration failed
                if adventurer.turns_moved == adventurer.game.turn:
                    moved = True
        elif move_coords in moves["abandon"]:
            #Transfer the Adventurer's wealth to sit on their current tile for others to collect
            city_tile = game.play_area[move_coords[0]][move_coords[1]]
            adventurer.abandon_expedition(city_tile)
        else:
            game_vis.clear_prompt()
            game_vis.give_prompt("This is not a valid move, so waiting in place. click to continue.")
            game_vis.clear_move_options()
            game_vis.get_input_coords(adventurer)
            game_vis.clear_prompt()
            adventurer.wait()
        game_vis.draw_play_area()
        #clean up the highlights
        game_vis.clear_prompt()
        game_vis.clear_move_options()
        return True
    
    def continue_turn(self, adventurer):
        '''Iteratively allows the players to move.
        
        Arguments
        adventurer is a Cartolan.Adventurer
        '''
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        adventurers = game.adventurers[self]
#        #Clear the previously drawn route for this adventurer, before drawing a new one
#        adventurer.route = [adventurer.current_tile]
        #Update the play area after other player's movements, such as virtual players
        game_vis.start_turn(self.colour)
        game_vis.draw_play_area()
        game_vis.draw_routes()
        game_vis.draw_tokens()
        game_vis.draw_scores()
        #Have the player acknowledge that it is their turn
#        game_vis.clear_prompt()
        game_vis.give_prompt(self.colour+" player's turn for Adventurer #"+str(adventurers.index(adventurer)+1)+". click to continue.")
        game_vis.draw_move_options()
        game_vis.get_input_coords(adventurer)
        game_vis.clear_prompt()
        
        #Move while moves are still available
        while adventurer.turns_moved < adventurer.game.turn:
            print(self.colour+" player's Adventurer #"+str(adventurers.index(adventurer)+1)+" is still able to move.")
            self.continue_move(adventurer)
        
        #If this is not the last adventurer for the player then finish here, otherwise clear the routes for all the non-human players that will play between this and the next human player
        if adventurers.index(adventurer) < len(adventurers) - 1:
            return True
        
#        #we'll need to clear routes up to either the next human player after this one in the play order...
#        players = game.players
#        for player_index in range(players.index(self)+1, len(players)):
#            if isinstance(players[player_index], PlayerHuman):
#                return True
#            for adventurer in game.adventurers[players[player_index]]:
#                adventurer.route = [adventurer.current_tile]
#        #...or if this was the last human player then we clear up to the first human in the play order
#        for player in players:
#            if isinstance(player, PlayerHuman):
#                return True
#            for adventurer in game.adventurers[player]:
#                adventurer.route = [adventurer.current_tile]
        
        return True
    
    def check_action(self, adventurer, action_type, actions, prompt):
        '''Generic function to handle seeking player input on whether to carry out actions
        
        Inputs:
        adventurer takes a Cartolan Adventurer which is able to take the action
        
        prompt takes a string that will be communicated to the human player
        '''
        if self.fast_forward:
            return None
        
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #make sure that tiles and token positions are up to date
        game_vis.draw_play_area()
        game_vis.draw_routes()
        game_vis.draw_tokens()
        game_vis.draw_scores()
        if isinstance(adventurer, AdventurerRegular):
            game_vis.draw_chest_tiles(adventurer.chest_tiles, adventurer.preferred_tile_num, adventurer.num_chest_tiles)
        if isinstance(adventurer, AdventurerAdvanced):
            game_vis.draw_cards(adventurer)
        
        print("Adding movement options that will be available next move, to allow skipping of actions")
        if not isinstance(adventurer.current_tile, CityTile): #If this is a buying action from the city then the turn is about to end, even with spare moves
            moves, move_map = self.establish_moves(adventurer)
            for move in moves:
                actions[move] = moves[move]            
        
        print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(game.adventurers[self].index(adventurer)+1)
              +" can act")
        moves_since_rest = adventurer.downwind_moves + adventurer.upwind_moves + adventurer.land_moves
        max_moves = adventurer.max_downwind_moves
        game_vis.draw_move_options(moves_since_rest, actions, max_moves)

        #prompt the player to input
        print("Prompting the "+self.colour+" player for input")
#            game_vis.clear_prompt()
        game_vis.give_prompt(prompt)
        
        move_location = None
        move_coords = game_vis.get_input_coords(adventurer)
        if move_coords in actions[action_type]:
            print(self.colour+" player chose the coordinates of the tile where their Adventurer can buy.")
            move_location = adventurer.game.play_area[move_coords[0]][move_coords[1]]
        elif actions.get("move"): # If there were movement options, then check whether these were chosen
            if move_coords in actions["move"]:
                self.fast_forward = True
                self.queued_move = move_map[move_coords[0]].get(move_coords[1])
                move_location = None
        else:
            print(self.colour+" player chose coordinates away from the tile where their Adventurer can buy.")
            move_location = None

        #clean up the highlights
        game_vis.clear_prompt()
        game_vis.clear_move_options()
#             game_vis.draw_tokens()
        return move_location
        
    #if offered by a Wonder, always trade
    def check_trade(self, adventurer, tile):
        return True
    
    #if offered by an agent, always collect wealth
    #@TODO let the player choose how much wealth to collect using input()
    def check_collect_wealth(self, agent):
        return True
    
    def check_rest(self, adventurer, agent):
        game  = adventurer.game
        actions = {}
        if agent in adventurer.agents_rested:
            return False
        else:
            if agent.player == self:
                action_type = "rest"
                actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                            , adventurer.current_tile.tile_position.latitude]]
                prompt = ("If you want "+str(self.colour)+" adventurer #" 
                                               +str(game.adventurers[self].index(adventurer)+1) 
                                               +" to rest then click their tile, otherwise click elsewhere.")
            elif adventurer.wealth >= adventurer.game.cost_agent_exploring:
                action_type = "buy"
                actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                            , adventurer.current_tile.tile_position.latitude]]
                prompt = ("If you want "+str(self.colour)+" adventurer #" 
                                               +str(game.adventurers[self].index(adventurer)+1) 
                                               +" to rest for "
                                               +str(game.cost_agent_rest)+
                                               " treasure then click their tile, otherwise click elsewhere.")
            else:
                return False
        #Check whether the player wants to go ahead
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
        
    #if offered by a city, then give the player the option to pay and refresh their chest maps
    def check_buy_maps(self, adventurer, report="Player is being asked whether to pay to refresh their chest maps"):
        print(report)
        actions = {}
        action_type = "buy"
        actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]
        prompt = ("If you want your Adventurer to buy a new set of maps for "
                             +str(adventurer.game.cost_refresh_maps)
                             +" then click the City, otherwise click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
    
    #if offered by a city, then give the player the option to buy a discovery card 
    def check_buy_tech(self, adventurer, report="Player is being asked whether to buy a Discovery card"):
        print(report)
        actions = {}
        action_type = "buy"
        actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]
        
        prompt = ("If you want your Adventurer to buy a manuscript for " 
                             +str(adventurer.game.cost_tech)
                             +" then click the City, otherwise click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
    
    #if offered by a city, then give the player the option to buy an Adventurer 
    def check_buy_adventurer(self, adventurer, report="Player is being asked whether to buy an Adventurer"):
        print(report)
        actions = {}
        action_type = "buy"
        actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]
        prompt = ("If you want to recruit another Adventurer for " 
                             +str(adventurer.game.cost_adventurer)
                             +" then click the City, otherwise click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False

    # Let the player choose whether to place an agent when offered
    def check_place_agent(self, adventurer):
        actions = {}
        action_type = "buy"
        actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]
        prompt = ("If you want your Adventurer to recruit an Agent on this tile for "+str(adventurer.cost_agent_exploring)
                        +" treasure then click it, otherwise click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
        
    # When offered, give the player the option to buy on any tile that doesn't have an active Agent 
    def check_buy_agent(self, adventurer, report="Player has been offered to buy an agent by a city"):
        print(report)
        actions = {}
        action_type = "buy"
        #Establish a list of all tiles without an active Agent, to offer the player
        actions[action_type] = []
        prompt = ("Click any unoccupied tile to hire an Agent and send them there for " 
                             +str(adventurer.game.cost_agent_from_city) 
                             +" treasure, otherwise click elsewhere.")
        play_area = adventurer.game.play_area
        for longitude in play_area:
            for latitude in play_area[longitude]:
#                    #Check that this lat and latitude are outside any city's domain
#                    outside_city_domains = True
#                    for city_tile in adventurer.game.cities:
#                        city_longitude = city_tile.tile_position.longitude
#                        city_latitude = city_tile.tile_position.latitude
#                        if abs(longitude - city_longitude)+abs(latitude - city_latitude) <= adventurer.game.CITY_DOMAIN_RADIUS:
#                            outside_city_domains = False
#                    #If outside all cities' domains then this is a valid location to place an agent
#                    if outside_city_domains:
                tile = play_area[longitude][latitude] 
                if tile.agent is None:
                    if not isinstance(tile, CityTile):
                        actions[action_type].append([tile.tile_position.longitude, tile.tile_position.latitude])
                elif isinstance(adventurer.game, GameRegular):
                    if tile.agent.is_dispossessed:
                        actions[action_type].append([tile.tile_position.longitude, tile.tile_position.latitude])
        return self.check_action(adventurer, action_type, actions, prompt)
        
    # Let the player choose whether to move one of their Agents
    def check_move_agent(self, adventurer):     
        action_type = "move_agent"
        actions = {action_type:[]}
        for agent in adventurer.game.agents[self]:
            actions[action_type].append([agent.current_tile.tile_position.longitude, agent.current_tile.tile_position.latitude])
        prompt = ("You will need to move an existing " +str(self.colour)+ " Agent, click to choose one"
                                       +", otherwise click elsewhere to cancel buying an Agent.")
        selected_tile = self.check_action(adventurer, action_type, actions, prompt)
        if selected_tile is not None:
            return selected_tile.agent
        else:
            return None
    
    def check_transfer_agent(self, adventurer):
        action_type = "agent_transfer"
        actions = {action_type:[]}
        for agent in adventurer.game.agents[self]:
            actions[action_type].append([agent.current_tile.tile_position.longitude, agent.current_tile.tile_position.latitude])
        prompt = ("Select an Agent If you want " +str(self.colour)+ " Adventurer to move treasure there "
                                       +", otherwise click elsewhere.")
        selected_tile = self.check_action(adventurer, action_type, actions, prompt)
        if selected_tile is not None:
            return selected_tile.agent
        else:
            return None
    
    #Give the player the choice to attack
    #@TODO highlight specific tokens to attack
    def check_attack_adventurer(self, adventurer, other_adventurer):
        action_type = "attack"
        actions = {action_type:[[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]}
        prompt = ("If you want "+str(self.colour)+" Adventurer #" 
                           +str(adventurer.game.adventurers[self].index(adventurer)+1) 
                           +" to attack "+ other_adventurer.player.colour+" player's Adventurer, then click their tile. "
                                      +" Otherwise, click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
    
    #if offered by a city then always bank everything
    def check_deposit(self, adventurer, maximum, minimum=0, report="Player is being asked whether to bank treasure"):
        print(report)
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #Protect in case of inversions
        if minimum > maximum:
            old_max = maximum
            maximum = minimum
            minimum = old_max
        
        if isinstance(adventurer.current_tile, CityTile): #As there is a separate check to withdraw treasure before a turn, assume they will always bank everything
            return adventurer.wealth
        else:
            deposit_amount = None
            while deposit_amount not in range(minimum, maximum+1):
                deposit_amount = game_vis.get_input_value("How much treasure will your Adventurer move to this Agent, from "+str(minimum)+" to "+str(maximum)+"?", maximum, minimum)
            return deposit_amount
    
    def check_travel_money(self, adventurer, maximum, default):
        '''Lets the player input a figure for the wealth that will be taken from the Vault before an expedition
        '''
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #Ask the visual for an amount, so that it can either prompt the player or default
        travel_money = game_vis.get_input_value("How much treasure will your Adventurer take with them, up to "+str(maximum)+"?", maximum)
        if travel_money in range(0, maximum+1):
            return travel_money
        else:
            return default
    
    #prompt the player on victory for how much wealth to take using input()
    def check_steal_amount(self, adventurer, maximum, default):
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #Ask the visual for an amount, so that it can either prompt the player or default
        steal_amount = game_vis.get_input_value("Your Adventurer's piracy succeeded. How much treasure will they take, up to "+str(maximum)+"?", maximum)
        if steal_amount in range(0, maximum+1):
            return steal_amount
        else:
            return default
    
    #@TODO prompt the player on victory for how much wealth to take 
    def check_attack_agent(self, adventurer, agent):
        action_type = "attack"
        actions = {action_type:[[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]}
        prompt = ("If you want "+str(self.colour)+" Adventurer #" 
                           +str(adventurer.game.adventurers[self].index(adventurer)+1) 
                           +" to attack "+ agent.player.colour+" player's Agent, then click their tile. "
                                      +" Otherwise, click elsewhere.")    
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
    
    # Always restor own Agents if it can be afforded
    def check_restore_agent(self, adventurer, agent):
        action_type = "buy"
        actions = {action_type:[[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]}
        prompt = ("If you want your Adventurer to restore your dispossessed Agent on this tile for "+str(adventurer.game.cost_agent_restore)
                        +" then click it, otherwise click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
        
    # if half Disaster tile dropped wealth exceeds own wealth then try to collect it
    def check_court_disaster(self, adventurer, disaster_tile):
        action_type = "attack"
        actions = {action_type:[[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]}
        prompt = ("If you want your pirate Adventurer to try and recover "+str(disaster_tile.dropped_wealth // 2)
                        +" from the tile then click it, otherwise click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
