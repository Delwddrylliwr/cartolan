import PodSixNet.Channel
import PodSixNet.Server
from players_human import PlayerHuman
from players_heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter, PlayerRegularPirate, PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter
from game import GameBeginner, GameRegular
from visuals import GameVisualisation, ClientGameVisualisation
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

class ClientChannel(PodSixNet.Channel.Channel):
    '''The receiving methods for messages from clients for a pygame-based server
    '''
    def Network(self, data):
        print(data)
        
    def setup(self):
        '''The receiving method for "setup" messages from clients, to get the number of players
        '''
        self.player_colours = player_colours
    
    def Network_input(self, data):
        '''Receiving method for plain 'input' messages from clients
        '''
        self._server.input_buffer = data["input"]
        
    def Network_move(self, data):
        '''The receiving method for "move" messages from clients
        '''
        self.generic_move_or_action(data)
    
    def Network_buy(self, data):
        '''The receiving method for "buy" messages from clients
        '''
        self.generic_move_or_action(data)
    
    def Network_attack(self, data):
        '''The receiving method for "attack" messages from clients
        '''
        self.generic_move_or_action(data)
        
    #@TODO may want to differentiate client instructions more deeply in future, if multiple moves are to be offered at the same time    
    def generic_move_or_action(self, data):
        #deconsolidate all of the data from the dictionary
        longitude = data["longitude"]
        latitude = data["latitude"]
        
        player_colour = data["player_colour"]
        adventurer_num = data["adventurer_num"]
        
#        if not self.gameid == data["gameid"]: #id of game given by server at start of game
            #@TODO handle a message from the wrong game for this channel
            
        #tells server to pass coordinates on to the waiting game
        self._server.pass_coordinates(longitude, latitude, self.gameid, player_colour, adventurer_num)
    
    def Network_quit(self, data):
        '''The receiving method for "quit" messages from clients
        '''
        quitting_player_colour = data["player_colour"]
        self._server.player_quits(self.game_id, quitting_player_colour)
        self.player_colours.remove(quitting_player_colour)
        if len(self.player_colours):
            self.Close()
    
    def Close(self):
        '''Closes the channel to the client
        '''
        self._server.close(self.gameid)

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
        self.games = {}
        self.input_buffer = {}
        #Track the latest game as it's being initiated
        self.next_game_type = None
        self.next_num_players = None
        self.next_player_channels = {}
    
    #@TODO allow players to join a game, replacing a virtual player 
    def Connected(self, channel, addr):
        '''Allocates players to games
        '''
        print('new connection:', channel)
        channel.setup()
        if self.next_game_type == None:
            # Seek game specification from newly joined client
            prompt_text = "Please specify which mode of Cartolan you would like to host: "
            self.next_game_type = ""
            for game_type in self.game_modes:
                prompt_text += "'"+game_type+"', or "
            channel.send({"action":"prompt", "colour":"block", "prompt_text":prompt_text})
            while not self.next_game_type in self.game_modes:
                self.next_game_type = self.remote_input(channel)
            self.min_players = self.game_modes[game_type]["game_type"].MIN_PLAYERS
            self.max_players = self.game_modes[game_type]["game_type"].MAX_PLAYERS
            prompt_text = ("Please specify how many players will play from this computer, between 1 and " +str(self.max_players)+ "?")
            channel.send({"action":"prompt", "colour":"block", "prompt_text":prompt_text})
            num_client_players = None
            while not num_client_players in range(1, self.max_players + 1):
                num_client_players = int(self.remote_input(channel))
            prompt_text("Please specify how many other players will play, between 1 and " +str(self.max_players - num_client_players)+ "?")
            channel.send({"action":"prompt", "colour":"black", "prompt_text":prompt_text})
            num_players = None
            while not num_players in range(self.min_players, self.max_players + 1):
                num_players = num_client_players + int(self.remote_input(channel))
            self.next_num_players = num_players
            #randomly choose/order the player colours to fit this number, then assign a suitable number to this channel
            self.next_player_colours = random.sample(self.game_modes[game_type]["player_set"], self.next_num_players)
            for player_num in range(num_client_players):
                player_colour = self.next_player_colours.pop()
                channel.player_colours.append(player_colour)
                self.next_player_channels[player_colour] = channel
        else:
            #Add this client to the game that's being set up
            self.queue.append(channel)
            prompt_text = ("The current game has " +str(len(self.next_player_channels)) +"/"
                           +str(self.next_num_players)+" players. Please specify how many players will play from this computer, between 1 and " 
                           +str(self.next_num_players - len(self.next_player_channels))+ "?")
            channel.send({"action":"prompt", "colour":"block", "prompt_text":prompt_text})
            num_client_players = None
            while not num_client_players in range(1, self.max_players + 1):
                num_client_players = int(self.remote_input(channel))
            #Assign colours to the newly joined players
            for player_num in range(num_client_players):
                player_colour = self.next_player_colours.pop()
                channel.player_colours.append(player_colour)
                self.next_player_channels[player_colour] = channel
            if len(self.next_player_channels) == self.next_num_players:
                #@TODO specify initial tile placement
                #@TODO specify initial adventurer locations
                self.games.append({"player_channels":self.next_game_players
                    , "play_area_sizes":None, "adventurers":None, "agents":None})
                for chan in self.queue:
                    chan.Send({"action": "start_game","player_colours":self.next_player_channels.keys()
                        , "local_player_colours":chan.player_colours, "gameid": len(self.games) - 1
                        , "game_type":self.next_game_type})
                    chan.game_id = len(self.games) - 1
                    self.next_num_players = None
                    self.next_player_channels = None
                    self.next_player_colours = None
                    self.next_game_type = None
    
    def close(self, game_id):
        '''Passes on close instruction to each of the clients
        
        Parameters:    
        game_id should be an integer referencing a game instance in a List
        '''
        try:
            player_channels = self.games[game_id]["player_channels"]
            for channel in set(player_channels.values()):
                if channel:
                    channel.Send({"action":"close"})
                else:
                    # Free up the local game slot if this was the local game
                    self.local_game = False
        except:
            pass
    
    def pass_coordinates(self, longitude, latitude, game_id, player_colour, adventurer_num):
        '''Checks that the game is awaiting input from a player, and makes it available.
        
        Arguments:
        longitude an Int giving one of the grid coordinates
        latitude an Int giving one of the grid coordinates
        game_id a hexadecimal string uniquely identifying
        player_colour a string identifying the player within the game, by their colour
        adventurer_number an Int identifying the Adventurer token for which the player is submitting a movement/action
        '''
        if not self.games[game_id]["current_player_colour"] == player_colour:
            return False
        else:
            self.games[game_id]["current_player_input"] = [longitude, latitude]
            return True
    
    def give_prompt(self, game, player_colour, prompt):
        '''Passes a prompt for the relevant remote players 
        '''
        channel = self.games[game.game_id]["player_channels"][player_colour]
        channel.send({"action":"prompt", "player_colour":player_colour, "prompt_text":prompt})
    
    def clear_prompt(self, game, player_colour):
        '''Clears prompts for the relevant remote player
        '''
        channel = self.games[game.game_id]["player_channels"][player_colour]
        channel.send({"action":"prompt", "player_colour":player_colour})
    
    def remote_input(self, channel):
        '''Allows players to submit text input
        '''
        #collect and return any input left in the buffer
        input_text = self.input_buffer[channel]
        self.input_buffer[channel] = None
        return input_text
    
    def remote_input_coords(self, adventurer):
        '''Allows Players to submit coordinates directly
        '''
        #identify game and player through adventurer
        game_id = adventurer.game.game_id
        player = adventurer.player
        #collect and return any coordinates left for the game by that player's remote version
        if self.games[game_id]["current_player_colour"] == player.player_colour:
            input_coords = self.games[game_id]["current_player_input"]
            #Record that the coordinates have been collected
            self.games[game_id]["current_player_input"] = None
            return input_coords
        else:
            return None
    
    def player_quits(self, game_id, player_colour):
        '''When a player quits an active game, replace them with a virtual player.
        '''
        game_vis = self.games[game_id]["game_vis"]
        player_channels = self.games[game_id]["player_channels"]
        player_channels[player_colour] = self.game_modes[game_vis.game.__class__]["player_sets"][player_colour](player_colour)
    
    def tick(self):
        '''Checks the games for messages and handles appropriately
        '''
        # Check for any player actions or quit messages
        for game_id in self.games:
            game = games[game_id]["game"]
        
        self.Pump()
                                
        
print("STARTING SERVER ON LOCALHOST")
cartolan_server = CartolanServer(GAME_MODES, DEFAULT_DIMENSIONS, DEFAULT_ORIGIN)
while True:
    cartolan_server.tick()
    sleep(0.01)


    