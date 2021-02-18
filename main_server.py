'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''
from app_server import CartolanServer
from players_heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter, PlayerRegularPirate, PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter
from game import GameBeginner, GameRegular
from time import sleep
import sys
#from game_config import BeginnerConfig, RegularConfig, AdvancedConfig

DEFAULT_DIMENSIONS = [20, 10]
DEFAULT_ORIGIN = [9, 4]
GAME_MODES = { 'Beginner':{'game_type':GameBeginner, 'player_set':{"blue":PlayerBeginnerExplorer
                                                                   , "red":PlayerBeginnerTrader
                                                                   , "yellow":PlayerBeginnerRouter
                                                                      }}
              , 'Regular':{'game_type':GameRegular, 'player_set':{
                                                                  "orange":PlayerRegularPirate
                                                                    , "blue":PlayerRegularExplorer
                                                                   , "red":PlayerRegularTrader
                                                                   , "yellow":PlayerRegularRouter
                                                                  }
                          }
                 }
#All games will start with the following configurations of tiles and (per player) adventurers
INITIAL_TILES = [{"longitude":str(0), "latitude":str(0)
             , "tile_type":"capital", "tile_back":"water"
             , "tile_edges":{"upwind_clock":"True", "upwind_anti":"True"
                             , "downwind_clock":"True", "downwind_anti":"True"}
             , "wind_direction":{"north":"True", "east":"True"}
             }]
#include surrounding water tiles
for tile_position in [[0,1], [1,0], [0,-1], [-1,0]]:
    INITIAL_TILES.append({"longitude":str(tile_position[0]), "latitude":str(tile_position[1])
                 , "tile_type":"plain", "tile_back":"water"
                 , "tile_edges":{"upwind_clock":"True", "upwind_anti":"True"
                             , "downwind_clock":"True", "downwind_anti":"True"}
                 , "wind_direction":{"north":"True", "east":"True"}
                 })
INITIAL_ADVENTURERS = [[str(0),str(0)]] #a list of tuples for each adventurer's long/lat
        
#Establish connection to the server, first seeking it from command line arguments, then user input, then defaulting to localhost
if len(sys.argv) > 1:
    print("Server address taken to be "+sys.argv[1])
    address = sys.argv[1]
else:
    address = input("Address of Server: ")
try:
    if not address:
        print("STARTING SERVER ON LOCALHOST")
        host, port="localhost", 8000
    else:
        host, port = address.split(":")
except:
    print("Error Connecting to Server")
    print("Usage:", "host:port")
    print ("e.g.", "localhost:31425")
    exit()
cartolan_server = CartolanServer(GAME_MODES, DEFAULT_DIMENSIONS, DEFAULT_ORIGIN, localaddr=(host, int(port)))
print("Cartolan server started")
while True:
    cartolan_server.tick()
    sleep(0.01)


    