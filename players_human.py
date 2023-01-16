'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

from base import Player, Agent, CityTile
from game import GameRegular, GameAdvanced
from regular import AdventurerRegular
from advanced import AdventurerAdvanced
#import copy

class PlayerHuman(Player):
    '''A pyplot-based interface for a human players to make decisions in live play.
    '''
    def __init__(self, name):
        super().__init__(name)
        self.attack_history = {} #to keep track of when this player has attacked, for reference
        
        #Allow for fixed responses to checks on particular actions, to speed up GUI
        self.clear_auto_actions()
        #Keep track of whether the player has chosen to queue up a move rather than take any Actions
        self.queued_move = None
        self.fast_forward = False
        #Keep track of any routes that the player has chosen to follow
        self.follow_route = None
        self.destination = None
        #Keep track of whether the turn has been reset mid-move
        self.undone = False
    
    def clear_auto_actions(self):
        '''Resets any fixed responses that have been set.
        '''
        self.auto_actions = {"rest":None
                           , "buy_rest":None
                           , "attack":None
                           }
        self.follow_route = []
        self.destination = None
    
    def establish_moves(self, adventurer):
        '''Checks the available moves away from their tile for an adventurer and provides suitable highlights, as well as a mapping from coordinates to compass points
        '''
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
            if gui_input.get("toggle"):
                toggled_action = gui_input["toggle"]
                if self.auto_actions[toggled_action] is None:
                    self.auto_actions[toggled_action] = True
                elif self.auto_actions[toggled_action]:
                    self.auto_actions[toggled_action] = False
                else:
                    self.auto_actions[toggled_action] = None
                game_vis.draw_toggle_menu(self.auto_actions)
            if isinstance(adventurer, AdventurerRegular):
                preferred_tile = gui_input.get("preferred_tile")
                if isinstance(preferred_tile, int):
                    print("Player received menu input, choosing chest tile #"+str(preferred_tile+1))
                    if adventurer.preferred_tile_num == preferred_tile:
                        adventurer.preferred_tile_num = None
                    elif preferred_tile < len(adventurer.chest_tiles):
                        adventurer.preferred_tile_num = preferred_tile
                    game_vis.draw_chest_tiles()
            if isinstance(adventurer, AdventurerAdvanced):
                game_vis.draw_cards()
    
    def move_to_tile(self, adventurer, tile):
        '''Establishes the direction for movement to an adjacent tile.'''
        print(str(adventurer.player.name) +": trying a move from the tile at "+str(adventurer.current_tile.tile_position.longitude)+ ", " +str(adventurer.current_tile.tile_position.latitude)+" onto the tile at " +str(tile.tile_position.longitude)+ ", " +str(tile.tile_position.latitude))
        #check that the tile is adjacent to the current one
        if abs(adventurer.current_tile.tile_position.longitude - tile.tile_position.longitude) + abs(adventurer.current_tile.tile_position.latitude - tile.tile_position.latitude) > 1:
            print("Next tile in route was further away than a single move!?")
            return False
        #establish directions to the tile
        if adventurer.current_tile.tile_position.latitude < tile.tile_position.latitude:
            return adventurer.move('n')
        elif adventurer.current_tile.tile_position.longitude < tile.tile_position.longitude:
            return adventurer.move('e')
        elif adventurer.current_tile.tile_position.latitude > tile.tile_position.latitude:
            return adventurer.move('s')
        else:
            return adventurer.move('w')
    
    def continue_move(self, adventurer):
        '''Offers the user available moves, translates their mouse input into movement, and updates visuals.
        
        Arguments
        adventurer takes a Cartolan.Adventurer
        '''
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #If a route is being followed, then try to proceed to the next tile until hitting a city
        if self.follow_route:
            next_tile = self.follow_route.pop(0)
            while adventurer.current_tile == next_tile:
                if self.follow_route:
                    next_tile = self.follow_route.pop(0)
                else:
                    return False
            if ((next_tile == self.destination or isinstance(next_tile, CityTile)) 
                and adventurer.has_remaining_moves()):
                #As about to complete a route to the city, turn off route-following mode
                self.follow_route = []
                self.destination = None
##                self.clear_auto_actions()
            return self.move_to_tile(adventurer, next_tile)
        
        #If Actions were skipped for a queued move, then carry it out and start checking actions with input again
        if self.fast_forward:
            self.fast_forward = False
            if self.queued_move in ['n', 'e', 's', 'w']:
                moved = adventurer.move(self.queued_move)
                #check whether the turn is over despite movement failing, e.g. it failed because exploration failed
                if adventurer.turns_moved == adventurer.game.turn:
                    moved = True
                return moved
        
        #Bring focus back to the moving adventurer
        game_vis.viewed_adventurer = adventurer
        game_vis.viewed_player_name = adventurer.player.name
        game_vis.viewed_adventurer_number = game.adventurers[adventurer.player].index(adventurer)
                        
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
#        print("Highlighting the available moves for the "+self.name+" player's Adventurer #"+str(game.adventurers[self].index(adventurer)+1))
        #redraw all the tokens and scores
        #make sure that tiles and token positions are up to date
        game_vis.draw_play_area()
        game_vis.draw_routes()
        #Draw the left menu items
        game_vis.draw_scores()
        if isinstance(adventurer, AdventurerAdvanced):
            game_vis.draw_cards()
        #Draw the right menu items
        game_vis.draw_move_count()
        game_vis.draw_toggle_menu(self.auto_actions)
        game_vis.draw_routes_menu()
        if isinstance(adventurer, AdventurerRegular):
            adventurer.match_chest_directions()
            game_vis.draw_chest_tiles()
        game_vis.draw_tile_piles()
        game_vis.draw_discard_pile()
        game_vis.draw_undo_button()
        game_vis.draw_move_options(moves)
        game_vis.draw_tokens() #draw them on top of highlights
            
        #prompt the player to choose a tile to move on to
        print("Prompting the "+self.name+" for input")
#        game_vis.clear_prompt()
        prompt = ("Click which tile you would like "+str(self.name)+"'s Adventurer #" 
                                       +str(game.adventurers[self].index(adventurer)+1) 
                                       +" to move to?")
        if game_vis.drawn_routes:
            prompt += " Or select a route to follow."
        game_vis.current_player_name = adventurer.player.name
        game_vis.give_prompt(prompt)

        # Draw the left menu items
        game_vis.draw_scores()
        if isinstance(adventurer, AdventurerAdvanced):
            game_vis.draw_cards()
        # Draw the right menu items
        game_vis.draw_move_count()
        game_vis.draw_toggle_menu(self.auto_actions)
        if isinstance(adventurer, AdventurerRegular):
            adventurer.match_chest_directions()
            game_vis.draw_chest_tiles()
        game_vis.draw_tile_piles()
        game_vis.draw_discard_pile()
        game_vis.draw_undo_button()

        #Carry out the player's chosen move
        player_input = {"Nothing":"Nothing"}
        while player_input.get("Nothing") is not None:
            player_input = game_vis.get_input_coords(adventurer)
        print("Player's input:")
        print(player_input)
        #Recieve input for menu actions that change player preferences, while no coordinates are received
        while (player_input.get("move") is None 
               and player_input.get("abandon") is None):
            if player_input.get("route") is not None:
                if adventurer.current_tile in player_input["route"]:
                    self.follow_route = player_input["route"][:] #Copy the other player's route rather than referncing the list (which would then mean modifying it and disrupting the visuals)
                    destination_coords = player_input["destination"]
                    play_area = adventurer.game.play_area
                    self.destination = None
                    if play_area.get(destination_coords[0]):
                        self.destination = play_area[destination_coords[0]].get(destination_coords[1])
#                    print("Setting out on route of length "+str(len(self.follow_route)))
#                    if self.auto_actions["rest"] is None:
#                        self.auto_actions["rest"] = True #
                    #Remove the route up until the current tile
                    while not self.follow_route[0] == adventurer.current_tile:
                            self.follow_route.pop(0)
                    print("Trimmed route to current tile, with length "+str(len(self.follow_route)))
                    return self.continue_move(adventurer)
                else:
                    player_input = game_vis.get_input_coords(adventurer)
            elif player_input.get("undo") is not None:
                print("The Adventurer's turn has been reset and we need to go back to the start of the turn.")
                self.undone = True
                return False
            else:
                self.respond_menu_choices(adventurer, player_input)
                #Redraw everything in case the adventurer of focus was changed
                game_vis.draw_play_area()
                game_vis.draw_routes()

                game_vis.draw_move_options(moves)
                game_vis.draw_tokens() #draw them on top of highlights
                game_vis.give_prompt(prompt)
                # Draw the left menu items
                game_vis.draw_scores()
                if isinstance(adventurer, AdventurerAdvanced):
                    game_vis.draw_cards()
                # Draw the right menu items
                game_vis.draw_move_count()
                game_vis.draw_toggle_menu(self.auto_actions)
                game_vis.draw_routes_menu()
                if isinstance(adventurer, AdventurerRegular):
                    adventurer.match_chest_directions()
                    game_vis.draw_chest_tiles()
                game_vis.draw_tile_piles()
                game_vis.draw_discard_pile()
                game_vis.draw_undo_button()
                #Seek input again
                player_input = game_vis.get_input_coords(adventurer)
                print("Player's input:")
                print(player_input)

        if player_input.get("move") is not None:
            move_coords = player_input["move"]
#            print(self.name+" player chose valid coordinates to move to.")
            if move_map[move_coords[0]].get(move_coords[1]) == "wait":
                game_vis.clear_move_options()
                moved = adventurer.wait()
#                print("moved = "+str(moved))
            else:
                game_vis.clear_move_options()
                compass_point = move_map[move_coords[0]].get(move_coords[1])
                if compass_point in ["n", "e", "s", "w"]:
                    moved = adventurer.move(compass_point)
                else:
                    moved = adventurer.wait()
                #check whether the turn is over despite movement failing, e.g. it failed because exploration failed
                if adventurer.turns_moved == adventurer.game.turn:
                    moved = True
        elif player_input.get("abandon"):
            move_coords = player_input["abandon"]
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
        adventurer_number = adventurers.index(adventurer)
        
#        #Clear the previously drawn route for this adventurer, before drawing a new one
#        adventurer.route = [adventurer.current_tile]
        #Update the play area after other player's movements, such as virtual players
        game_vis.start_turn(adventurer)
        game_vis.draw_play_area()
        game_vis.draw_routes()
        game_vis.draw_tokens()
        game_vis.draw_scores()
        #Have the player acknowledge that it is their turn
#        game_vis.clear_prompt()
        game_vis.give_prompt(self.name.capitalize()+"'s turn for Adventurer #"+str(adventurer_number+1)+". click to continue.")
#        game_vis.draw_move_options()
        game_vis.get_input_coords(adventurer)
        game_vis.clear_prompt()
        
        if isinstance(game, GameAdvanced):
            if game.assigned_cadres.get(self) is None:
                game.choose_cadre(self)
        if isinstance(adventurer, AdventurerAdvanced):
            if adventurer.character_card is None:
                adventurer.choose_character()
        
        #Backup the game state, in case an undo is needed this turn
        game.save()
#        backup = copy.deepcopy(adventurer)
        
        #Move while moves are still available
        while adventurer.turns_moved < adventurer.game.turn:
            print(self.name.capitalize()+"'s Adventurer #"+str(adventurers.index(adventurer)+1)+" is still able to move.")
            self.continue_move(adventurer)
            #If undo has been invoked then restore the game state from the start of the turn
            if self.undone:
                print("Resetting the turn, after agreement from all clients.")
                adventurer.game.restore()
                #for the adventurer reference in the while loop above, replace all data with
#                adventurer.game = backup.game #Make sure that any further use of this Adventurer instance's game will interact with the restored game
#                game_vis.game = backup.game #Point the visualisation to the backup game instance
#                game_vis.client.game = backup.game #update the turn-scheduling 
                #Make sure that resetting does not continue
                self.undone = False
                game_vis.reset_peer_undos()
        self.follow_route = [] #Break the route-following behaviour at the end of the turn
        self.destination = None
#        self.clear_auto_actions()
        
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
        #Deal with automated player responses, whether fixed responses to certain prompts or ignoring prompts because of a queued move
        if action_type in self.auto_actions.keys():
            if self.auto_actions[action_type] is not None:
                return self.auto_actions[action_type]
        else:
            print("With no fixed response set, stopping following route.")
            self.follow_route = [] #If there was no fixed response then stop automatically following and return control to the player
            self.destination = None
#            self.clear_auto_actions()
        if self.fast_forward:
            return None
        
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #make sure that tiles and token positions are up to date
        game_vis.draw_play_area()
        game_vis.draw_routes()
        #Draw the left menu items
        game_vis.draw_scores()
        if isinstance(adventurer, AdventurerAdvanced):
            game_vis.draw_cards()
        #Draw the right menu items
        game_vis.draw_move_count()
        game_vis.draw_toggle_menu(self.auto_actions)
        game_vis.draw_routes_menu()
        if isinstance(adventurer, AdventurerRegular):
            adventurer.match_chest_directions()
            game_vis.draw_chest_tiles()
        game_vis.draw_tile_piles()
        game_vis.draw_discard_pile()
        game_vis.draw_undo_button()

        print("Adding movement options that will be available next move, to allow skipping of actions")
        if not isinstance(adventurer.current_tile, CityTile): #If this is a buying action from the city then the turn is about to end, even with spare moves
            moves, move_map = self.establish_moves(adventurer)
            for move in moves:
                #first prevent the fast forward move from blocking actions
                for action in actions:
                    for coords in actions[action]:
                        if coords in moves[move]:
                            moves[move].remove(coords)
                #Add these moves to the fast forward options
                actions[move] = moves[move]        
        
        print("Highlighting the tile where "+self.name+"'s Adventurer #"+str(game.adventurers[self].index(adventurer)+1)
              +" can "+action_type)
        game_vis.draw_move_options(actions)
        game_vis.draw_tokens() #draw tokens on top of highlights

        #prompt the player to input
        print("Prompting the "+self.name+" player for input")
#            game_vis.clear_prompt()
        game_vis.current_player_name = adventurer.player.name
        game_vis.give_prompt(prompt)

        # Draw the left menu items
        game_vis.draw_scores()
        if isinstance(adventurer, AdventurerAdvanced):
            game_vis.draw_cards()
        # Draw the right menu items
        game_vis.draw_move_count()
        game_vis.draw_toggle_menu(self.auto_actions)
        if isinstance(adventurer, AdventurerRegular):
            adventurer.match_chest_directions()
            game_vis.draw_chest_tiles()
        game_vis.draw_tile_piles()
        game_vis.draw_discard_pile()
        game_vis.draw_undo_button()
        
        action_location = None
#        player_input = None
#        while not player_input:
        player_input = game_vis.get_input_coords(adventurer)
#        print("Player's input:")
#        print(player_input)
        #Check if this was a menu click, respond and gather another
        while (player_input.get(action_type) is None 
               and player_input.get("move") is None
               and player_input.get("Nothing") is None):
            if player_input.get("undo") is not None:
                #We'll want to refuse any actions and get to the end of the Adventurer's current move-action cycle in order to reset
                self.undone = True
                return False
            self.respond_menu_choices(adventurer, player_input)
            #Redraw everything in case the adventurer of focus was changed
            #make sure that tiles and token positions are up to date
            game_vis.draw_play_area()
            game_vis.draw_routes()
            game_vis.draw_tile_piles()
            game_vis.draw_discard_pile()
            game_vis.draw_undo_button()
            game_vis.draw_move_options(actions)
            game_vis.draw_tokens() #draw tokens on top of highlights
            game_vis.give_prompt(prompt)
            # Draw the left menu items
            game_vis.draw_scores()
            if isinstance(adventurer, AdventurerAdvanced):
                game_vis.draw_cards()
            # Draw the right menu items
            game_vis.draw_move_count()
            game_vis.draw_toggle_menu(self.auto_actions)
            game_vis.draw_routes_menu()
            if isinstance(adventurer, AdventurerRegular):
                adventurer.match_chest_directions()
                game_vis.draw_chest_tiles()

            #Seek input again
            player_input = game_vis.get_input_coords(adventurer)
        if player_input.get(action_type) is not None:
            action_coords = player_input.get(action_type)
            print(self.name.capitalize()+" chose the coordinates of the tile where their Adventurer can "+action_type)
            action_location = adventurer.game.play_area[action_coords[0]][action_coords[1]]
        elif player_input.get("move") is not None: # If there were movement options, then check whether these were chosen
            move_coords = player_input.get("move")
            self.fast_forward = True
            self.queued_move = move_map[move_coords[0]].get(move_coords[1])
            action_location = None
            #If a move was chosen instead of an Action during route-following, then this means departing from the route
            self.follow_route = []
            self.destination = None
#            longitude = game.play_area.get(move_coords[0])
#            if longitude is not None:
#                tile = longitude.get(move_coords[1])
#                if tile is not None and tile not in self.follow_route:
#                    #This was a successful departure from the route
#                    self.follow_route = []
#                    self.destination = None
        else:
            print(self.name.capitalize()+" chose coordinates away from the tile where their Adventurer can "+action_type)
            action_location = None

        #clean up the highlights
        game_vis.clear_prompt()
        game_vis.clear_move_options()
#             game_vis.draw_tokens()
        return action_location
        
    #if offered by a Wonder, always trade
    def check_trade(self, adventurer, tile):
        if self.undone:
            return False
        return True
    
    #if offered by an agent, always collect wealth
    #@TODO let the player choose how much wealth to collect using input()
    def check_collect_wealth(self, agent):
        if self.undone: 
            print("automatically responding false to action")
            return False
        return True
    
    def check_rest(self, adventurer, token):
        if self.undone: 
            print("automatically responding false to action")
            return False
        game  = adventurer.game
        actions = {}
        if isinstance(token, Agent):
            token_description = " the Inn "
        elif isinstance(token, AdventurerAdvanced):
            token_description = token.player.name.capitalize()+"'s Adventurer #"+str(game.adventurers[token.player].index(token)+1)+" "
        else:
            print("Skipping asking player about rest because the token offered can't provide it.")
            return False
        if token.player == self:
            action_type = "rest"
            actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]
            prompt = ("If you want "+str(self.name)+"'s Adventurer #" 
                                           +str(game.adventurers[self].index(adventurer)+1) 
                                           +" to rest with "+token_description+" then click their tile, otherwise click elsewhere.")
        elif isinstance(adventurer, AdventurerAdvanced) and adventurer.num_free_rests > 0:
            action_type = "rest"
            actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                                        , adventurer.current_tile.tile_position.latitude]]
            prompt = ("If you want " + str(self.name) + "'s Adventurer #"
                      + str(game.adventurers[self].index(adventurer) + 1)
                      + " to rest with " + token_description + " then click their tile, otherwise click elsewhere.")
        else:
            action_type = "buy_rest"
            actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]
            prompt = ("If you want "+str(self.name)+"'s Adventurer #" 
                                           +str(game.adventurers[self].index(adventurer)+1) 
                                           +" to rest with "+token_description+" for "
                                           +str(game.cost_agent_rest)+
                                           " Silk then click their tile, otherwise click elsewhere.")
        #Check whether the player wants to go ahead
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
        
    #if offered by a city, then give the player the option to pay and refresh their chest maps
    def check_buy_maps(self, adventurer, report="Player is being asked whether to pay to refresh their chest maps"):
        print(report)
        if self.undone: 
            print("automatically responding false to action")
            return False
        # self.clear_auto_actions() #Make sure that auto-actions to buy doesn't apply
        actions = {}
        action_type = "buy"
        actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]
        prompt = ("If you want your Adventurer to buy a new set of maps for "
                             +str(adventurer.game.cost_refresh_maps)
                             +" then click their tile, otherwise click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
    
    #if offered by a city, then give the player the option to buy a discovery card 
    def check_buy_tech(self, adventurer, report="Player is being asked whether to buy a Discovery card"):
        print(report)
        if self.undone: 
            print("automatically responding false to action")
            return False
        # self.clear_auto_actions() #Make sure that auto-actions to buy doesn't apply
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
        if self.undone: 
            print("automatically responding false to action")
            return False
        # self.clear_auto_actions() #Make sure that auto-actions to buy doesn't apply
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
        if self.undone: 
            print("automatically responding false to action")
            return False
        # self.clear_auto_actions() #Make sure that auto-actions to buy doesn't apply
        action_type = "buy"
        actions[action_type] = [[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]
        prompt = ("If you want your Adventurer to base an Inn on this tile for "+str(adventurer.cost_agent_exploring)
                        +" Silk then click it, otherwise click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
        
    # When offered, give the player the option to buy on any tile that doesn't have an active Agent 
    def check_buy_agent(self, adventurer, report="Player has been offered to buy an Inn by a city"):
        print(report)
        if self.undone: 
            print("automatically responding false to action")
            return False
        # self.clear_auto_actions() #Make sure that auto-actions to buy doesn't apply
        actions = {}
        action_type = "buy"
        #Establish a list of all tiles without an active Agent, to offer the player
        actions[action_type] = []
        prompt = ("Click any unoccupied tile to buy rights and base an Inn there for "
                             +str(adventurer.game.cost_agent_from_city) 
                             +" Silk, otherwise click elsewhere.")
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
        if self.undone: 
            print("automatically responding false to action")
            return None
        action_type = "move_agent"
        actions = {action_type:[]}
        for agent in adventurer.game.agents[self]:
            actions[action_type].append([agent.current_tile.tile_position.longitude, agent.current_tile.tile_position.latitude])
        prompt = ("You will need to move an existing Inn of " +str(self.name)+ ", click to choose one"
                                       +", otherwise click elsewhere to cancel buying an Inn.")
        selected_tile = self.check_action(adventurer, action_type, actions, prompt)
        if selected_tile is not None:
            return selected_tile.agent
        else:
            return None
    
    def check_transfer_agent(self, adventurer):
        if self.undone: 
            print("automatically responding false to action")
            return None
        action_type = "agent_transfer"
        actions = {action_type:[]}
        for agent in adventurer.game.agents[self]:
            if not agent.current_tile == adventurer.current_tile: #Avoid trying to transfer Silk to the current tile
                actions[action_type].append([agent.current_tile.tile_position.longitude, agent.current_tile.tile_position.latitude])
        prompt = ("Select an Inn If you want " +str(self.name)+ "'s Adventurer to move Silk there "
                                       +", otherwise click elsewhere.")
        selected_tile = self.check_action(adventurer, action_type, actions, prompt)
        if selected_tile is not None:
            return selected_tile.agent
        else:
            return None
    
    #Give the player the choice to attack
    #@TODO highlight specific tokens to attack
    def check_attack_adventurer(self, adventurer, other_adventurer):
        if self.undone: 
            print("automatically responding false to action")
            return False
        action_type = "attack"
        actions = {action_type:[[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]}
        prompt = ("If you want "+str(self.name)+"'s Adventurer #" 
                           +str(adventurer.game.adventurers[self].index(adventurer)+1) 
                           +" to attack "+ other_adventurer.player.name+"'s Adventurer, then click their tile. "
                                      +" Otherwise, click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
    
    #if offered by a city then always bank everything
    def check_deposit(self, adventurer, maximum, minimum=0, default=0, report="Player is being asked whether to bank Silk"):
        print(report)
        if self.undone: 
            print("automatically responding false to action")
            return 0
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #Protect in case of inversions
        if minimum > maximum:
            old_max = maximum
            maximum = minimum
            minimum = old_max
        
        if isinstance(adventurer.current_tile, CityTile): #As there is a separate check to withdraw Silk before a turn, assume they will always bank everything
            return adventurer.wealth
        else:
            deposit_amount = game_vis.get_input_value(adventurer, "How much Silk will your Adventurer move to this Inn, from "+str(minimum)+" to "+str(maximum)+"?", maximum, minimum)
            if deposit_amount is not None:
                return deposit_amount
            else:
                return default
    
    def check_travel_money(self, adventurer, maximum, default):
        '''Lets the player input a figure for the wealth that will be taken from the Vault before an expedition
        '''
        if self.undone: 
            print("automatically responding false to action")
            return 0
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #Ask the visual for an amount, so that it can either prompt the player or default
        travel_money = game_vis.get_input_value(adventurer, "How much Silk will your Adventurer take with them, up to "+str(maximum)+"?", maximum)
        if travel_money in range(0, maximum+1):
            return travel_money
        else:
            return default
    
    #prompt the player on victory for how much wealth to take using input()
    def check_steal_amount(self, adventurer, maximum, default):
        if self.undone: 
            print("automatically responding false to action")
            return 0
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #Ask the visual for an amount, so that it can either prompt the player or default
        steal_amount = game_vis.get_input_value(adventurer, "Your Adventurer's piracy succeeded. How much Silk will they take, up to "+str(maximum)+"?", maximum)
        if steal_amount in range(0, maximum+1):
            return steal_amount
        else:
            return default
    
    #@TODO prompt the player on victory for how much wealth to take 
    def check_attack_agent(self, adventurer, agent):
        if self.undone: 
            print("automatically responding false to action")
            return False
        action_type = "attack"
        actions = {action_type:[[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]}
        prompt = ("If you want "+str(self.name)+"'s Adventurer #" 
                           +str(adventurer.game.adventurers[self].index(adventurer)+1) 
                           +" to attack "+ agent.player.name+"'s player's Inn, then click their tile. "
                                      +" Otherwise, click elsewhere.")    
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
    
    # Always restor own Agents if it can be afforded
    def check_restore_agent(self, adventurer, agent):
        if self.undone: 
            print("automatically responding false to action")
            return False
        action_type = "buy"
        actions = {action_type:[[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]}
        prompt = ("If you want your Adventurer to restore your ransacked Inn on this tile for "+str(adventurer.game.cost_agent_restore)
                        +" then click it, otherwise click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
        
    # if half Disaster tile dropped wealth exceeds own wealth then try to collect it
    def check_court_disaster(self, adventurer, disaster_tile):
        if self.undone: 
            print("automatically responding false to action")
            return False
        action_type = "attack"
        actions = {action_type:[[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]}
        prompt = ("If you want your pirate Adventurer to try and recover "+str(disaster_tile.dropped_wealth // 2)
                        +" from the tile then click it, otherwise click elsewhere.")
        if self.check_action(adventurer, action_type, actions, prompt):
            return True
        else:
            return False
        
    def choose_card(self, adventurer, cards):
        '''Responds to option from the game to pick from a list of cards, based on player input
        '''
        card_variety = cards[0].card_type[:3]
        if card_variety == "adv":
            prompt = "Select a Character card for "+self.name+"'s Adventurer #"+str(adventurer.game.adventurers[self].index(adventurer) + 1)
        elif card_variety == "dis":
            prompt = "Select a Manuscript card for "+self.name+"'s Adventurer #"+str(adventurer.game.adventurers[self].index(adventurer) + 1)
        elif card_variety == "com":
            prompt = "Select a Cadre card for "+self.name
        else:
            prompt = "Select a card for "+self.name+"'s Adventurer #"+str(adventurer.game.adventurers[self].index(adventurer) + 1)
        
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #make sure that tiles and token positions are up to date
        game_vis.draw_play_area()
        game_vis.draw_routes()
        game_vis.draw_tokens()
        game_vis.draw_scores()
        game_vis.draw_move_count()
        if isinstance(adventurer, AdventurerRegular) and card_variety not in ["com", "adv"]:
            game_vis.draw_chest_tiles()
        if isinstance(adventurer, AdventurerAdvanced):
            game_vis.draw_cards()
        
        #prompt the player to input
        print("Prompting "+self.name+" for input")
#            game_vis.clear_prompt()
        game_vis.give_prompt(prompt)
        game_vis.draw_card_offers(cards)
        card = cards[game_vis.get_input_choice(adventurer, cards)]

        #clean up the highlights
        game_vis.clear_prompt()
        return card
    
    def choose_tile(self, adventurer, tiles):
        '''Responds to option from the game to pick from a list of tiles, based on player input
        '''
        prompt = "Select a tile for "+self.name+"'s Adventurer #"+str(adventurer.game.adventurers[self].index(adventurer) + 1)
        
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #make sure that tiles and token positions are up to date
        game_vis.draw_play_area()
        game_vis.draw_routes()
        game_vis.draw_tokens()
        game_vis.draw_scores()
        game_vis.draw_move_count()
        if isinstance(adventurer, AdventurerRegular):
            game_vis.draw_chest_tiles()
        if isinstance(adventurer, AdventurerAdvanced):
            game_vis.draw_cards()
        
        #prompt the player to input
        print("Prompting "+self.name+" for input")
#            game_vis.clear_prompt()
        game_vis.give_prompt(prompt)
        game_vis.draw_tile_offers(tiles)
        tile = tiles[game_vis.get_input_choice(adventurer, tiles, "tile")]

        #clean up the highlights
        game_vis.clear_prompt()
        return tile
