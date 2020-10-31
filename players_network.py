from base import Player
from matplotlib import pyplot
from game import GameRegular

class PlayerHuman(Player): # do you need to give this access to the visualisation?
    # from ipywidgets import widgets # bring in widgets to receive player input
    
    def __init__(self, colour, play_area_vis):
        super().__init__(colour)
        
        self.play_area_vis = play_area_vis
        
        self.attack_history = []
    
    def get_coords_from_figure(self, adventurer):
        '''Collects mouseclick input from the user and converts it into the position of a game tile.
        
        Arguments
        adventurer takes a Cartolan.Adventurer
        '''
        pyplot.ginput(timeout=0) # this call to ginput should reveal the highlights, but will it also be the one that determines movement
        self.play_area_vis.clear_prompt()
        self.play_area_vis.give_prompt("Click again to confirm")
        move_click = pyplot.ginput(timeout=0)
#         pyplot.show(block=False)
        if not move_click:
            print(self.colour+" player failed to choose a move, so it is assumed the Adventurer will wait in place")
            move_coords = [adventurer.current_tile.tile_position.longitude, adventurer.current_tile.tile_position.latitude]
        else:
            move_coords = [int(move_click[0][0]) - self.play_area_vis.origin[0], int(move_click[0][1]) - self.play_area_vis.origin[1]]
#                 move_coords = [int(move_click[0][0] * play_area_vis.dimensions[0]) - play_area_vis.origin[0]
#                                , int(move_click[0][1] * play_area_vis.dimensions[1]) - play_area_vis.origin[0]]
        
        return move_coords
    
    
    def continue_move(self, adventurer):
        '''Offers the user available moves, translates their mouse input into movement, and updates visuals.
        
        Arguments
        adventurer takes a Cartolan.Adventurer
        '''
        valid_moves = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]
        chance_moves = []
        invalid_moves = []
        move_map = {adventurer.current_tile.tile_position.longitude:{adventurer.current_tile.tile_position.latitude:'wait'}}
        
        #prompt the player to choose a tile to move on to
        print("Prompting the "+self.colour+" player for input")
        self.play_area_vis.clear_prompt()
        self.play_area_vis.give_prompt("Double click which tile you would like "+str(self.colour)+" adventurer #" 
                                       +str(self.adventurers.index(adventurer)+1) 
                                       +" to move to?")
        
        #highlight the tiles that can be reached this move
        for compass_point in ['n', 'e', 's', 'w']:
            #locate the space in the play area that the Adventurer is moving into
            longitude_increment = int(compass_point.lower() in ["east","e"]) - int(compass_point.lower() in ["west","w"])
            potential_longitude = adventurer.current_tile.tile_position.longitude + longitude_increment
            latitude_increment = int(compass_point.lower() in ["north","n"]) - int(compass_point.lower() in ["south","s"])
            potential_latitude = adventurer.current_tile.tile_position.latitude + latitude_increment
            can_move = adventurer.can_move(compass_point)
            if can_move:
                valid_moves.append([potential_longitude, potential_latitude])
            elif can_move is None:
                chance_moves.append([potential_longitude, potential_latitude])
            else:
                invalid_moves.append([potential_longitude, potential_latitude])
            #keep track of what compass point these coordinates correspond to
            if move_map.get(potential_longitude):
                move_map[potential_longitude][potential_latitude] = compass_point
            else:
                move_map[potential_longitude] = {potential_latitude:compass_point}
        
        #highlight the tiles
        print("Highlighting the available moves for the "+self.colour+" player's Adventurer #"+str(self.adventurers.index(adventurer)+1))
        self.play_area_vis.draw_move_options(valid_moves, invalid_moves, chance_coords=chance_moves)
        
        #Carry out the player's chosen move
        move_coords = self.get_coords_from_figure(adventurer)
        if move_coords in valid_moves or move_coords in chance_moves:
            print(self.colour+" player chose valid coordinates to move to.")
            if move_map[move_coords[0]].get(move_coords[1]) == "wait":
                self.play_area_vis.clear_move_options()
                moved = adventurer.wait()
                print("moved = "+str(moved))
            else:
                self.play_area_vis.clear_move_options()
                moved = adventurer.move(move_map[move_coords[0]].get(move_coords[1]))
                #check whether the turn is over despite movement failing, e.g. it failed because exploration failed
                if adventurer.turns_moved == adventurer.game.turn:
                    moved = True
        else:
            self.play_area_vis.clear_prompt()
            self.play_area_vis.give_prompt("This is not a valid move, so waiting in place. Double click to continue.")
            self.play_area_vis.clear_move_options()
            self.get_coords_from_figure(adventurer)
            adventurer.wait()
                
#         self.play_area_vis.give_prompt("Click to reveal available moves")
        #if the tile that has just been reached is at the edge of the visualised area, then grow this
        current_tile_position = adventurer.current_tile.tile_position
        if current_tile_position.longitude + 1 >= self.play_area_vis.dimensions[0] - self.play_area_vis.origin[0]:
            self.play_area_vis.give_prompt("Expanding visible play area, please wait.")
            self.play_area_vis.increase_max_longitude()
            self.play_area_vis.draw_play_area(adventurer.game.play_area)
        elif current_tile_position.longitude <= - self.play_area_vis.origin[0]:
            self.play_area_vis.give_prompt("Expanding visible play area, please wait.")
            self.play_area_vis.decrease_min_longitude()
            self.play_area_vis.draw_play_area(adventurer.game.play_area)
        elif current_tile_position.latitude + 1 >= self.play_area_vis.dimensions[1] - self.play_area_vis.origin[1]:
            self.play_area_vis.give_prompt("Expanding visible play area, please wait.")
            self.play_area_vis.increase_max_latitude()
            self.play_area_vis.draw_play_area(adventurer.game.play_area)
        elif current_tile_position.latitude <= - self.play_area_vis.origin[1]:
            self.play_area_vis.give_prompt("Expanding visible play area, please wait.")
            self.play_area_vis.decrease_min_latitude() 
            self.play_area_vis.draw_play_area(adventurer.game.play_area)
        else: #add in the tiles that have not been visualised so far, which should only ever be the current tile of the adventurer    
            self.play_area_vis.draw_play_area(adventurer.game.play_area)
        
        #clean up the highlights
        self.play_area_vis.clear_move_options()
        #redraw all the tokens and scores
        self.play_area_vis.draw_routes(adventurer.game.players)
        self.play_area_vis.draw_tokens(adventurer.game.players)
        return True
    
    def continue_turn(self, adventurer):
        '''Iteratively allows the players to move.
        
        Arguments
        adventurer is a Cartolan.Adventurer
        '''
        #Clear the previously drawn route for this adventurer, before drawing a new one
        adventurer.route = [adventurer.current_tile]
        #Update the play area after other player's movements, such as virtual players
        self.play_area_vis.draw_play_area(adventurer.game.play_area)
        self.play_area_vis.draw_routes(adventurer.game.players)
        self.play_area_vis.draw_tokens(adventurer.game.players)
        #Have the player acknowledge that it is their turn
        self.play_area_vis.clear_prompt()
        self.play_area_vis.give_prompt(self.colour+" player's turn for Adventurer #"+str(self.adventurers.index(adventurer)+1)+". Double click to continue.")
        self.play_area_vis.draw_move_options()
        self.get_coords_from_figure(adventurer)
        
        #Move while moves are still available
        while adventurer.turns_moved < adventurer.game.turn:
            print(self.colour+" player's Adventurer #"+str(self.adventurers.index(adventurer)+1)+" is still able to move.")
            self.continue_move(adventurer)
        
        #If this is not the last adventurer for the player then finish here, otherwise clear the routes for all the non-human players that will play between this and the next human player
        if self.adventurers.index(adventurer) < len(self.adventurers) - 1:
            return True
        
        #we'll need to clear routes up to either the next human player after this one in the play order...
        players = adventurer.game.players
        for player_index in range(players.index(self)+1, len(players)):
            if isinstance(players[player_index], PlayerHuman):
                return True
            for adventurer in players[player_index].adventurers:
                adventurer.route = [adventurer.current_tile]
        #...or if this was the last human player then we clear up to the first human in the play order
        for player in players:
            if isinstance(player, PlayerHuman):
                return True
            for adventurer in player.adventurers:
                adventurer.route = [adventurer.current_tile]
        
        return True
    
    #if offered by a Wonder, always trade
    def check_trade(self, adventurer, tile):
        return True
    
    #if offered by an agent, always collect wealth
    def check_collect_wealth(self, agent):
        return True
    
    #if offered always rest at own agents, give the player a choice about resting at others
    def check_rest(self, adventurer, agent):
        if agent.player == self:
            return True
        else:
            buy_coords = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]

            #make sure that tiles and token positions are up to date
            self.play_area_vis.draw_tokens(adventurer.game.players)
            
            #highlight the tile where rest can be bought
            print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(self.adventurers.index(adventurer)+1)+" can rest")
            self.play_area_vis.draw_move_options(buy_coords=buy_coords)

            #prompt the player to choose a tile to move on to
            print("Prompting the "+self.colour+" player for input")
            self.play_area_vis.clear_prompt()
            self.play_area_vis.give_prompt("If you want "+str(self.colour)+" adventurer #" 
                                           +str(self.adventurers.index(adventurer)+1) 
                                           +" to rest then double click their tile, otherwise double click elsewhere.")
            
            rest = False
            move_coords = self.get_coords_from_figure(adventurer)
            if move_coords in buy_coords:
                print(self.colour+" player chose the coordinates of the tile where their Adventurer can rest.")
                rest = True
            else:
                print(self.colour+" player chose coordinates away from the tile where their Adventurer can rest.")
                rest = False

            #clean up the highlights
            self.play_area_vis.clear_move_options()
#             self.play_area_vis.draw_tokens(adventurer.game.players)
            return rest
        
    
    #if offered by a city then always bank everything
    def check_bank_wealth(self, adventurer, report="Player is being asked whether to bank wealth"):
        print(report)
        return adventurer.wealth
    
    #if offered by a city, then give the player the option to buy an Adventurer 
    def check_buy_adventurer(self, adventurer, report="Player is being asked whether to buy an Adventurer"):
        print(report)
        if self.vault_wealth >= adventurer.game.COST_ADVENTURER:
            buy_coords = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]

            #make sure that tiles and token positions are up to date
            self.play_area_vis.draw_tokens(adventurer.game.players)
            
            #highlight the city tile where an adventurer can be bought
            print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(self.adventurers.index(adventurer)+1)
                  +" can recruit another adventurer")
            self.play_area_vis.draw_move_options(buy_coords=buy_coords)

            #prompt the player to input
            print("Prompting the "+self.colour+" player for input")
            self.play_area_vis.clear_prompt()
            self.play_area_vis.give_prompt("If you want "+str(self.colour)+" Adventurer #" 
                               +str(self.adventurers.index(adventurer)+1) 
                               +" to recruit another Adventurer then double click their tile, otherwise double click elsewhere.")
            
            recruit = False
            move_coords = self.get_coords_from_figure(adventurer)
            if move_coords in buy_coords:
                print(self.colour+" player chose the coordinates of the tile where their Adventurer can recruit.")
                recruit = True
            else:
                print(self.colour+" player chose coordinates away from the tile where their Adventurer can recruit.")
                recruit = False

            #clean up the highlights
            self.play_area_vis.clear_move_options()
#             self.play_area_vis.draw_tokens(adventurer.game.players)
            return recruit
        else:
            return False
    
    # Let the player choose whether to place an agent when offered
    def check_place_agent(self, adventurer):
        if adventurer.wealth >= adventurer.game.COST_AGENT_EXPLORING:
            buy_coords = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]

            #make sure that tiles and token positions are up to date
            # current_tile_position = adventurer.current_tile.tile_position
            # new_play_area = {current_tile_position.longitude:{current_tile_position.latitude:adventurer.current_tile}}
#             self.play_area_vis.draw_play_area(adventurer.game.play_area, new_play_area)
            self.play_area_vis.draw_play_area(adventurer.game.play_area)
            self.play_area_vis.draw_tokens(adventurer.game.players)
            
            #highlight the tile where the agent can be placed
            print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(self.adventurers.index(adventurer)+1)
                  +" can recruit an Agent")
            self.play_area_vis.draw_move_options(buy_coords=buy_coords)

            #prompt the player to input
            print("Prompting the "+self.colour+" player for input")
            self.play_area_vis.clear_prompt()
            self.play_area_vis.give_prompt("If you want "+str(self.colour)+" Adventurer #" 
                               +str(self.adventurers.index(adventurer)+1) 
                               +" to recruit an Agent on this tile then double click it, otherwise double click elsewhere.")
            
            recruit = False
            move_coords = self.get_coords_from_figure(adventurer)
            if move_coords in buy_coords:
                print(self.colour+" player chose the coordinates of the tile where their Adventurer can recruit.")
                recruit = True
            else:
                print(self.colour+" player chose coordinates away from the tile where their Adventurer can recruit.")
                recruit = False

            #clean up the highlights
            self.play_area_vis.clear_move_options()
#             self.play_area_vis.draw_tokens(adventurer.game.players)
            return recruit
        else:
            return False
    
    # When offered, give the player the option to buy on any tile that doesn't have an active Agent 
    def check_buy_agent(self, adventurer, report="Player has been offered to buy an agent by a city"):
        print(report)
        if self.vault_wealth >= adventurer.game.COST_AGENT_FROM_CITY:
            #Establish a list of all tiles without an active Agent, to offer the player
            buy_coords = []
            play_area = adventurer.game.play_area
            for longitude in play_area:
                for latitude in play_area[longitude]:
                    #Check that this lat and latitude are outside any city's domain
                    outside_city_domains = True
                    for city_tile in adventurer.game.cities:
                        city_longitude = city_tile.tile_position.longitude
                        city_latitude = city_tile.tile_position.latitude
                        if abs(longitude - city_longitude)+abs(latitude - city_latitude) <= adventurer.game.CITY_DOMAIN_RADIUS:
                            outside_city_domains = False
                    #If outside all cities' domains then this is a valid location to place an agent
                    if outside_city_domains:
                        tile = play_area[longitude][latitude] 
                        if tile.agent is None:
                            buy_coords.append([tile.tile_position.longitude, tile.tile_position.latitude])
                        elif isinstance(adventurer.game, GameRegular):
                            if tile.agent.is_dispossessed:
                                buy_coords.append([tile.tile_position.longitude, tile.tile_position.latitude])
            
            #make sure that tiles and token positions are up to date
            self.play_area_vis.draw_tokens(adventurer.game.players)
            
            #highlight the tiles where an Agent could be placed 
            print("Highlighting the tile where "+self.colour+" player can send an Agent")
            self.play_area_vis.draw_move_options(buy_coords=buy_coords)

            #prompt the player to input
            print("Prompting the "+self.colour+" player for input")
            self.play_area_vis.clear_prompt()
            self.play_area_vis.give_prompt("If you want to recruit an Agent and send them to"
                                           +"an unoccupied tile then double click it, otherwise double click elsewhere.")
            
            agent_placement = None
            move_coords = self.get_coords_from_figure(adventurer)
            if move_coords in buy_coords:
                print(self.colour+" player chose a tile where thay can send an agent.")
                agent_placement = adventurer.game.play_area[move_coords[0]][move_coords[1]]
            else:
                print(self.colour+" player chose coordinates where they can't recruit.")
                agent_placement = None

            #clean up the highlights
            self.play_area_vis.clear_move_options()
#             self.play_area_vis.draw_tokens(adventurer.game.players)
            return agent_placement
        else:
            return None
    
    # never move an agent when offered
    def check_move_agent(self, adventurer):     
        agent_coords = []
        for agent in self.agents:
            agent_coords.append([agent.current_tile.tile_position.longitude, agent.current_tile.tile_position.latitude])

        #make sure that tiles and token positions are up to date
        self.play_area_vis.draw_tokens(adventurer.game.players)

        #highlight the tile where the agent might be moved from
        print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(self.adventurers.index(adventurer)+1)
              +" can recruit an Agent")
        self.play_area_vis.draw_move_options(valid_coords=agent_coords)

        #prompt the player to input
        print("Prompting the "+self.colour+" player for input")
        self.play_area_vis.clear_prompt()
        self.play_area_vis.give_prompt("You will need to move an existing " +str(self.colour)+ " Agent, double click to choose one"
                                       +", otherwise double click elsewhere to cancel buying an Agent.")

        agent_to_move = None
        move_coords = self.get_coords_from_figure(adventurer)
        if move_coords in agent_coords:
            print(self.colour+" player chose the coordinates of the tile where their Agent can move from.")
            agent_to_move = adventurer.game.play_area[move_coords[0]][move_coords[1]].agent
        else:
            print(self.colour+" player chose coordinates away from the tile where their Agent can move from.")
            agent_to_move = None

        #clean up the highlights
        self.play_area_vis.clear_move_options()
        return agent_to_move
    
    #Give the player the choice to attack
    #@TODO highlight specific tokens to attack
    def check_attack_adventurer(self, adventurer, other_adventurer):
        attack_coords = [[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]

        #make sure that tiles and token positions are up to date
        self.play_area_vis.draw_tokens(adventurer.game.players)
            
        #highlight the tile where the opposing Adventurer can be attacked
        print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(self.adventurers.index(adventurer)+1)
              +" can attack "+ other_adventurer.player.colour+" player's Adventurer")
        self.play_area_vis.draw_move_options(attack_coords=attack_coords)

        #prompt the player to input
        print("Prompting the "+self.colour+" player for input")
        self.play_area_vis.clear_prompt()
        self.play_area_vis.give_prompt("If you want "+str(self.colour)+" Adventurer #" 
                           +str(self.adventurers.index(adventurer)+1) 
                           +" to attack "+ other_adventurer.player.colour+" player's Adventurer, then double click their tile. "
                                      +" Otherwise, double click elsewhere.")

        attack = False
        move_coords = self.get_coords_from_figure(adventurer)
        if move_coords in attack_coords:
            print(self.colour+" player chose the coordinates of the tile where their Adventurer can attack.")
            attack = True
        else:
            print(self.colour+" player chose coordinates away from the tile where their Adventurer can attack.")
            attack = False

        #clean up the highlights
        self.play_area_vis.clear_move_options()
#             self.play_area_vis.draw_tokens(adventurer.game.players)
        return attack
    
    def check_attack_agent(self, adventurer, agent):
        attack_coords = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]

        #make sure that tiles and token positions are up to date
        self.play_area_vis.draw_tokens(adventurer.game.players)
            
        #highlight the tile where the opposing Agent can be attacked
        print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(self.adventurers.index(adventurer)+1)
              +" can attack "+ agent.player.colour+" player's Adventurer")
        self.play_area_vis.draw_move_options(attack_coords=attack_coords)

        #prompt the player to input
        print("Prompting the "+self.colour+" player for input")
        self.play_area_vis.clear_prompt()
        self.play_area_vis.give_prompt("If you want "+str(self.colour)+" Adventurer #" 
                           +str(self.adventurers.index(adventurer)+1) 
                           +" to attack "+ agent.player.colour+" player's Agent, then double click their tile. "
                                      +" Otherwise, double click elsewhere.")

        attack = False
        move_coords = self.get_coords_from_figure(adventurer)
        if move_coords in attack_coords:
            print(self.colour+" player chose the coordinates of the tile where their Adventurer can attack.")
            attack = True
        else:
            print(self.colour+" player chose coordinates away from the tile where their Adventurer can attack.")
            attack = False

        #clean up the highlights
        self.play_area_vis.clear_move_options()
#             self.play_area_vis.draw_tokens(adventurer.game.players)
        return attack
    
    # Always restor own Agents if it can be afforded
    def check_restore_agent(self, adventurer, agent):
        if agent.player == adventurer.player and adventurer.wealth >= adventurer.game.COST_AGENT_RESTORE:
            return True
        else:
            return False