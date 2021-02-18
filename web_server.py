'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com

Based on this example from AlexiK: https://stackoverflow.com/questions/32595130/javascript-html5-canvas-display-from-python-websocket-server
'''

from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer, SimpleSSLWebSocketServer
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
import sys
import os
import random
import pygame
from pygame.locals import *
import base64
import string
from threading import Thread

client_visuals = {}
client_players = {}
games = {}
channel_games = {}
#Track the latest game as it's being initiated
current_game_queue = []
next_game_type = None
next_num_players = None
next_player_channels = {}
next_virtual_players = []

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
    def init_ZMQ(self):
        '''Set up a socket with a secure threadsafe message queue based on ZeroMQ: https://en.wikipedia.org/wiki/ZeroMQ
        '''
        file = sys.argv[0]
        base_dir = os.path.dirname(file)
        keys_dir = os.path.join(base_dir, 'certificates')
        public_keys_dir = os.path.join(base_dir, 'public_keys')
        secret_keys_dir = os.path.join(base_dir, 'private_keys')
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
        self.socket.curve_publickey = client_public
        self.socket.curve_secretkey = client_secret
        server_public_file = os.path.join(public_keys_dir, "server.key")
        server_public, _ = zmq.auth.load_certificate(server_public_file)
        self.socket.curve_serverkey = server_public
        self.width = "0"
        self.height = "0"
    
    def join_game(self):
        '''Adds players to a queue, with the first specifying setup, and starts a game when enough join.
        '''
        try:
            if next_game_type == None:
                current_game_queue.append(channel)
                print("Seeking game specification from newly joined client")
                prompt_text = "Please specify which mode of Cartolan you would like to host: "
                valid_options = []
                self.next_game_type = ""
                for game_type in self.game_modes:
                    prompt_text += "'"+game_type+"', or "
                    valid_options.append(game_type)
                print("Prompting channel at " +channel.addr[0]+ " with: " +prompt_text)
                self.socket.send({"action":"input", "input_prompt":prompt_text, "valid_options":valid_options})
                while not next_game_type in valid_options:
                    next_game_type = self.socket.recv()
                min_players = self.game_modes[next_game_type]["game_type"].MIN_PLAYERS
                max_players = self.game_modes[next_game_type]["game_type"].MAX_PLAYERS
                #Get remote user input about how many players they have at their end
                valid_options = [str(i) for i in range(1, max_players)]
                prompt_text = ("Please specify how many players will play from this computer, between " +valid_options[0]+ " and " +valid_options[-1]+ "?")
                num_client_players = None
                print("Prompting channel at " +channel.addr[0]+ " with: " +prompt_text)
                self.socket.send({"action":"input", "input_prompt":prompt_text, "valid_options":valid_options})
                while not str(num_client_players) in valid_options:
                    received_input = self.socket.recv()
                    if received_input:
                        num_client_players = int(received_input)
                #Get remote user input about how many computer players they are to host
                valid_options = [str(i) for i in range(0, max_players - num_client_players)]
                prompt_text = ("Please specify how many computer players will play, between " +valid_options[0]+ " and " +valid_options[-1]+ "?")
                num_virtual_players = None
                print("Prompting channel at " +channel.addr[0]+ " with: " +prompt_text)
                self.socket.send({"action":"input", "input_prompt":prompt_text, "valid_options":valid_options})
                while not str(num_virtual_players) in valid_options:
                    received_input = self.remote_input(channel)
                    if received_input:
                        num_virtual_players = int(received_input)
                #Get remote user input about how many other players they want in their game
                valid_options = [str(i) for i in range(1, max_players - num_client_players - num_virtual_players + 1)]
                prompt_text = ("Please specify how many other players will play, between 1 and " +str(max_players - num_client_players - num_virtual_players)+ "?")
                num_players = None
                print("Prompting channel at " +self.address+ " with: " +prompt_text)
                self.socket.send({"action":"input", "input_prompt":prompt_text, "valid_options":valid_options})
                while not num_players in range(min_players, max_players + 1):
                    received_input = self.socket.recv()
                    if received_input:
                        num_players = num_client_players + num_virtual_players + int(received_input)
                next_num_players = num_players
                #randomly choose/order the player colours to fit this number, then assign a suitable number to this channel
                next_player_colours = random.sample(game_modes[next_game_type]["player_set"].keys(), next_num_players)
                client_players[self] = []
                for player_num in range(num_client_players):
                    player_colour = next_player_colours[player_num]
                    client_players[self].append(player_colour)
                    next_player_channels[player_colour] = self
                next_virtual_players = []
                for player_num in range(num_virtual_players):
                    player_colour = next_player_colours[num_client_players + player_num]
                    client_players[self].append(player_colour)
                    next_player_channels[player_colour] = self
                    virtual_players.append(player_colour)
            else:
                #Add this client to the game that's being set up
                next_game_queue.append(self)
                num_existing_players = len(next_player_channels)
                valid_options = [str(i) for i in range(1, next_num_players - num_existing_players + 1)]
                prompt_text = ("The current game has " +str(num_existing_players) +"/"
                               +str(next_num_players)+" players. Please specify how many players will play from this computer, between 1 and " 
                               +str(next_num_players - len(next_player_channels))+ "?")
                num_client_players = None
                print("Prompting channel at " +channel.addr[0]+ " with: " +prompt_text)
                channel.Send({"action":"input", "input_prompt":prompt_text, "valid_options":valid_options})
                while not num_client_players in range(1, max_players + 1):
                    received_input = self.socket.recv()
                    if received_input:
                        num_client_players = int(received_input)
                #Assign colours to the newly joined players
                client_players[self] = []
                for player_num in range(num_existing_players, num_existing_players + num_client_players):
                    player_colour = next_player_colours[player_num]
                    client_players[self].append(player_colour)
                    next_player_channels[player_colour] = self
                if len(next_player_channels) == next_num_players:
                    #specify initial adventurer locations for the given players
                    adventurers_json = {}
                    random.shuffle(next_player_colours)
                    current_player_colour = next_player_colours[0]
                    for player_colour in next_player_channels:
                        adventurers_json[player_colour] = INITIAL_ADVENTURERS
                    games.append({"player_channels":next_player_channels})
                    for client in next_game_queue:
                        client.socket.send({"action": "start_game"
                            ,"player_colours":next_player_colours
                            , "local_player_colours":client_players[socket]
                            , "virtual_players":next_virtual_players
                            , "game_type":next_game_type
                            , "initial_tiles":INITIAL_TILES
                            , "initial_adventurers":adventurers_json
                            , "current_player_colour":current_player_colour
                            })
                        client_games[client] = {}
                        client_games[client]["game_id"] = len(games) - 1                
                    # Clean up before the next game is constructed
                    next_num_players = None
                    next_player_colours = None
                    next_game_type = None
                    next_player_channels = {}
                    queue = []
        except Exception as e:
           print (e)


    def start_game(self):
        '''Create a visualisation (and a game if needed), share images of the pygame canvas and receive input coordinates.
        '''
        self.local_player_colours = data["local_player_colours"]
        print("Setting up the local version of the game:")
        print(data)
        game_type = GAME_MODES[data["game_type"]]["game_type"] #needed to identify the class of other elements like Adventurers and Agents
        self.players = [] #to capture order of play
        self.player_colours = {} #to access Player objects quickly based on colour
        self.virtual_players = data["virtual_players"]
        for player_colour in data["player_colours"]:
            if player_colour in self.virtual_players:
                player = self.GAME_MODES[data["game_type"]]["player_set"][player_colour](player_colour)
            else:
                player = PlayerHuman(player_colour)
            self.players.append(player)
            self.player_colours[player_colour] = player 
        
        game = game_type(self.players)
        self.game = game
        #Informing players of this game visualisation
        for player in self.players:
            player.games[game.game_id]["game_vis"] = self
            self.shared_tokens["adventurers"][player.colour] = []
            self.shared_tokens["agents"][player.colour] = []
            self.shared_scores[player.colour] = 0
        print("Building the tile piles")
        game.setup_tile_pile("water")
        if isinstance(game, GameRegular):
            game.setup_tile_pile("land")
            game.tile_piles["land"].tiles.append(MythicalTileRegular(game))
        print("Placing the initial tiles and adventurers")
        self.Network_place_tiles({"tiles":data["initial_tiles"]})
        #@TODO adapt to use the Network_move_tokens method
        initial_adventurers = data["initial_adventurers"] #expects a dict of colours and list of 2-tuples giving the placement(s) of initial Adventurers for each player
        if not len(self.players) == len(initial_adventurers):
            raise Exception("Player attributes from Host have different lengths")
        for player in self.players:
            for adventurer_location in initial_adventurers[player.colour]:
                longitude = game.play_area.get(int(adventurer_location[0]))
                if longitude:
                    adventurer_tile = longitude.get(int(adventurer_location[1]))
                    if adventurer_tile:
                        adventurer = game_type.ADVENTURER_TYPE(game, player, adventurer_tile)
                    else:
                        raise Exception("Server tried to place on Adventurer where there was no tile")
        
        print("With proxy game and players set up, continuing the startup of a normal visual")
        min_longitude, max_longitude = 0, 0
        min_latitude, max_latitude = 0, 0
        for longitude in self.game.play_area:
            if longitude < min_longitude:
                min_longitude = longitude
            elif longitude > max_longitude:
                max_longitude = longitude
            for latitude in self.game.play_area[longitude]:
                if latitude < min_latitude:
                    min_latitude = latitude
                elif latitude > max_latitude:
                    max_latitude = latitude
        origin = [-min_longitude + self.DIMENSION_INCREMENT
                  , -min_latitude + self.DIMENSION_INCREMENT
                  ]
        dimensions = [max_longitude + origin[0] + self.DIMENSION_INCREMENT
                      , max_latitude + origin[1] + self.DIMENSION_INCREMENT
                      ]
        super().__init__(game, dimensions, origin)
        
        #keep track of whether the game is active or waiting for the server to collect enough players
        self.game.turn = 1
        self.current_player_colour = data["current_player_colour"]
        if self.current_player_colour in self.local_player_colours:
            self.local_player_turn = True
        else:
            self.local_player_turn = False
        
        print("Waiting and watching for it to be a local player's turn, before switching to local control and execution of the game")
        self.game.game_over = False
        while not self.game.game_over:
            #distinguish between local and remote play and hand control of the game to the remote player's computer as needed, through the server    
            while not self.local_player_turn:
                self.update()
                sleep(self.UPDATE_DELAY)
            
            print("Switching to local execution of the game, now it is a local player's turn")
            current_player = self.player_colours[self.current_player_colour]
            adventurers = self.game.adventurers[current_player]
            for adventurer in adventurers:
                print("Starting the turn for " +current_player.colour+ " Adventurer #" +str(adventurers.index(adventurer) + 1))
                self.Send({"action":"prompt", "prompt_text":self.current_player_colour +" player is moving their Adventurer #" +str(adventurers.index(adventurer)+1)})
                if adventurer.turns_moved < self.game.turn:
                    current_player.continue_turn(adventurer)
                    print() #to help log readability
                    
                    #check whether this adventurer's turn has won them the game
                    if self.game.check_win_conditions():
                        self.game.game_over = True
                        break
            #Make sure visuals are up to date and all changes have been shared to the server
            self.draw_play_area()
            #for virtual players, share their route
            if current_player.colour in self.virtual_players:
                for adventurer in adventurers:
                    for tile in adventurer.route:
                        adventurers_routes = [{} for i in range(len(adventurers))] #this adventurer#s moves are shared by their position in a list
                        adventurers_routes[adventurers.index(adventurer)] = {"longitude":tile.tile_position.longitude, "latitude":tile.tile_position.latitude}
                        self.Send({"action":"move_tokens", "changes":{"adventurers":{current_player.colour:adventurers_routes}, "agents":{}}})
            self.draw_routes()
            self.draw_tokens()
            self.draw_scores()
            if self.game.game_over:
                self.Send({"action":"declare_win", "winning_player_colour":self.game.winning_player.colour})
                connection.Pump()
                self.Pump()
                self.Network_declare_win({"winning_player_colour":self.game.winning_player.colour})
            print("Passing play to the next player")
            if self.players.index(current_player) < len(self.players) - 1:
                current_player = self.players[self.players.index(current_player) + 1]
                self.current_player_colour = current_player.colour
            else:
                #If this was the last player in the play order then the turn increases by 1
                current_player = self.players[0]
                self.game.turn += 1
                self.current_player_colour = current_player.colour
            if self.current_player_colour not in self.local_player_colours:
                #Reset the route to be visualised for this non-local player
                for adventurer in self.game.adventurers[current_player]:
                    adventurer.route = [adventurer.current_tile]
                self.local_player_turn = False
            if self.current_player_colour in self.virtual_players:
                #Reset the route to be visualised for this virtual player
                for adventurer in self.game.adventurers[current_player]:
                    adventurer.route = [adventurer.current_tile]
            self.Send({"action":"new_turn", "turn":self.game.turn, "current_player_colour":self.current_player_colour})
    
    def handleMessage(self):
        '''Distinguish whether this message is an initiation or continuation of a game.
        ''' 
        #@TODO match the player to a game, set up a separate game visualisation for that client socket
        try:
           message = str(self.data) 
           protocode, msg = message.split("[00100]")
           if protocode == ("SUB"):
               print("SUB")
               self.socket.setsockopt(zmq.IDENTITY, str(msg))
               self.socket.connect("tcp://LOCALHOST:80")
               #Check whether there are enough players in the queue for a game,
               #start one in a Thread if so
               #@TODO join specifically the game that has been asked for
               Thread(target=self.join_game).start()
           elif protocode == ("MESSAGE"):
               print("MESSAGE")
               msg = str(msg)
               ident, mdata = msg.split("[11111]")
               msg = ('%sSPLIT%s' % (ident, mdata))
               self.socket.send(str(msg))
           else:
               raise Exception
        except Exception as e:
           print (e)

    def handleConnected(self):
        '''On initial connection, establish client details, allocate to game
        '''
        print(self.address, 'connected')
        clients.append(self)
        self.init_ZMQ()
#        channel.setup()


    def handleClose(self):
        '''Gracefully remove a client
        '''
       clients.pop(self)
       print (self.address, 'closed')
       for client in clients:
          client.sendMessage(self.address[0] + u' - disconnected')

server = SimpleWebSocketServer('', 10000, WebServer)
server.serveforever()