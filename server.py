import PodSixNet.Channel
import PodSixNet.Server
from players_heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter, PlayerRegularPirate, PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter
from game import GameBeginner, GameRegular
from time import sleep
import random

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
    
class ClientChannel(PodSixNet.Channel.Channel):
    '''The receiving methods for messages from clients for a pygame-based server
    '''
    def Network(self, data):
        print(data)
        
    def Network_input(self, data):
        '''Receiving method for plain "input" messages from clients
        '''
        self._server.input_buffer[self] = data["input"]
        
    def Network_place_tiles(self, data):
        '''Relays "place_tiles" messages from the current host to client games
        '''
        self._server.relay_data(self, data)
        
    def Network_move_tokens(self, data):
        '''Relays "move_tokens" messages from the current host to client games
        '''
        self._server.relay_data(self, data)
        
    def Network_update_scores(self, data):
        '''Relays "update_scores" messages from the current host to client games
        '''
        self._server.relay_data(self, data)
    
    def Network_prompt(self, data):
        '''Relays "move_tokens" messages from the current host to client games
        '''
        self._server.relay_data(self, data)
    
    def Network_new_turn(self, data):
        '''Relays "new_turn" messages from the current host to client games
        '''
        self._server.relay_data(self, data)
    
    def Network_declare_win(self, data):
        '''Relays "new_turn" messages from the current host to client games
        '''
        self._server.relay_data(self, data)
        
#    def Network_quit(self, data):
#        '''The receiving method for "quit" messages from clients
#        '''
#        quitting_player_colour = data["player_colour"]
##        self._server.player_quits(self, quitting_player_colour)
#        self.player_colours.remove(quitting_player_colour)
#        if len(self.player_colours):
#            self.Close()
    
#    def Close(self):
#        '''Closes the channel to the client
#        '''
#        self._server.close()

class CartolanServer(PodSixNet.Server.Server):
    '''A pygame-based server hosting a game and communicating with client visuals.
    
    Architecture:
    Server Side |    Client Side
    Server   <->   Visualisation  <- Game
                    /\                \/
                    Player <- Adventurer/Agent
    
    Client games alternate in progressing play (so as to avoid latency in uncovering tiles)
    Server synchronises client games, and the tile piles across them
    Where there are consistency checks across clients, the current player serves as master
    '''
    channelClass = ClientChannel
    WAIT_DURATION = 1
    TIMEOUT_DURATION = 60
    
    def __init__(self, game_modes, dimensions, origin, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)
        self.game_modes = game_modes
        self.dimensions = dimensions
        self.orgin = origin
        self.games = []
        self.channel_games = {}
        self.channel_players = {}
        self.input_buffer = {}
        #Track the latest game as it's being initiated
        self.next_game_type = None
        self.next_num_players = None
        self.queue = []
        self.next_player_channels = {}
    
    #@TODO allow players to join a game, replacing a virtual player 
    def Connected(self, channel, addr):
        '''Allocates players to games
        '''
        print('new connection: ', channel.addr)
#        channel.setup()
        self.input_buffer[channel] = None
        if self.next_game_type == None:
            self.queue.append(channel)
            print("Seeking game specification from newly joined client")
            prompt_text = "Please specify which mode of Cartolan you would like to host: "
            valid_options = []
            self.next_game_type = ""
            for game_type in self.game_modes:
                prompt_text += "'"+game_type+"', or "
                valid_options.append(game_type)
            print("Prompting channel at " +channel.addr[0]+ " with: " +prompt_text)
            channel.Send({"action":"input", "input_prompt":prompt_text, "valid_options":valid_options})
            while not self.next_game_type in valid_options:
                self.next_game_type = self.remote_input(channel)
            self.min_players = self.game_modes[game_type]["game_type"].MIN_PLAYERS
            self.max_players = self.game_modes[game_type]["game_type"].MAX_PLAYERS
            valid_options = [str(i) for i in range(1, self.max_players)]
            prompt_text = ("Please specify how many players will play from this computer, between 1 and " +str(self.max_players - 1)+ "?")
            num_client_players = None
            print("Prompting channel at " +channel.addr[0]+ " with: " +prompt_text)
            channel.Send({"action":"input", "input_prompt":prompt_text, "valid_options":valid_options})
            while not num_client_players in range(1, self.max_players):
                received_input = self.remote_input(channel)
                if received_input:
                    num_client_players = int(received_input)
            valid_options = [str(i) for i in range(1, self.max_players - num_client_players + 1)]
            prompt_text = ("Please specify how many other players will play, between 1 and " +str(self.max_players - num_client_players)+ "?")
            num_players = None
            print("Prompting channel at " +channel.addr[0]+ " with: " +prompt_text)
            channel.Send({"action":"input", "input_prompt":prompt_text, "valid_options":valid_options})
            while not num_players in range(self.min_players, self.max_players + 1):
                received_input = self.remote_input(channel)
                if received_input:
                    num_players = num_client_players + int(received_input)
            self.next_num_players = num_players
            #randomly choose/order the player colours to fit this number, then assign a suitable number to this channel
            self.next_player_colours = random.sample(self.game_modes[game_type]["player_set"].keys(), self.next_num_players)
            self.channel_players[channel] = []
            for player_num in range(num_client_players):
                player_colour = self.next_player_colours[player_num]
                self.channel_players[channel].append(player_colour)
                self.next_player_channels[player_colour] = channel
        else:
            #Add this client to the game that's being set up
            self.queue.append(channel)
            num_existing_players = len(self.next_player_channels)
            valid_options = [str(i) for i in range(1, self.next_num_players - num_existing_players + 1)]
            prompt_text = ("The current game has " +str(num_existing_players) +"/"
                           +str(self.next_num_players)+" players. Please specify how many players will play from this computer, between 1 and " 
                           +str(self.next_num_players - len(self.next_player_channels))+ "?")
            num_client_players = None
            print("Prompting channel at " +channel.addr[0]+ " with: " +prompt_text)
            channel.Send({"action":"input", "input_prompt":prompt_text, "valid_options":valid_options})
            while not num_client_players in range(1, self.max_players + 1):
                received_input = self.remote_input(channel)
                if received_input:
                    num_client_players = int(received_input)
            #Assign colours to the newly joined players
            self.channel_players[channel] = []
            for player_num in range(num_existing_players, num_existing_players + num_client_players):
                player_colour = self.next_player_colours[player_num]
                self.channel_players[channel].append(player_colour)
                self.next_player_channels[player_colour] = channel
            if len(self.next_player_channels) == self.next_num_players:
                #specify initial adventurer locations for the given players
                adventurers_json = {}
                random.shuffle(self.next_player_colours)
                current_player_colour = self.next_player_colours[0]
                for player_colour in self.next_player_channels:
                    adventurers_json[player_colour] = INITIAL_ADVENTURERS
                self.games.append({"player_channels":self.next_player_channels})
                for chan in self.queue:
                    chan.Send({"action": "start_game"
                        ,"player_colours":self.next_player_colours
                        , "local_player_colours":self.channel_players[chan]
                        , "game_type":self.next_game_type
                        , "initial_tiles":INITIAL_TILES
                        , "initial_adventurers":adventurers_json
                        , "current_player_colour":current_player_colour
                        })
                    self.channel_games[chan] = {}
                    self.channel_games[chan]["game_id"] = len(self.games) - 1                
                # Clean up before the next game is constructed
                self.next_num_players = None
                self.next_player_colours = None
                self.next_game_type = None
                self.next_player_channels = {}
                self.queue = []
    
#    def close(self):
#        '''Passes on close instruction to each of the clients
#        
#        Parameters:    
#        game_id should be an integer referencing a game instance in a List
#        '''
#        try:
#            player_channels = self.games[game_id]["player_channels"]
#            for channel in set(player_channels.values()):
#                if channel:
#                    channel.Send({"action":"close"})
#                else:
#                    # Free up the local game slot if this was the local game
#                    self.local_game = False
#        except:
#            pass
    
    def relay_data(self, host_channel, data):
        '''Relays updated game state from the channel that is currently hosting the game
        
        Arguments:
        host_channel expects a PodSixNet/Cartolan ClientChannel
        data expects a dict in the format of a PodSixNet message for a ConnectionListener
        '''
        game_id = self.channel_games[host_channel]["game_id"]
        player_channels = self.games[game_id]["player_channels"]
        for channel in set(player_channels.values()):
            if not channel == host_channel:
                print("Sending a message to "+str(channel.addr[0]))
                channel.Send(data)
    
    def remote_input(self, channel):
        '''Seeks input from remote players (mostly in game setup)
        '''
        #collect and return any input left in the buffer
        sleep(0.01)
        self.Pump()
        input_text = self.input_buffer[channel]
        self.input_buffer[channel] = None
        return input_text
    
#    def player_quits(self, channel, player_colour):
#        '''When a player quits an active game, replace them with a virtual player.
#        '''
#        game_vis = self.games[game_id]["game_vis"]
#        player_channels = self.games[game_id]["player_channels"]
#        player_channels[player_colour] = self.game_modes[game_vis.game.__class__]["player_sets"][player_colour](player_colour)
    
    def tick(self):
        '''Checks the games for messages and handles appropriately
        '''
#        # Check for any player actions or quit messages
#        for game_id in self.games:
#            game = self.games[game_id]["game"]
        
        self.Pump()
                                
        
print("STARTING SERVER ON LOCALHOST")
cartolan_server = CartolanServer(GAME_MODES, DEFAULT_DIMENSIONS, DEFAULT_ORIGIN, localaddr=('localhost', 8000))
while True:
    cartolan_server.tick()
    sleep(0.01)


    