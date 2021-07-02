'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import random
from game import GameBeginner, GameRegular, GameAdvanced
from players_human import PlayerHuman
from players_heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter
from players_heuristical import PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter, PlayerRegularPirate
from base import Tile, WindDirection, TileEdges
from live_visuals import GameVisualisation #, ClientGameVisualisation

#First some global functions to set up the game area
def setup_tiles(players, game_mode, movement_rules, exploration_rules, mythical_city):
    '''Part of game setup for Cartolan, this places the intital tiles ready for play
    
    Arguments:
    List of Cartolan.Player for the Players involved in the game
    Cartolan.Game for the game that these tiles are being laid for
    String giving the movement rules variant that will apply for this game
    String giving the exploration rules variant that will apply for this game
    '''
    
    game = game_mode(players, movement_rules, exploration_rules)
#     exec("CityTile" +game_mode+ "(game, True, True).place_tile(0,0)")
    game.CITY_TYPE(game, WindDirection(True,True), TileEdges(True,True,True,True), True, True).place_tile(0,0)
#     capital_tile = CityTileBeginner(game, True, True)
#     capital_tile.place_tile(0,0)
    
    #place surrounding water tiles
#     if len(players) == 2:
    if True:
        Tile(game, "water", WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(0, 1) #north
        Tile(game, "water", WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(1, 0) #east
        Tile(game, "water", WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(0, -1) #south
        Tile(game, "water", WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(-1, 0) #west
    elif mythical_city and len(players) == 3:
        Tile(game, "water", WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(0, 1) #north
        Tile(game, "water", WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(1, 0) #east
        Tile(game, "water", WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(0, -1) #south
        Tile(game, "water", WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(-1, 0) #west
    elif len(players) == 4 or (not mythical_city and len(players) == 3):
        Tile(game, "water", WindDirection(False,False), TileEdges(True,True,True,True), False).place_tile(0, 1) #north
        Tile(game, "water", WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(1, 0) #east
        Tile(game, "water", WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(0, -1) #south
        Tile(game, "water", WindDirection(False,False), TileEdges(True,True,True,True), False).place_tile(-1, 0) #west

    game.setup_tile_pile("water")
    if game_mode in [GameRegular, GameAdvanced]:
        game.setup_tile_pile("land")
        if mythical_city:
            game.tile_piles["land"].tiles.append(game.CITY_TYPE(game, WindDirection(True,True), TileEdges(False,False,False,False), False, True))
      
    print("Placed the Capital tile, and surrounding water tiles")
    return game

def setup_adventurers(players, game_mode, movement_rules, exploration_rules, mythical_city):
    '''Part of game setup for Cartolan, this places the intital Adventurer tokens for each player
    
    Arguments:
    List of Cartolan.Player for the Players involved in the game
    Cartolan.Game for the game that these tiles are being laid for
    String giving the movement rules variant that will apply for this game
    String giving the exploration rules variant that will apply for this game
    '''
    game = setup_tiles(players, game_mode, movement_rules, exploration_rules, mythical_city)
    
    for player in players:
#         exec("Adventurer" +game_mode+ "(game, player, game.cities[0])") #this should probably work, because it doesn't need to create a local
        print("adding an adventurer for " +str(player.colour)+ " player, who already has " +str(len(game.adventurers[player]))+ " adventurers")
#         AdventurerBeginner(game, player, game.cities[0])
        game.ADVENTURER_TYPE(game, player, game.cities[0])
    
    print("Placed starting adventurer for each player")
    
    return game

def setup_simulation(players, game_mode, movement_rules, exploration_rules, mythical_city = True):
    '''The final part of game setup for Cartolan, this chooses a random play order for the players involved
    
    Arguments:
    List of Cartolan.Player for the Players involved in the game
    Cartolan.Game for the game that these tiles are being laid for
    String giving the movement rules variant that will apply for this game
    String giving the exploration rules variant that will apply for this game
    '''
    game = setup_adventurers(players, game_mode, movement_rules, exploration_rules, mythical_city)
      
    #turn order has been handled by the parent setup
#     game.players = random.shuffle(game.players)
    print("Randomly chose " +str(players[0].colour)+ " player to start")
    return game


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
                
        self.game_vis.give_prompt(self.game.winning_player.colour+" player won the game (click to close)")
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