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
        
    def connect_visual(self):
        '''Create a visualisation (and a game if needed), share images of the pygame canvas and receive input coordinates.
        '''
        while True:
            try:
                data = self.socket.recv()
                code, self.width = data.split('[55555]')
                data = self.socket.recv()
                code, self.height = data.split('[55555]')
                self.width = int(self.width)
                self.height = int(self.height)
                self.width = float(self.width /1.5)
                self.height = float(self.height /1.5)
                print (self.width, self.height)
                data = self.socket.recv()   
                image = pygame.image.frombuffer(data
                                                , (int(self.width), int(self.height))
                                                ,"RGB")
                randname = id_generator()
                pygame.image.save(image, randname+".png")
                out = open(randname+".png","rb").read()
                self.sendMessage(base64.b64encode(out))
                print("data sent")
                os.remove(randname+".png")
            except Exception as e:
                print (e)
    
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
               self.socket.connect("tcp://127.0.0.1:9001")
               Thread(target=self.ondata).start()
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


    def handleClose(self):
        '''Gracefully remove a client
        '''
       clients.pop(self)
       print (self.address, 'closed')
       for client in clients:
          client.sendMessage(self.address[0] + u' - disconnected')

server = SimpleWebSocketServer('', 10000, WebServer)
server.serveforever()