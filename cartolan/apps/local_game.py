'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import random
from cartolan.core.setup import create_game
from cartolan.editions.modes import GameBeginner, GameRegular, GameAdvanced
from cartolan.players.human_local import PlayerHuman
from cartolan.players.heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter
from cartolan.players.heuristical import PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter, PlayerRegularPirate
from cartolan.core.tiles import Tile, WindDirection, TileEdges
from cartolan.ui.live_visuals import GameVisualisation #, ClientGameVisualisation

#First some global functions to set up the game area
def setup_simulation(players, game_mode, movement_rules, exploration_rules, mythical_city=True):
    '''Deprecated wrapper: use cartolan.core.setup.create_game instead.'''
    return create_game(game_mode, players, movement_rules, exploration_rules, mythical_city)


class InteractiveGame:
    '''A wrapper for Game class objects to refresh visuals as play progresses'''
    # Now for the constants
    HUMAN_PLAYER_COLOURS = ["purple", "pink", "brown", "white"]
    GAME_MODES = { 'Beginner':{'game_type':GameBeginner}
              , 'Regular':{'game_type':GameRegular}
              }
    MOVEMENT_RULES = ['initial', 'budgetted']
    EXPLORATION_RULES = ['clockwise', 'continuous']
    NUM_PLAYERS_OPTIONS = [2, 3, 4]
    STARTING_DIMENSIONS = [20, 10]
    STARTING_ORIGIN = [9, 4]
    
    def __init__(self):
        # These parameters will likely be changed each game
        self.game_mode = "Regular"
        self.movement_rules = "initial"
        self.exploration_rules = "continuous"
        self.mythical_city = True
        self.num_players = 2
        self.num_human_players = self.num_players

        
    def click_play_game(self, event):
        self.play_game()
        
    def select_mode(self, label):
        self.game_mode = label
        
    def select_movement(self, label):
        self.movement_rules = label
    
    def select_exploration(self, label):
        self.exploration_rules = label
    
    def set_num_human_players(self, label):
        self.num_human_players = int(label)
    
    def setup_players(self):
        '''Sets up a list of Cartolan.PlayerHuman to play the game'''
        # add human players
        for human_player_num in range(0, self.num_human_players):
            self.players.append(PlayerHuman(self.HUMAN_PLAYER_COLOURS[human_player_num]))

    
    def play_game(self):
        '''Sets up the play_area and then substitutes for the game's own start_game method'''
        
        #start the visuals, to be updated by the human players before and during turns
        # sys.stdout = stdout_backup
        self.dimensions = self.STARTING_DIMENSIONS
        self.origin = self.STARTING_ORIGIN 
               
        #Set up a list of players
        self.players = []
        self.setup_players()
        
        #setup the game
        print("setting up the play area")
        self.game = setup_simulation(self.players
                                     , self.GAME_MODES[self.game_mode]["game_type"]
                                     , self.movement_rules
                                     , self.exploration_rules
                                     , self.mythical_city)
        
#        min_longitude, max_longitude = 0, 0
#        min_latitude, max_latitude = 0, 0
#        for longitude in self.game.play_area:
#            if longitude < min_longitude:
#                min_longitude = longitude
#            elif longitude > max_longitude:
#                max_longitude = longitude
#            for latitude in self.game.play_area[longitude]:
#                if latitude < min_latitude:
#                    min_latitude = latitude
#                elif latitude > max_latitude:
#                    max_latitude = latitude
#        self.origin = [-min_longitude + GameVisualisation.DIMENSION_BUFFER
#                  , -min_latitude + GameVisualisation.DIMENSION_BUFFER
#                  ]
#        self.dimensions = [max_longitude - min_longitude + 2*GameVisualisation.DIMENSION_BUFFER
#                      , max_latitude - min_latitude + 2*GameVisualisation.DIMENSION_BUFFER
#                      ]
        self.origin = [1, 1]
        self.dimensions = [2, 2]
        
        #visualise this initial setup
#        self.game_vis = PlayAreaVisualisation(self.game, self.dimensions, self.origin)
        self.game_vis = GameVisualisation(self.game, self.dimensions, self.origin)
        print("starting visuals")
        self.game_vis.draw_play_area()
        self.game_vis.draw_tokens()
        
        #Let the players reference game and especially visuals, for the GUI
        for player in self.players:
            player.connect_gui(self.game_vis)
        
        #run the game
        self.game.game_over = False
        while not self.game.game_over:
#             pyplot.show(self.game_vis)
            self.game.turn += 1
            self.game.game_over = self.game.play_round()
        
            #Draw the changes to the play area
#             self.game_vis.draw_play_area(self.game.play_area)
            
#             #Draw the computer players' paths but clear their history so that only the last turn is ever drawn
#             self.game_vis.draw_routes(self.players)
#             for player in self.players:
#                 for adventurer in player.adventurers:
#                     adventurer.route = []
                
        self.game_vis.give_prompt(self.game.winning_player.name+" won the game (click to close)")
#         pyplot.waitforbuttonpress() #Delay until the player has read the message
        self.game_vis.get_input_coords(self.game.adventurers[self.game.winning_player][0])
        self.game_vis.close()

class InteractiveSimulation(InteractiveGame):
    '''Extends the InteractiveGame class to include virtual, computer-controlled, players'''
    # Now for the constants
    HUMAN_PLAYER_COLOURS = ["purple", "pink", "brown", "black"]
    GAME_MODES = { 'Beginner':{'game_type':GameBeginner, 'player_set':{"blue":PlayerBeginnerExplorer
                                                                   , "red":PlayerBeginnerTrader
                                                                   , "yellow":PlayerBeginnerRouter
#                                                                    , "green":PlayerBeginnerGenetic
                                                                      }}
              , 'Regular':{'game_type':GameRegular, 'player_set':{
                                                                  "orange":PlayerRegularPirate
#                                                                    , "blue":PlayerRegularExplorer
                                                                   , "red":PlayerRegularTrader
                                                                   , "yellow":PlayerRegularRouter
#                                                                    , "green":PlayerRegularGenetic
                                                                  }
                          }
                 }
    
    def __init__(self):
        # These parameters will likely be changed each game
        super().__init__()
        self.num_players = 4
        self.num_human_players = 1
        
    def set_num_human_players(self, label):
        self.num_human_players = int(label)
    
    def setup_players(self):
        super().setup_players()
        
        #add virtual computer players
        player_colours = random.sample(list(self.GAME_MODES[self.game_mode]["player_set"]), self.num_players - len(self.players))
        for player_colour in player_colours:
            #player_colour = random.choice(player_set)
            self.players.append(self.GAME_MODES[self.game_mode]["player_set"][player_colour](player_colour))
            
#if __name__ == "__main__":
#    game_options = {"local":InteractiveSimulation, "network":ClientGameVisualisation}
#    game_choice = ""
#    while not game_choice in game_options:
#        game_choice = input("Please specify whether you want to play only with players on this computer, or with players on other computers too? Type 'local' or 'network' respectively\n")
#    client_visual = game_options[game_choice]()
#    if game_choice == "local":
#        prompt_text = "What version of Cartolan would you like to play? Type in either "
#        for game_mode in client_visual.GAME_MODES:
#            prompt_text += "'" +game_mode+ "' or "
#        game_mode = ""
#        while not game_mode in client_visual.GAME_MODES:
#            game_mode = input(prompt_text + "\n")
#        client_visual.game_mode = game_mode
#        min_players = client_visual.GAME_MODES[game_mode]["game_type"].MIN_PLAYERS
#        max_players = client_visual.GAME_MODES[game_mode]["game_type"].MAX_PLAYERS
#        num_human_players = 0
#        while not num_human_players in range(1, max_players+1):
#            num_human_players = int(input("How many human players will take part in this game? Enter a number between 1 and "+str(max_players) +"\n"))
#        if num_human_players < max_players:
#            num_players = 0
#            while not num_players in range(min_players, max_players+1):
#                num_players = num_human_players + int(input("How many computer players will take part in this game? Enter a number between 0 and "+str(max_players - num_human_players)+"\n"))
#        else:
#            num_players = num_human_players
#        client_visual.num_human_players = num_human_players
#        client_visual.num_players = num_players
#        client_visual.play_game()