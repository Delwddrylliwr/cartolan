from base import Player
from game import GameRegular

class PlayerHuman(Player):
    '''A pyplot-based interface for a human players to make decisions in live play.
    '''
    def __init__(self, colour):
        super().__init__(colour)
        self.attack_history = []
    
    def continue_move(self, adventurer):
        '''Offers the user available moves, translates their mouse input into movement, and updates visuals.
        
        Arguments
        adventurer takes a Cartolan.Adventurer
        '''
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        valid_moves = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]
        chance_moves = []
        invalid_moves = []
        move_map = {adventurer.current_tile.tile_position.longitude:{adventurer.current_tile.tile_position.latitude:'wait'}}
        
        #redraw all the tokens and scores
        game_vis.draw_play_area()
        game_vis.draw_routes()
        game_vis.draw_tokens()
        game_vis.draw_scores()
        #prompt the player to choose a tile to move on to
        print("Prompting the "+self.colour+" player for input")
#        game_vis.clear_prompt()
        game_vis.give_prompt("click which tile you would like "+str(self.colour)+" adventurer #" 
                                       +str(game.adventurers[self].index(adventurer)+1) 
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
        print("Highlighting the available moves for the "+self.colour+" player's Adventurer #"+str(game.adventurers[self].index(adventurer)+1))
        game_vis.draw_move_options(valid_moves, invalid_moves, chance_coords=chance_moves)
        
        #Carry out the player's chosen move
        move_coords = game_vis.get_input_coords(adventurer)
        while move_coords not in valid_moves:
            move_coords = game_vis.get_input_coords(adventurer)
        if move_coords in valid_moves or move_coords in chance_moves:
            print(self.colour+" player chose valid coordinates to move to.")
            if move_map[move_coords[0]].get(move_coords[1]) == "wait":
                game_vis.clear_move_options()
                moved = adventurer.wait()
                print("moved = "+str(moved))
            else:
                game_vis.clear_move_options()
                moved = adventurer.move(move_map[move_coords[0]].get(move_coords[1]))
                #check whether the turn is over despite movement failing, e.g. it failed because exploration failed
                if adventurer.turns_moved == adventurer.game.turn:
                    moved = True
        else:
            game_vis.clear_prompt()
            game_vis.give_prompt("This is not a valid move, so waiting in place. click to continue.")
            game_vis.clear_move_options()
            game_vis.get_input_coords(adventurer)
            game_vis.clear_prompt()
            adventurer.wait()
                
#         game_vis.give_prompt("Click to reveal available moves")
        #if the tile that has just been reached is at the edge of the visualised area, then grow this
        current_tile_position = adventurer.current_tile.tile_position
        game_vis.clear_prompt()
        if current_tile_position.longitude + 1 >= game_vis.dimensions[0] - game_vis.origin[0]:
            game_vis.give_prompt("Expanding visible play area, please wait.")
            game_vis.increase_max_longitude()
            game_vis.draw_play_area()
        elif current_tile_position.longitude <= - game_vis.origin[0]:
            game_vis.give_prompt("Expanding visible play area, please wait.")
            game_vis.decrease_min_longitude()
            game_vis.draw_play_area()
        elif current_tile_position.latitude + 1 >= game_vis.dimensions[1] - game_vis.origin[1]:
            game_vis.give_prompt("Expanding visible play area, please wait.")
            game_vis.increase_max_latitude()
            game_vis.draw_play_area()
        elif current_tile_position.latitude <= - game_vis.origin[1]:
            game_vis.give_prompt("Expanding visible play area, please wait.")
            game_vis.decrease_min_latitude() 
            game_vis.draw_play_area()
        else: #add in the tiles that have not been visualised so far, which should only ever be the current tile of the adventurer    
            game_vis.draw_play_area()
        
        #clean up the highlights
        game_vis.clear_prompt()
        game_vis.clear_move_options()
#        #redraw all the tokens and scores
#        game_vis.draw_play_area()
#        game_vis.draw_routes()
#        game_vis.draw_tokens()
#        game_vis.draw_scores()
        return True
    
    def continue_turn(self, adventurer):
        '''Iteratively allows the players to move.
        
        Arguments
        adventurer is a Cartolan.Adventurer
        '''
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        adventurers = game.adventurers[self]
        #Clear the previously drawn route for this adventurer, before drawing a new one
        adventurer.route = [adventurer.current_tile]
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
        
        #we'll need to clear routes up to either the next human player after this one in the play order...
        players = game.players
        for player_index in range(players.index(self)+1, len(players)):
            if isinstance(players[player_index], PlayerHuman):
                return True
            for adventurer in game.adventurers[players[player_index]]:
                adventurer.route = [adventurer.current_tile]
        #...or if this was the last human player then we clear up to the first human in the play order
        for player in players:
            if isinstance(player, PlayerHuman):
                return True
            for adventurer in game.adventurers[player]:
                adventurer.route = [adventurer.current_tile]
        
        return True
    
    #if offered by a Wonder, always trade
    def check_trade(self, adventurer, tile):
        return True
    
    #if offered by an agent, always collect wealth
    #@TODO let the player choose how much wealth to collect using input()
    def check_collect_wealth(self, agent):
        return True
    
    #if offered always rest at own agents, give the player a choice about resting at others
    def check_rest(self, adventurer, agent):
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        #make sure that tiles and token positions are up to date
        game_vis.draw_play_area()
        game_vis.draw_tokens()
        game_vis.draw_scores()
        
        #highlight the tile where rest can be sought or bought
        print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(game.adventurers[self].index(adventurer)+1)+" can rest")
        if not agent in adventurer.agents_rested:
            if agent.player == self:
                valid_coords = [[adventurer.current_tile.tile_position.longitude
                            , adventurer.current_tile.tile_position.latitude]]
                game_vis.draw_move_options(rest_coords=valid_coords)
            elif adventurer.wealth >= adventurer.game.COST_AGENT_EXPLORING:
                valid_coords = [[adventurer.current_tile.tile_position.longitude
                            , adventurer.current_tile.tile_position.latitude]]
                game_vis.draw_move_options(buy_coords=valid_coords)
            else:
                return False
        else:
            return False

        #prompt the player to choose a tile to move on to
        print("Prompting the "+self.colour+" player for input")
#            game_vis.clear_prompt()
        game_vis.give_prompt("If you want "+str(self.colour)+" adventurer #" 
                                       +str(game.adventurers[self].index(adventurer)+1) 
                                       +" to rest then click their tile, otherwise click elsewhere.")
        
        rest = False
        move_coords = game_vis.get_input_coords(adventurer)
        if move_coords in valid_coords:
            print(self.colour+" player chose the coordinates of the tile where their Adventurer can rest.")
            rest = True
        else:
            print(self.colour+" player chose coordinates away from the tile where their Adventurer can rest.")
            rest = False

        #clean up the highlights
        game_vis.clear_prompt()
        game_vis.clear_move_options()
#             game_vis.draw_tokens()
        return rest
        
    
    #if offered by a city then always bank everything
    #@TODO allow player to specify how much wealth to bank using input() or a text box: https://stackoverflow.com/questions/46390231/how-to-create-a-text-input-box-with-pygame
    def check_bank_wealth(self, adventurer, report="Player is being asked whether to bank wealth"):
        print(report)
        return adventurer.wealth
    
    #if offered by a city, then give the player the option to buy an Adventurer 
    def check_buy_adventurer(self, adventurer, report="Player is being asked whether to buy an Adventurer"):
        print(report)
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        if self.vault_wealth >= adventurer.game.COST_ADVENTURER:
            buy_coords = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]

            #make sure that tiles and token positions are up to date
            game_vis.draw_play_area()
            game_vis.draw_tokens()
            game_vis.draw_scores()
            
            #highlight the city tile where an adventurer can be bought
            print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(game.adventurers[self].index(adventurer)+1)
                  +" can recruit another adventurer")
            game_vis.draw_move_options(buy_coords=buy_coords)

            #prompt the player to input
            print("Prompting the "+self.colour+" player for input")
#            game_vis.clear_prompt()
            game_vis.give_prompt("If you want "+str(self.colour)+" Adventurer #" 
                               +str(game.adventurers[self].index(adventurer)+1) 
                               +" to recruit another Adventurer then click their tile, otherwise click elsewhere.")
            
            recruit = False
            move_coords = game_vis.get_input_coords(adventurer)
            if move_coords in buy_coords:
                print(self.colour+" player chose the coordinates of the tile where their Adventurer can recruit.")
                recruit = True
            else:
                print(self.colour+" player chose coordinates away from the tile where their Adventurer can recruit.")
                recruit = False

            #clean up the highlights
            game_vis.clear_prompt()
            game_vis.clear_move_options()
#             game_vis.draw_tokens()
            return recruit
        else:
            return False
    
    # Let the player choose whether to place an agent when offered
    def check_place_agent(self, adventurer):
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        if adventurer.wealth >= adventurer.game.COST_AGENT_EXPLORING:
            buy_coords = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]

            #make sure that tiles and token positions are up to date
            # current_tile_position = adventurer.current_tile.tile_position
            # new_play_area = {current_tile_position.longitude:{current_tile_position.latitude:adventurer.current_tile}}
#             game_vis.draw_play_area(adventurer.game.play_area, new_play_area)
            game_vis.draw_play_area()
            game_vis.draw_tokens()
            game_vis.draw_scores()
            
            #highlight the tile where the agent can be placed
            print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(game.adventurers[self].index(adventurer)+1)
                  +" can recruit an Agent")
            game_vis.draw_move_options(buy_coords=buy_coords)

            #prompt the player to input
            print("Prompting the "+self.colour+" player for input")
#            game_vis.clear_prompt()
            game_vis.give_prompt("If you want "+str(self.colour)+" Adventurer #" 
                               +str(game.adventurers[self].index(adventurer)+1) 
                               +" to recruit an Agent on this tile then click it, otherwise click elsewhere.")
            
            recruit = False
            move_coords = game_vis.get_input_coords(adventurer)
            if move_coords in buy_coords:
                print(self.colour+" player chose the coordinates of the tile where their Adventurer can recruit.")
                recruit = True
            else:
                print(self.colour+" player chose coordinates away from the tile where their Adventurer can recruit.")
                recruit = False

            #clean up the highlights
            game_vis.clear_move_options()
            game_vis.clear_prompt()
#             game_vis.draw_tokens()
            return recruit
        else:
            return False
    
    # When offered, give the player the option to buy on any tile that doesn't have an active Agent 
    def check_buy_agent(self, adventurer, report="Player has been offered to buy an agent by a city"):
        print(report)
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        if self.vault_wealth >= adventurer.game.COST_AGENT_FROM_CITY:
            #Establish a list of all tiles without an active Agent, to offer the player
            buy_coords = []
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
                        buy_coords.append([tile.tile_position.longitude, tile.tile_position.latitude])
                    elif isinstance(adventurer.game, GameRegular):
                        if tile.agent.is_dispossessed:
                            buy_coords.append([tile.tile_position.longitude, tile.tile_position.latitude])
            
            #make sure that tiles and token positions are up to date
            game_vis.draw_play_area()
            game_vis.draw_tokens()
            game_vis.draw_scores()
            
            #highlight the tiles where an Agent could be placed 
            print("Highlighting the tile where "+self.colour+" player can send an Agent")
            game_vis.draw_move_options(buy_coords=buy_coords)

            #prompt the player to input
            print("Prompting the "+self.colour+" player for input")
#            game_vis.clear_prompt()
            game_vis.give_prompt("If you want to recruit an Agent and send them to"
                                           +"an unoccupied tile then click it, otherwise click elsewhere.")
            
            agent_placement = None
            move_coords = game_vis.get_input_coords(adventurer)
            if move_coords in buy_coords:
                print(self.colour+" player chose a tile where thay can send an agent.")
                agent_placement = adventurer.game.play_area[move_coords[0]][move_coords[1]]
            else:
                print(self.colour+" player chose coordinates where they can't recruit.")
                agent_placement = None

            #clean up the highlights
            game_vis.clear_move_options()
            game_vis.clear_prompt()
#             game_vis.draw_tokens()
            return agent_placement
        else:
            return None
    
    # never move an agent when offered
    def check_move_agent(self, adventurer):     
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        
        agent_coords = []
        for agent in game.agents[self]:
            agent_coords.append([agent.current_tile.tile_position.longitude, agent.current_tile.tile_position.latitude])

        #make sure that tiles and token positions are up to date
        game_vis.draw_play_area()
        game_vis.draw_tokens()
        game_vis.draw_scores()

        #highlight the tile where the agent might be moved from
        print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(game.adventurers[self].index(adventurer)+1)
              +" can recruit an Agent")
        game_vis.draw_move_options(valid_coords=agent_coords)

        #prompt the player to input
        print("Prompting the "+self.colour+" player for input")
#        game_vis.clear_prompt()
        game_vis.give_prompt("You will need to move an existing " +str(self.colour)+ " Agent, click to choose one"
                                       +", otherwise click elsewhere to cancel buying an Agent.")

        agent_to_move = None
        move_coords = game_vis.get_input_coords(adventurer)
        if move_coords in agent_coords:
            print(self.colour+" player chose the coordinates of the tile where their Agent can move from.")
            agent_to_move = adventurer.game.play_area[move_coords[0]][move_coords[1]].agent
        else:
            print(self.colour+" player chose coordinates away from the tile where their Agent can move from.")
            agent_to_move = None

        #clean up the highlights
        game_vis.clear_prompt()
        game_vis.clear_move_options()
        return agent_to_move
    
    #Give the player the choice to attack
    #@TODO highlight specific tokens to attack
    #@TODO prompt the player on victory for how much wealth to take using input()
    def check_attack_adventurer(self, adventurer, other_adventurer):
        attack_coords = [[adventurer.current_tile.tile_position.longitude
                    , adventurer.current_tile.tile_position.latitude]]

        #make sure that tiles and token positions are up to date
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]
        game_vis.draw_play_area()
        game_vis.draw_tokens()
        game_vis.draw_scores()
            
        #highlight the tile where the opposing Adventurer can be attacked
        print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(game.adventurers[self].index(adventurer)+1)
              +" can attack "+ other_adventurer.player.colour+" player's Adventurer")
        game_vis.draw_move_options(attack_coords=attack_coords)

        #prompt the player to input
        print("Prompting the "+self.colour+" player for input")
#        game_vis.clear_prompt()
        game_vis.give_prompt("If you want "+str(self.colour)+" Adventurer #" 
                           +str(game.adventurers[self].index(adventurer)+1) 
                           +" to attack "+ other_adventurer.player.colour+" player's Adventurer, then click their tile. "
                                      +" Otherwise, click elsewhere.")

        attack = False
        move_coords = game_vis.get_input_coords(adventurer)
        if move_coords in attack_coords:
            print(self.colour+" player chose the coordinates of the tile where their Adventurer can attack.")
            attack = True
        else:
            print(self.colour+" player chose coordinates away from the tile where their Adventurer can attack.")
            attack = False

        #clean up the highlights
        game_vis.clear_prompt()
        game_vis.clear_move_options()
#             game_vis.draw_tokens()
        return attack
    
    #@TODO prompt the player on victory for how much wealth to take 
    def check_attack_agent(self, adventurer, agent):
        attack_coords = [[adventurer.current_tile.tile_position.longitude
                        , adventurer.current_tile.tile_position.latitude]]
        game = adventurer.game
        game_vis = self.games[game.game_id]["game_vis"]

        #make sure that tiles and token positions are up to date
        game_vis.draw_play_area()
        game_vis.draw_tokens()
        game_vis.draw_scores()
            
        #highlight the tile where the opposing Agent can be attacked
        print("Highlighting the tile where "+self.colour+" player's Adventurer #"+str(game.adventurers[self].index(adventurer)+1)
              +" can attack "+ agent.player.colour+" player's Adventurer")
        game_vis.draw_move_options(attack_coords=attack_coords)

        #prompt the player to input
        print("Prompting the "+self.colour+" player for input")
#        game_vis.clear_prompt()
        game_vis.give_prompt("If you want "+str(self.colour)+" Adventurer #" 
                           +str(game.adventurers[self].index(adventurer)+1) 
                           +" to attack "+ agent.player.colour+" player's Agent, then click their tile. "
                                      +" Otherwise, click elsewhere.")

        attack = False
        move_coords = game_vis.get_input_coords(adventurer)
        if move_coords in attack_coords:
            print(self.colour+" player chose the coordinates of the tile where their Adventurer can attack.")
            attack = True
        else:
            print(self.colour+" player chose coordinates away from the tile where their Adventurer can attack.")
            attack = False

        #clean up the highlights
        game_vis.clear_prompt()
        game_vis.clear_move_options()
#             game_vis.draw_tokens()
        return attack
    
    # Always restor own Agents if it can be afforded
    def check_restore_agent(self, adventurer, agent):
        if agent.player == adventurer.player and adventurer.wealth >= adventurer.game.COST_AGENT_RESTORE:
            return True
        else:
            return False
