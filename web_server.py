'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com

Based on this example from AlexiK: https://stackoverflow.com/questions/32595130/javascript-html5-canvas-display-from-python-websocket-server
'''

from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer #, SimpleSSLWebSocketServer
from main_game import setup_simulation
#from live_visuals import ClientGameVisualisation, WebServerVisualisation
from live_visuals import WebServerVisualisation
from game import GameBeginner, GameRegular, GameAdvanced
from players_human import PlayerHuman
from players_heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter
from players_heuristical import PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter, PlayerRegularPirate
from players_heuristical import PlayerAdvancedExplorer, PlayerAdvancedTrader, PlayerAdvancedRouter, PlayerAdvancedPirate
#import zmq
#import zmq.auth
#from zmq.auth.thread import ThreadAuthenticator
import sys
#import os
import time
import random
import string
from threading import Thread

DEFAULT_PORT = 10000

DEFAULT_WIDTH = int(0.8*1366)
DEFAULT_HEIGHT = int(0.8*768)
DIMENSION_INCREMENT = 2

GAME_MODES = { 'Basic':{'game_type':GameBeginner, 'player_set':{"blue":PlayerBeginnerExplorer
                                                                   , "red":PlayerBeginnerTrader
                                                                   , "yellow":PlayerBeginnerRouter
#                                                                    , "green":PlayerBeginnerGenetic
                                                                   , "orange":PlayerBeginnerExplorer
                                                                      }}
              , 'Even':{'game_type':GameRegular, 'player_set':{
                                                                  "orange":PlayerRegularPirate
                                                                    , "blue":PlayerRegularExplorer
                                                                   , "red":PlayerRegularTrader
                                                                   , "yellow":PlayerRegularRouter
#                                                                    , "green":PlayerRegularGenetic
                                                                  }}
              , 'Rich':{'game_type':GameAdvanced, 'player_set':{
                                                                  "orange":PlayerAdvancedPirate
                                                                    , "blue":PlayerAdvancedExplorer
                                                                   , "red":PlayerAdvancedTrader
                                                                   , "yellow":PlayerAdvancedRouter
#                                                                    , "green":PlayerRegularGenetic
                                                                  }}
              }
DEFAULT_GAME_MODE = "Regular"
DEFAULT_LOCAL_PLAYERS = 1
DEFAULT_VIRTUAL_PLAYERS = 0
DEFAULT_REMOTE_PLAYERS = 2
DEFAULT_JOINING_PLAYERS = 1
#@TODO the below should be moved to the config file for all simulation and game versions
MOVEMENT_RULES = "initial"
EXPLORATION_RULES = "continuous"
MYTHICAL_CITY = True


next_game_id = 0
clients = []
client_visuals = {}
client_players = {}
games = {} #referenced by game IDs
client_games = {} #referenced by ClientSocket
#player_clients = {} #refernced by players
#player_games = {} #refereced by players
#Track new games as they're being initiated, based on sequential game IDs
new_game_queues = {} #referenced by game ID
new_game_types = {} #referenced by game ID
new_game_colours = {} #referenced by game ID
new_game_players = {} #referenced by game ID

def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class ClientSocket(WebSocket):
    '''Shares whole images of clients' play areas and receives input coordinates.
    
    Architecture:
    Client Side |    Server Side
    Web app    <-> Socket <-> Server   <->   Visualisation  <- Game
                                               /\                \/
                                              Player <- Adventurer/Agent
    
    '''
    INPUT_DELAY = 0.1 #delay time between checking for input, in seconds
    TIMEOUT_DELAY = 5 #delay time between heartbeats, after which loop will stop keeping the socket alive
    
    width = DEFAULT_WIDTH
    height = DEFAULT_HEIGHT
    global DIMENSION_INCREMENT
    
    coords_buffer = None
    text_buffer = None
    
    def get_text(self):
        output = self.text_buffer
        self.text_buffer = None
        return output
    
    def get_coords(self):
        output = self.coords_buffer
        self.coords_buffer = None
        return output
    
#    def init_ZMQ(self):
#        '''Set up a socket with a secure threadsafe message queue based on ZeroMQ: https://en.wikipedia.org/wiki/ZeroMQ
#        '''
#        file = sys.argv[0]
#        base_dir = os.path.dirname(file)
#        keys_dir = os.path.join(base_dir, 'certificates')
#        public_keys_dir = os.path.join(base_dir, 'public_keys')
#        secret_keys_dir = os.path.join(base_dir, 'private_keys')
#        self.context = zmq.Context()
#        self.socket = self.context.socket(zmq.DEALER)
#        client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")
#        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
#        self.socket.curve_publickey = client_public
#        self.socket.curve_secretkey = client_secret
#        server_public_file = os.path.join(public_keys_dir, "server.key")
#        server_public, _ = zmq.auth.load_certificate(server_public_file)
#        self.socket.curve_serverkey = server_public
#        self.width = "0"
#        self.height = "0"
    
    def join_game(self):
        '''Adds players to a queue, the first specifies setup, the last hosts in their thread.
        '''
        global next_game_id, clients, client_visuals, client_players, games
        global client_games
        global new_game_queues, new_game_types, new_game_colours, new_game_players
        game_id = None
        num_client_players = None
        in_queue = False
        #@TODO return to creating a new game if there are none available after the user returns input
        while not in_queue:
            if len(new_game_types) == 0:
                print("With no games queued up, configuring a new game.")
                game_id = next_game_id
                next_game_id += 1
                new_game_queues[game_id] = [self]
                print("Seeking game specification from newly joined client")
                prompt_text = "Please specify which mode of Cartolan you would like to host: "
                valid_options = []
                new_game_type = ""
                for game_type in GAME_MODES:
                    prompt_text += "'"+game_type+"'"
                    valid_options.append(game_type)
                    if len(valid_options) < len(GAME_MODES):
                        prompt_text += ", or "
                    else:
                        prompt_text += "."
                prompt_text += " (Hit enter for default "+DEFAULT_GAME_MODE+")"
                print("Prompting client at " +str(self.address)+ " with: " +prompt_text)
                self.sendMessage("PROMPT[00100]"+prompt_text)
                while not new_game_type in valid_options:
                    new_game_type = self.get_text()
                    if new_game_type:
                        if new_game_type == "BLANK":
                            print("Game type prompt was left blank, so assuming default mode of "+DEFAULT_GAME_MODE)
                            new_game_type = DEFAULT_GAME_MODE
                        elif not new_game_type in valid_options:
                            new_game_type = None
                            self.sendMessage("PROMPT[00100]"+prompt_text)
                    time.sleep(self.INPUT_DELAY)
                new_game_types[game_id] = new_game_type
                min_players = GAME_MODES[new_game_type]["game_type"].MIN_PLAYERS
                max_players = GAME_MODES[new_game_type]["game_type"].MAX_PLAYERS
                #Get remote user input about how many players they have at their end
                valid_options = [str(i) for i in range(1, max_players + 1)]
                prompt_text = ("Please specify how many players will play from this computer, between " +valid_options[0]+ " and " +valid_options[-1]+ "?")
                prompt_text += " (Hit enter for default "+str(DEFAULT_LOCAL_PLAYERS)+")"
                num_client_players = None
                print("Prompting client at " +str(self.address)+ " with: " +prompt_text)
                self.sendMessage("PROMPT[00100]"+prompt_text)
                while not str(num_client_players) in valid_options:
                    received_input = self.get_text()
                    if received_input:
                        if received_input.isnumeric():
                            num_client_players = int(received_input)
                            if not str(num_client_players) in valid_options:
                                num_client_players = None
                                self.sendMessage("PROMPT[00100]"+prompt_text)
                        else:
                            #For any input besides a number, assume the default
                            num_client_players = DEFAULT_LOCAL_PLAYERS
                    else:
                        time.sleep(self.INPUT_DELAY)
                #Get remote user input about how many computer players the game will have
                num_virtual_players = 0
                if num_client_players < max_players:
                    valid_options = [str(i) for i in range(0, max_players - num_client_players + 1)]
                    prompt_text = ("Please specify how many computer-controlled players will play, between " +valid_options[0]+ " and " +valid_options[-1]+ "?")
                    prompt_text += " (Hit enter for default "+str(DEFAULT_VIRTUAL_PLAYERS)+")"
                    print("Prompting client at " +str(self.address)+ " with: " +prompt_text)
                    self.sendMessage("PROMPT[00100]"+prompt_text)
                    num_virtual_players = None
                    while not str(num_virtual_players) in valid_options:
                        received_input = self.get_text()
                        if received_input:
                            if received_input.isnumeric():
                                num_virtual_players = int(received_input)
                                if not str(num_virtual_players) in valid_options:
                                    num_virtual_players = None
                                    self.sendMessage("PROMPT[00100]"+prompt_text)
                            else:
                                #For any input besides a number, assume the default
                                num_virtual_players = DEFAULT_VIRTUAL_PLAYERS
                        else:
                            time.sleep(self.INPUT_DELAY)
                #Get remote user input about how many other players they want in their game
                num_players = num_client_players + num_virtual_players
                #If there are still spaces available then allow for remote players
                if num_players < max_players:
                    valid_options = [str(i) for i in range(max(min_players - num_players, 0), max_players - num_players + 1)]
                    prompt_text = ("Please specify how many players from other computers will play, between "+str(valid_options[0])+" and " +str(valid_options[-1])+ "?")
                    prompt_text += " (Hit enter for default "+str(DEFAULT_REMOTE_PLAYERS)+")"
                    print("Prompting client at " +str(self.address)+ " with: " +prompt_text)
                    self.sendMessage("PROMPT[00100]"+prompt_text)
                    num_players = None
                    while not num_players in range(min_players, max_players + 1):
                        received_input = self.get_text()
                        if received_input:
                            if received_input.isnumeric():
                                num_players = num_client_players + num_virtual_players + int(received_input)
                                if not num_players in range(min_players, max_players + 1):
                                    num_players = None
                                    self.sendMessage("PROMPT[00100]"+prompt_text)
                            else:
                                #For any input besides a number, assume the default
                                num_players = num_client_players + num_virtual_players + DEFAULT_REMOTE_PLAYERS
                        else:
                            time.sleep(self.INPUT_DELAY)
                #randomly choose/order the player colours to fit this number, then assign a suitable number to this channel
                new_game_colours[game_id] = random.sample(GAME_MODES[new_game_type]["player_set"].keys(), num_players)
                client_players[self] = []
                new_game_players[game_id] = []
                for player_num in range(num_client_players):
                    player_colour = new_game_colours[game_id][player_num]
                    player = PlayerHuman(player_colour)
                    client_players[self].append(player)
                    new_game_players[game_id].append(player)
                for player_num in range(num_virtual_players):
                    player_colour = new_game_colours[game_id][num_client_players + player_num]
                    player = GAME_MODES[new_game_type]["player_set"][player_colour](player_colour)
                    client_players[self].append(player)
                    new_game_players[game_id].append(player)
                #Notify the player that they are in the queue and how many more players are awaited
                print("QUEUE[00100]"+str(len(new_game_players[game_id]))+"/"+str(num_players))
                self.sendMessage("QUEUE[00100]"+str(len(new_game_players[game_id]))+"/"+str(num_players))
                in_queue = True
            else:
                print("Trying to join this client to an existing game")
                #Try adding this client to an existing game, but then try another if that fills up while user is inputting
                #Select a (semi-)random game to join
                game_id = list(new_game_types.keys())[0]
                new_game_type = new_game_types[game_id]
                num_existing_clients = len(new_game_queues[game_id])
                #Seek input about how many players there are using this client
                min_players = GAME_MODES[new_game_type]["game_type"].MIN_PLAYERS
                max_players = GAME_MODES[new_game_type]["game_type"].MAX_PLAYERS
                num_players = len(new_game_colours[game_id])
                num_existing_players = len(new_game_players[game_id])
                num_spaces = num_players - num_existing_players
                print("The existing game has "+str(num_existing_clients)+" other clients connected")
                valid_options = [str(i) for i in range(1, num_spaces + 1)]
                prompt_text = ("The current game has " +str(num_existing_players) +"/"
                               +str(num_players)+" players. Please specify how many players will play from this computer, between 1 and " 
                               +str(num_spaces)+ "?")
                prompt_text += " (Hit enter for default "+str(DEFAULT_JOINING_PLAYERS)+")"
                num_client_players = None
                print("Prompting client at " +str(self.address)+ " with: " +prompt_text)
                self.sendMessage("PROMPT[00100]"+prompt_text)
                while not num_client_players in range(1, max_players + 1):
                    received_input = self.get_text()
                    if received_input:
                        if received_input.isnumeric():
                            num_client_players = int(received_input)
                            if not num_client_players in range(1, max_players + 1):
                                num_client_players = None
                                self.sendMessage("PROMPT[00100]"+prompt_text)
                        else:
                            #For any input besides a number, assume the default
                            num_client_players = DEFAULT_JOINING_PLAYERS
                    else:
                        time.sleep(self.INPUT_DELAY)
                #Now blocking is done, try to reserve a place in this game
                #Check whether the number of spaces for this game has changed and start again if so
                num_players = len(new_game_colours[game_id])
                num_existing_players = len(new_game_players[game_id])
                num_spaces = num_players - num_existing_players
                if num_client_players > num_spaces:
                    continue
                new_game_queues[game_id].append(self)
                
                #Assign colours to the newly joined players
                client_players[self] = []
                for player_num in range(num_existing_players, num_existing_players + num_client_players):
                    player_colour = new_game_colours[game_id][player_num]
                    player = PlayerHuman(player_colour)
                    client_players[self].append(player)
                    new_game_players[game_id].append(player)
                #Notify the player that they are in the queue and how many more players are awaited
                print("QUEUE[00100]"+str(num_existing_players + num_client_players)+"/"+str(num_players))
                for client in new_game_queues[game_id]:
                    client.sendMessage("QUEUE[00100]"+str(num_existing_players + num_client_players)+"/"+str(num_players))
                in_queue = True
            
            #If this client's game is now full then start it off
            num_players = len(new_game_colours[game_id])
            num_existing_players = len(new_game_players[game_id])
            if num_existing_players == num_players:
                print("Enough players have joined, so STARTING GAME #"+str(game_id))
                random.shuffle(new_game_players[game_id])
                self.game = setup_simulation(new_game_players[game_id]
                                     , GAME_MODES[new_game_type]["game_type"]
                                     , MOVEMENT_RULES
                                     , EXPLORATION_RULES
                                     , MYTHICAL_CITY)
                
                #Move the game's lookups into the active list and clean up
                games[game_id] = {"player_colours":new_game_colours.pop(game_id)
                                    , "players":new_game_players.pop(game_id)
                                    , "game_type":new_game_types.pop(game_id)
                                    , "clients":new_game_queues.pop(game_id)
                                    }                    
                
                #Establish dimensions for the play area, based on the setup
                #@TODO this code is repeated several times in different places, functionalise it
#                min_longitude, max_longitude = 0, 0
#                min_latitude, max_latitude = 0, 0
#                for longitude in self.game.play_area:
#                    if longitude < min_longitude:
#                        min_longitude = longitude
#                    elif longitude > max_longitude:
#                        max_longitude = longitude
#                    for latitude in self.game.play_area[longitude]:
#                        if latitude < min_latitude:
#                            min_latitude = latitude
#                        elif latitude > max_latitude:
#                            max_latitude = latitude
#                origin = [-min_longitude + DIMENSION_INCREMENT
#                          , -min_latitude + DIMENSION_INCREMENT
#                          ]
#                dimensions = [max_longitude + origin[0] + DIMENSION_INCREMENT
#                              , max_latitude + origin[1] + DIMENSION_INCREMENT
#                              ]
                origin = [1,1]
                dimensions = [3,3]
                clients = games[game_id]["clients"]
                visuals = []
                for client in clients:
                    #create game visualisation corresponding to each client's window resolution
                    game_vis = WebServerVisualisation(self.game, dimensions, origin, visuals, client, client.width, client.height)
                    print("Visual created for client at "+ str(client.address)+ " with dimensions: "+str(client.width)+"x"+str(client.height))
                    client_visuals[client] = game_vis
                    visuals.append(game_vis)
                    for player in client_players[client]:
                        player.connect_gui(game_vis)
                
                #start game in this thread including all the client visuals (so that the players created here are available to just one thread)
                self.game.game_started = True
                self.game.turn = 0
                self.game.game_over = False
                while not self.game.game_over:
                    self.game.turn += 1
                    self.game.game_over = self.game.play_round()
                
                #Inform all clients that the game has ended
                win_message = self.game.winning_player.colour+" player won the game"
                if self.game.wealth_difference >= self.game.game_winning_difference:
                    win_message += " by buying a global monopoly with their extra wealth"
                else:
                    win_message += " as the richest when the world map was completed"
                win_message +=  " (refresh to play again)"
                for client in games[game_id]["clients"]:
                    print("Closing game for client: "+str(client.address))
                    game_vis = client_visuals[client]
                    game_vis.draw_play_area()
                    game_vis.draw_scores()
                    game_vis.draw_tokens()
                    game_vis.current_player_colour = self.game.winning_player.colour
                    game_vis.give_prompt(win_message)
                    game_vis.update_web_display()
                game_vis.close()
                
                #Tidy up and indicate that a game was joined and completed, and allow the thread to terminate
#                    for player in games[game_id]["players"]:
#                        player_clients.pop(player)
                games.pop(game_id)
                return True
            #keep connection alive until a game is joined
            connection_alive = True
            self.connection_confirmed = False
            self.sendMessage("PING[00100]")
            while connection_alive:
                connection_alive = self.connection_confirmed
                self.connection_confirmed = False
                self.sendMessage("PING[00100]")
                time.sleep(self.TIMEOUT_DELAY)
            print(self.address, " timed out")
            
    
    #@TODO decide whether to collect input from this socket via recv or the below
    def handleMessage(self):
        '''Distinguish whether this message is an initiation or continuation of a game.
        ''' 
        message = str(self.data)
        protocode, msg = message.split("[00100]")
        if protocode == ("START"):
           print("START...ing a new game connection")
#           self.socket.setsockopt(zmq.IDENTITY, str(msg))
#           self.socket.connect("tcp://LOCALHOST:80")
#           #Check whether there are enough players in the queue for a game,
#           #start one in a Thread if so
#           #@TODO join specifically the game that has been asked for
           self.width, self.height = [int(coord) for coord in msg.split("[55555]")]
           print("Received width: ", self.width," and height: ", self.height)
           Thread(target=self.join_game).start()
        elif protocode == ("PONG"):
            print("Client responded to ping")
            self.connection_confirmed = True
        elif protocode == ("TEXT"):
#           print("TEXT... "+msg)
           if not msg == "":
               self.text_buffer = msg
#           msg = str(msg)
#           ident, mdata = msg.split("[11111]")
#           msg = ('%sSPLIT%s' % (ident, mdata))
##           self.socket.send(str(msg))
        elif protocode == ("COORDS"):
           input_coords = msg.split("[66666]")
           print("Click coordinate Input received from client... "+", ".join(input_coords))
           print(time.strftime('%Y-%m-%d %H:%M %Z', time.gmtime(time.time()))) #timestamp
           try:
               if len(input_coords) == 2:
                   self.coords_buffer = []
                   for coord in input_coords:
                       self.coords_buffer.append(int(coord))
           except:
               self.coords_buffer = None
               print("The client response could not be converted into a pair of integer coordinates.")
#           msg = str(msg)
#           ident, mdata = msg.split("[11111]")
#           msg = ('%sSPLIT%s' % (ident, mdata))
##           self.socket.send(str(msg))

    def handleConnected(self):
        '''On initial connection, establish client details
        '''
        print(self.address, 'connected')
        clients.append(self)
        
#        self.init_ZMQ()
#        channel.setup()


    def handleClose(self):
        '''Gracefully remove a client
        '''
        clients.pop(self)
        print (self.address, 'closed')
        for client in clients:
            client.sendMessage(self.address[0] + u' - disconnected')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("Server port taken to be "+sys.argv[1])
        port = sys.argv[1]
    else:
        port = DEFAULT_PORT
    server = SimpleWebSocketServer('', port, ClientSocket)
    print("Starting server on port: ", port)
    server.serveforever()