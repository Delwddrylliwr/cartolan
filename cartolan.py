import sys
from matplotlib import pyplot
import pandas
import random
import csv
from game import GameBeginner, GameRegular, GameAdvanced
from players_human import PlayerHuman
from players_heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter
from players_heuristical import PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter, PlayerRegularPirate
from visuals import PlayAreaVisualisation, GameVisualisation, PlayStatsVisualisation
from regular import DisasterTile
from base import WaterTile, LandTile, WindDirection, TileEdges
from server import CartolanServer
from time import sleep

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
    game.CITY_TYPE(game, True, True).place_tile(0,0)
#     capital_tile = CityTileBeginner(game, True, True)
#     capital_tile.place_tile(0,0)
    
    #place surrounding water tiles
#     if len(players) == 2:
    if True:
        WaterTile(game, WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(0, 1) #north
        WaterTile(game, WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(1, 0) #east
        WaterTile(game, WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(0, -1) #south
        WaterTile(game, WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(-1, 0) #west
    elif mythical_city and len(players) == 3:
        WaterTile(game, WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(0, 1) #north
        WaterTile(game, WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(1, 0) #east
        WaterTile(game, WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(0, -1) #south
        WaterTile(game, WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(-1, 0) #west
    elif len(players) == 4 or (not mythical_city and len(players) == 3):
        WaterTile(game, WindDirection(False,False), TileEdges(True,True,True,True), False).place_tile(0, 1) #north
        WaterTile(game, WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(1, 0) #east
        WaterTile(game, WindDirection(True,True), TileEdges(True,True,True,True), False).place_tile(0, -1) #south
        WaterTile(game, WindDirection(False,False), TileEdges(True,True,True,True), False).place_tile(-1, 0) #west
         
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


#import gspread
#from oauth2client.service_account import ServiceAccountCredentials

## use creds to create a client to interact with the Google Drive API
#scope = ['https://spreadsheets.google.com/feeds']
##scope = ['https://www.googleapis.com/auth/spreadsheets']
#creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
#client = gspread.authorize(creds)

## Find a workbook by name and open the first sheet
## Make sure you use the right name here.
#sheet = client.open("test").sheet1
#tile_distribution = sheet.col_values(1)

def setup_water_pile(players, game_mode, movement_rules, exploration_rules, mythical_city):
    '''Part of game setup for Cartolan, this creates a tile of shuffled water-backed tiles ready for play
    
    Arguments:
    List of Cartolan.Player for the Players involved in the game
    Cartolan.Game for the game that these tiles are being laid for
    String giving the movement rules variant that will apply for this game
    String giving the exploration rules variant that will apply for this game
    '''
    game = setup_adventurers(players, game_mode, movement_rules, exploration_rules, mythical_city)
    
    import random
    
    #read in the numbers of water tiles, from google sheets?
    import csv

    tile_distribution = []
    wonder_distribution = []
    disaster_distribution = []

    with open("tile_distribution.csv") as csvfile:
        readCSV = csv.reader(csvfile)
        for row in readCSV:
            tile_distribution.append(int(row[0]))
            wonder_distribution.append(int(row[1]))
            if game_mode in [GameRegular, GameAdvanced]:
                disaster_distribution.append(row[2])
            else:
                disaster_distribution.append(0)
    
    #construct the water tile deck
    row_count = 0
    tiles = []
    for uc_water in [True, False]:
        for ua_water in [True, False]:
            for dc_water in [True, False]:
                for da_water in [True, False]:
                    if uc_water or ua_water:
                        for tile_num in range(0, int(tile_distribution[row_count])
                                              -int(wonder_distribution[row_count])
                                              -int(disaster_distribution[row_count])):
                            wind_direction = WindDirection(north = True, east = True)
                            tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
                            tiles.append(WaterTile(game, wind_direction, tile_edges, False))
                        for tile_num in range(0, int(wonder_distribution[row_count])):
                            wind_direction = WindDirection(north = True, east = True)
                            tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
                            tiles.append(WaterTile(game, wind_direction, tile_edges, True))
                        for tile_num in range(0, int(disaster_distribution[row_count])):
                            wind_direction = WindDirection(north = True, east = True)
                            tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
                            tiles.append(DisasterTile(game, "water", wind_direction))
                        row_count += 1
    
    #draw a suitable number of tiles from the deck for a pile
#     num_tiles = len(players)*game.WATER_TILES_PER_PLAYER
    num_tiles = game.NUM_WATER_TILES
    tile_pile = game.tile_piles["water"]
    for tile in random.sample(tiles, num_tiles):
        tile_pile.add_tile(tile)
    
    tile_pile.shuffle_tiles()
    
    print("Built a Water tile pile with " +str(len(game.tile_piles["water"].tiles))+ " tiles, and shuffled it")
    
    return game

# #test water tile instantiation
# row_count = 0
# game = GameBeginner(2, "initial", "clockwise")
# game.tile_piles["water"] = TilePile("water",[])
# tile_pile = game.tile_piles["water"]
# for uc_water in [True, False]:
#     for ua_water in [True, False]:
#         for dc_water in [True, False]:
#             for da_water in [True, False]:
#                 if uc_water or ua_water:
#                     for tile_num in range(0, int(tile_distribution[row_count])):
#                         tile_position = TilePosition(longitude = None, latitude = None)
#                         wind_direction = WindDirection(north = True, east = True)
#                         tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
#                         tile_pile.add_tile(WaterTile(game, tile_position, wind_direction, tile_edges))
#                     print(str(uc_water) +" "+ str(ua_water) +" "+ str(dc_water) +" "+ str(da_water) +" "+ str(tile_distribution[row_count]))
#                     row_count += 1
# print(len(game.tile_piles["water"].tiles))

def setup_land_pile(players, game_mode, movement_rules, exploration_rules, mythical_city):
    '''Part of game set up for Cartolan, this creates a tile of shuffled land-backed tiles ready for play
    
    Arguments:
    List of Cartolan.Player for the Players involved in the game
    Cartolan.Game for the game that these tiles are being laid for
    String giving the movement rules variant that will apply for this game
    String giving the exploration rules variant that will apply for this game
    '''
    game = setup_water_pile(players, game_mode, movement_rules, exploration_rules, mythical_city)
    
    if not game_mode in [GameRegular, GameAdvanced]:
        return game
    
    #read in the numbers of water and land tiles, from google sheets?
    
    tile_distribution = []
    wonder_distribution = []
    disaster_distribution = []

    with open("tile_distribution.csv") as csvfile:
        readCSV = csv.reader(csvfile)
        for row in readCSV:
            tile_distribution.append(row[0])
            wonder_distribution.append(row[1])
            disaster_distribution.append(row[2])

    #land tiles
    row_count = 12
    tiles = []
    for uc_water in [True, False]:
        for ua_water in [True, False]:
            for dc_water in [True, False]:
                for da_water in [True, False]:
                    if not uc_water or not ua_water:
                        for tile_num in range(0, int(tile_distribution[row_count])
                                              -int(wonder_distribution[row_count])
                                              -int(disaster_distribution[row_count])):
                            wind_direction = WindDirection(north = True, east = True)
                            tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
                            tiles.append(LandTile(game, wind_direction, tile_edges, False))
                        for tile_num in range(0, int(wonder_distribution[row_count])):
                            wind_direction = WindDirection(north = True, east = True)
                            tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
                            tiles.append(LandTile(game, wind_direction, tile_edges, True))
                        for tile_num in range(0, int(disaster_distribution[row_count])):
                            wind_direction = WindDirection(north = True, east = True)
                            tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
                            tiles.append(DisasterTile(game, "land", wind_direction))
                        row_count += 1
    
#     num_tiles = len(players)*game.LAND_TILES_PER_PLAYER
    num_tiles = game.NUM_LAND_TILES
    tile_pile = game.tile_piles["land"]
    for tile in random.sample(tiles, num_tiles):
        tile_pile.add_tile(tile)
    
    tile_pile.shuffle_tiles()    
    print("Built a Land tile pile with " +str(len(game.tile_piles["land"].tiles))+ " tiles, and shuffled it")
    
    return game
                        
# #test land tile instantiation
# row_count = 12
# game = GameBeginner(2, "initial", "clockwise")
# game.tile_piles["land"] = TilePile("land",[])
# tile_pile = game.tile_piles["land"]
# for uc_water in [True, False]:
#     for ua_water in [True, False]:
#         for dc_water in [True, False]:
#             for da_water in [True, False]:
#                 if not uc_water or not ua_water:
#                     for tile_num in range(0, int(tile_distribution[row_count])):
#                         tile_position = TilePosition(longitude = None, latitude = None)
#                         wind_direction = WindDirection(north = True, east = True)
#                         tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
#                         tile_pile.add_tile(LandTile(game, tile_position, wind_direction, tile_edges))
#                     print(str(uc_water) +" "+ str(ua_water) +" "+ str(dc_water) +" "+ str(da_water) +" "+ str(tile_distribution[row_count]))
#                     row_count += 1
# print(len(game.tile_piles["land"].tiles))

def setup_simulation(players, game_mode, movement_rules, exploration_rules, mythical_city = True):
    '''The final part of game setup for Cartolan, this chooses a random play order for the players involved
    
    Arguments:
    List of Cartolan.Player for the Players involved in the game
    Cartolan.Game for the game that these tiles are being laid for
    String giving the movement rules variant that will apply for this game
    String giving the exploration rules variant that will apply for this game
    '''
    game = setup_land_pile(players, game_mode, movement_rules, exploration_rules, mythical_city)
    
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
        self.mythical_city = False
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


#Now the various classes for differnt player combinations
class Simulations():
    """Run simulations of the game Cartolan."""
    GAME_MODES = { 'Beginner':{'game_type':GameBeginner, 'player_set':{"blue":PlayerBeginnerExplorer
                                                                            , "red":PlayerBeginnerTrader
                                                                            , "yellow":PlayerBeginnerRouter
                                                                      , "orange":PlayerBeginnerTrader}}
                      , 'Regular':{'game_type':GameRegular, 'player_set':{"blue":PlayerRegularExplorer
                                                                            , "red":PlayerRegularTrader
                                                                            , "yellow":PlayerRegularRouter
                                                                          , "orange":PlayerRegularPirate}}
                      }    
    MOVEMENT_RULES = ['initial', 'budgetted']
    EXPLORATION_RULES = ['clockwise', 'continuous']
    NUM_PLAYERS_OPTIONS = [2, 3, 4]
    
    def __init__(self):
        self.game_mode = "Regular"
        self.movement_rules = "initial" #"budgetted"
        self.exploration_rules = "clockwise" #,"continuous"
        self.mythical_city = False
        self.num_players = 2
        
        self.num_games = 50

    def click_run_sims(self, event):
        self.run_sims()
        
    def select_mode(self, label):
        self.game_mode = label
        
    def select_movement(self, label):
        self.movement_rules = label
    
    def select_exploration(self, label):
        self.exploration_rules = label
    
    def set_num_players(self, label):
        self.num_players = int(label)
    
    def set_num_sims(self, value):
        self.num_games = int(value)
    
    def setup_players(self):
        import random
        players = []
#             num_players = random.choice(num_players_options)
        player_colours = random.sample(list(self.GAME_MODES[self.game_mode]["player_set"]),self.num_players)
        for player_colour in player_colours:
            #player_colour = random.choice(player_set)
            players.append(self.GAME_MODES[self.game_mode]["player_set"][player_colour](player_colour))
        return players

        
    def run_sims(self):
        '''Method to run through a series of simulations, triggered by a UI button press'''
        #determine logging
        # stdout_backup = sys.stdout
#         sys.stdout = open(os.devnull, 'w')
        sys.stdout = open("./logs/cartolan_log.txt", 'w')
        # sys.stdout = sys.__stdout__

        #data to collect from each simulation
        self.sim_stats = pandas.DataFrame(columns = ["simulation_id", "num_players", "win_type", "turns"
                                                , "remaining_water_tiles"
                                                , "remaining_land_tiles"
                                                , "total_wealth_final", "max_wealth_final", "wealth_difference_final"
                                                , "winning_player_type", "winning_player_order", "winning_player_route"
                                                , "winning_player_agents"
                                                , "winning_player_adventurers"
                                                , "exploration_attempts", "failed_explorations"
                                                , "wealth_p1", "wealth_p2", "wealth_p3", "wealth_p4"
                                                , "num_adventurers_p1", "num_adventurers_p2"
                                                , "num_adventurers_p3", "num_adventurers_p4"
                                                , "num_agents_p1", "num_agents_p2", "num_agents_p3", "num_agents_p4"
                                                , "avg_route_p1", "avg_route_p2", "avg_route_p3", "avg_route_p4" 
                                                , "play_area", "players"])
        play_areas = {}
        player_sets = {}
        
        #retain the leftover tile distributions
        remaining_tile_edges = []

        #Function to collect average route lengths across a player's adventurers
        def avg_route_length(player):
            avg_route_length = 0
            for adventurer in player.adventurers:
                avg_route_length += len(adventurer.route)
            return avg_route_length/len(player.adventurers)

        # We have arrived! Time for the actual outcomes
        #@TODO multithread this: https://realpython.com/intro-to-python-threading/#starting-a-thread
        for sim_id in range(0, self.num_games):
            print("")
            #Instantiate players
            players = self.setup_players()

            #Instantiate a game
            if self.mythical_city:
                print("Setting up a "+self.game_mode+"-mode game, with "+self.movement_rules+" movement rules, and "
                  +self.exploration_rules+" exploration rules, and a mythical city")
            else:
                print("Setting up a "+self.game_mode+"-mode game, with "+self.movement_rules+" movement rules, and "
                  +self.exploration_rules+" exploration rules, and no mythical city")
            game = setup_simulation(players, self.GAME_MODES[self.game_mode]["game_type"]
                                    , self.movement_rules, self.exploration_rules, self.mythical_city)

            #run the game
            print("Starting simulation #"+str(sim_id)+" of "+self.game_mode+"-mode Cartolan, with " +str(self.num_players)+ " players")
            game.start_game()

            #record stats
            def player_strip(player_type):
                '''Reduces the name of a player type down '''
                name = player_type.__name__
                if "Beginner" in name:
                    return name[name.find("Beginner")+len("Beginner"):]
                elif "Regular" in name:
                    return name[name.find("Regular")+len("Regular"):]
                else:
                    return name[name.find("Player")+len("Player"):]
            
            if game.wealth_difference > 0 and self.num_players ==2:
                self.sim_stats = self.sim_stats.append( {"simulation_id":sim_id, "num_players":self.num_players
                                    , "win_type":game.win_type, "turns":game.turn
                                    , "remaining_water_tiles":len(game.tile_piles["water"].tiles)+len(game.discard_piles["water"].tiles)
                                    , "remaining_land_tiles":len(game.tile_piles["land"].tiles)+len(game.discard_piles["land"].tiles)
                                    , "total_wealth_final":game.total_vault_wealth
                                    , "max_wealth_final":game.max_wealth
                                    , "wealth_difference_final":game.wealth_difference
                                    , "winning_player_type":player_strip(type(game.winning_player))
                                    , "winning_player_order":game.players.index(game.winning_player)+1
                                    , "winning_player_route":avg_route_length(game.winning_player)
                                    , "winning_player_agents":len(game.winning_player.agents)
                                    , "winning_player_adventurers":len(game.winning_player.adventurers)
                                    , "exploration_attempts":game.exploration_attempts
                                    , "failed_explorations":game.num_failed_explorations 
                                    , "wealth_p1":game.players[0].vault_wealth
                                    , "wealth_p2":game.players[1].vault_wealth
                                    , "num_adventurers_p1":len(game.players[0].adventurers)
                                    , "num_adventurers_p2":len(game.players[1].adventurers)
                                    , "num_agents_p1":len(game.players[0].agents)
                                    , "num_agents_p2":len(game.players[1].agents)
                                    , "avg_route_p1":avg_route_length(players[0])
                                    , "avg_route_p2":avg_route_length(players[1])
                                              }, ignore_index=True)
            elif game.wealth_difference > 0 and self.num_players ==3:
                self.sim_stats = self.sim_stats.append( {"simulation_id":sim_id, "num_players":self.num_players
                                    , "win_type":game.win_type, "turns":game.turn
                                    , "remaining_water_tiles":len(game.tile_piles["water"].tiles)+len(game.discard_piles["water"].tiles)
                                    , "remaining_land_tiles":len(game.tile_piles["land"].tiles)+len(game.discard_piles["land"].tiles)
                                    , "total_wealth_final":game.total_vault_wealth
                                    , "max_wealth_final":game.max_wealth
                                    , "wealth_difference_final":game.wealth_difference
                                    , "winning_player_type":player_strip(type(game.winning_player))
                                    , "winning_player_order":game.players.index(game.winning_player)+1
                                    , "winning_player_route":avg_route_length(game.winning_player)
                                    , "winning_player_agents":len(game.winning_player.agents)
                                    , "winning_player_adventurers":len(game.winning_player.adventurers)
                                    , "exploration_attempts":game.exploration_attempts
                                    , "failed_explorations":game.num_failed_explorations 
                                    , "wealth_p1":game.players[0].vault_wealth, "wealth_p2":game.players[1].vault_wealth
                                    , "wealth_p3":game.players[2].vault_wealth
                                    , "num_adventurers_p1":len(game.players[0].adventurers)
                                    , "num_adventurers_p2":len(game.players[1].adventurers)
                                    , "num_adventurers_p3":len(game.players[2].adventurers)
                                    , "num_agents_p1":len(game.players[0].agents)
                                    , "num_agents_p2":len(game.players[1].agents)
                                    , "num_agents_p3":len(game.players[2].agents)
                                    , "avg_route_p1":avg_route_length(players[0])
                                    , "avg_route_p2":avg_route_length(players[1])
                                    , "avg_route_p3":avg_route_length(players[2])
                                              }, ignore_index=True)
            elif game.wealth_difference > 0 and self.num_players ==4:
                self.sim_stats = self.sim_stats.append( {"simulation_id":sim_id, "num_players":self.num_players
                                    , "win_type":game.win_type, "turns":game.turn
                                    , "remaining_water_tiles":len(game.tile_piles["water"].tiles)+len(game.discard_piles["water"].tiles)
                                    , "remaining_land_tiles":len(game.tile_piles["land"].tiles)+len(game.discard_piles["land"].tiles)
                                    , "total_wealth_final":game.total_vault_wealth
                                    , "max_wealth_final":game.max_wealth
                                    , "wealth_difference_final":game.wealth_difference
                                    , "winning_player_type":player_strip(type(game.winning_player))
                                    , "winning_player_order":game.players.index(game.winning_player)+1
                                    , "winning_player_route":avg_route_length(game.winning_player)
                                    , "winning_player_agents":len(game.winning_player.agents)
                                    , "winning_player_adventurers":len(game.winning_player.adventurers)
                                    , "exploration_attempts":game.exploration_attempts
                                    , "failed_explorations":game.num_failed_explorations 
                                    , "wealth_p1":game.players[0].vault_wealth, "wealth_p2":game.players[1].vault_wealth
                                    , "wealth_p3":game.players[2].vault_wealth, "wealth_p4":game.players[3].vault_wealth
                                    , "num_adventurers_p1":len(game.players[0].adventurers)
                                    , "num_adventurers_p2":len(game.players[1].adventurers)
                                    , "num_adventurers_p3":len(game.players[2].adventurers)
                                    , "num_adventurers_p4":len(game.players[3].adventurers)
                                    , "num_agents_p1":len(game.players[0].agents)
                                    , "num_agents_p2":len(game.players[1].agents)
                                    , "num_agents_p3":len(game.players[2].agents)
                                    , "num_agents_p4":len(game.players[3].agents)
                                    , "avg_route_p1":avg_route_length(players[0])
                                    , "avg_route_p2":avg_route_length(players[1])
                                    , "avg_route_p3":avg_route_length(players[2])
                                    , "avg_route_p4":avg_route_length(players[3])
                                              }, ignore_index=True)
            play_areas[sim_id] = game.play_area
            player_sets[sim_id] = game.players
            
            for tile_pile in game.tile_piles.values():
                for tile in tile_pile.tiles:
                    tile_edges = tile.tile_edges
                    tile_edges_string = ""
                    if tile_edges.upwind_clock_water:
                        tile_edges_string += "Water"
                    else:
                        tile_edges_string += "Land"
                    if tile_edges.upwind_anti_water:
                        tile_edges_string += "Water"
                    else:
                        tile_edges_string += "Land"
                    if tile_edges.downwind_clock_water:
                        tile_edges_string += "Water"
                    else:
                        tile_edges_string += "Land"
                    if tile_edges.downwind_anti_water:
                        tile_edges_string += "Water"
                    else:
                        tile_edges_string += "Land"
                    remaining_tile_edges.append(tile_edges_string)


        # Make sure that graphical outputs go here
#         sys.stdout = stdout_backup
        # Let's compare the performance of winning players to others
        play_stats_visualisation = PlayStatsVisualisation(self.sim_stats)
        play_stats_visualisation.win_type_comparison()
        play_stats_visualisation.turns_to_win()
        play_stats_visualisation.player_type_comparison()
        play_stats_visualisation.player_order_comparison()
        play_stats_visualisation.wealth_comparison()
        # play_stats_visualisation.wealth_variance_comparison()
        play_stats_visualisation.route_comparison()
        play_stats_visualisation.token_comparison()
        play_stats_visualisation.tile_comparison()
#         play_stats_visualisation.discards_comparison()
        play_stats_visualisation.remaining_tiles_distribution(remaining_tile_edges)
        play_stats_visualisation.fig.tight_layout(pad=2.0)
        

        def prep_visuals(sim_id_to_vis, title):
            play_area_to_vis = play_areas[sim_id_to_vis]
            #work out the ideal dimensions for the visualisation
            h_dimension = max(play_area_to_vis.keys())-min(play_area_to_vis.keys())
            h_origin = abs(min(play_area_to_vis.keys()))
            max_latitude = 0
            min_latitude = 0
            v_dimension = 0
            for longitude in play_area_to_vis:
                if max(play_area_to_vis[longitude].keys()) > max_latitude:
                    max_latitude = max(play_area_to_vis[longitude].keys())
                if min(play_area_to_vis[longitude].keys()) < min_latitude:
                    min_latitude = min(play_area_to_vis[longitude].keys())
            v_dimension = max_latitude - min_latitude
            v_origin = abs(min_latitude)
            dimensions = [h_dimension + 1, v_dimension + 1]
            origin = [h_origin, v_origin] 
            #render the play area and routes
            game_vis = PlayAreaVisualisation(dimensions, origin, title)
#             game_vis_med_wealth_difference.draw_play_area(play_area_to_vis, play_area_to_vis)
            game_vis.draw_play_area(play_area_to_vis)
            #@TODO earlier agent positions seem to be ignored
            game_vis.draw_tokens(player_sets[sim_id_to_vis])
            game_vis.draw_routes(player_sets[sim_id_to_vis])
            print("Determined that the dimensions for the "+title+" are "+ str(h_dimension)+", "+str(v_dimension))
            print("Determined that the origin positions for the "+title+" are "+ str(h_origin)+", "+str(v_origin))
            
        
        # Let's look at the final layout and paths of the game with the median wealth difference, if one exists:
        if self.sim_stats["wealth_difference_final"].median() in self.sim_stats["wealth_difference_final"].values:
            sim_id_med_wealth_difference = self.sim_stats[self.sim_stats["wealth_difference_final"] 
                                                  == self.sim_stats["wealth_difference_final"].median()]["simulation_id"].values[0]
            prep_visuals(sim_id_med_wealth_difference, "How the median wealth difference game progressed")
        
        # Let's also look at the games with maximum and minimum wealth differences
        sim_id_max_wealth_difference = self.sim_stats[self.sim_stats["wealth_difference_final"] 
                                                  == self.sim_stats["wealth_difference_final"].max()]["simulation_id"].values[0]
        prep_visuals(sim_id_max_wealth_difference, "How the maximum wealth difference game progressed")
        
        sim_id_min_wealth_difference = self.sim_stats[self.sim_stats["wealth_difference_final"] 
                                                  == self.sim_stats["wealth_difference_final"].min()]["simulation_id"].values[0]
        prep_visuals(sim_id_min_wealth_difference, "How the minimum wealth difference game progressed")
        
        pyplot.show()
        

class InteractiveSimulation(InteractiveGame):
    '''Extends the InteractiveGame class to include virtual, computer-controlled, players'''
    # Now for the constants
    HUMAN_PLAYER_COLOURS = ["purple", "pink", "brown", "white"]
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
   
class NetworkGame(InteractiveSimulation):
    def __init__(self):
        # Seek server port from host
        print("STARTING SERVER ON LOCALHOST")
        address = input("Host:Port (localhost:8000): ")
        if not address:
            host, port = "localhost", 8000
        else:
            host, port = address.split(":")
        
        server = CartolanServer(localaddr = (host, int(port)))
        while True:
            server.tick()
            sleep(0.01)
         
# class AISimulations(Simulations):
#     AI_PLAYER_COLOURS = ["green", "brown", "pink", "purple"]
    
#     def __init__(self):
#         super().__init__()
#         self.num_feed_fwd = 1
#         self.num_players = 4
        
#         self.train = True
        
#         #Instantiate the AI players, who will be reused between individual games
#         #Add the specified number of AI players
#         self.feed_fwd_players = []
#         for AI_index in range(self.num_feed_fwd):
#             AI_player = PlayerFeedFwd(self.AI_PLAYER_COLOURS[AI_index], train=self.train)
#             AI_player.build_network(self.GAME_MODES[self.game_mode]["game_type"])
#             self.feed_fwd_players.append(AI_player)
    
#     def setup_players(self):
#         import random
#         players = []
#         #Add the specified number of AI players
#         for AI_index in range(self.num_feed_fwd):
#             player = self.feed_fwd_players[AI_index]
#             players.append(player)
#             #Reset the player in all respects except the AI parameters
#             player.vault_wealth = 0
#             player.adventurers = []
#             player.agents = []
#             player.locations_to_avoid = []
#             player.attack_history = []
#             player.player_to_mimic = random.choice(list(self.GAME_MODES[self.game_mode]["player_set"].values()))  #each game a different class of heuristical player will be mimicked
        
#         #Fill the rest with random heuristical players
#         player_colours = random.sample(list(self.GAME_MODES[self.game_mode]["player_set"]),self.num_players - len(players))
#         for player_colour in player_colours:
#             #player_colour = random.choice(player_set)
#             players.append(self.GAME_MODES[self.game_mode]["player_set"][player_colour](player_colour))
#         return players
        
        

# class InteractiveAISimulation(InteractiveSimulation):
#     AI_PLAYER_COLOURS = ["green", "brown", "pink", "purple"]
    
#     def __init__(self):
#         super().__init__()
#         self.num_players = 4
#         self.num_human_players = 0
#         self.num_feed_fwd = 1
        
#         self.train = True
        
#         #Instantiate the AI players, who will be reused between individual games
#         #Add the specified number of AI players
#         self.feed_fwd_players = []
#         for AI_index in range(self.num_feed_fwd):
#             AI_player = PlayerFeedFwd(self.AI_PLAYER_COLOURS[AI_index], train=self.train)
#             AI_player.build_network(self.GAME_MODES[self.game_mode]["game_type"])
#             self.feed_fwd_players.append(AI_player)
        
#     def setup_players(self):
#         import random
        
#         #add AI computer players
#         #Add the specified number of AI players
#         for AI_index in range(self.num_feed_fwd):
#             player = self.feed_fwd_players[AI_index]
#             self.players.append(player)
#             #Reset the player in all respects except the AI parameters
#             player.vault_wealth = 0
#             player.adventurers = []
#             player.agents = []
#             player.locations_to_avoid = []
#             player.attack_history = []
#             player.player_to_mimic = random.choice(list(self.GAME_MODES[self.game_mode]["player_set"].values())) #each game a different class of heuristical player will be mimicked
        
#         #Add human and heuristical computer players
#         super().setup_players()
        
#     #@TODO at end of game, make sure an extra reward is registered and record the network weights to file
#     def play_game(self):
#         pass
    
#     def run(display_option, speed, params):
#         pygame.init()
#         agent = DQNAgent(params)
        

#         record = 0
#         while counter_games < params['episodes']:
            
